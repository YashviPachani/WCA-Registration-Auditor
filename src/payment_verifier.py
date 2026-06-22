"""
payment_verifier.py
Downloads payment screenshots from Google Drive, reads the amount using
EasyOCR with image preprocessing (crop top 60% + upscale, free, local,
no API key needed), and compares against expected fee.

Caches both downloaded images and OCR results so re-running the audit
on an updated participant list only processes NEW people.
"""

import os
import re
import json
import cv2
import easyocr
from src.drive_reader import download_file, extract_file_id

SCREENSHOTS_DIR = "data/screenshots_cache"
RESULTS_CACHE_PATH = "data/payment_verification_cache.json"

reader = easyocr.Reader(["en"], gpu=False)


# ──────────────────────────────────────────────
# CACHE HELPERS
# ──────────────────────────────────────────────


def load_results_cache():
    if os.path.exists(RESULTS_CACHE_PATH):
        try:
            with open(RESULTS_CACHE_PATH, "r") as f:
                content = f.read().strip()
                if not content:
                    return {}
                return json.loads(content)
        except (json.JSONDecodeError, ValueError):
            return {}
    return {}


def save_results_cache(cache):
    os.makedirs(os.path.dirname(RESULTS_CACHE_PATH), exist_ok=True)
    with open(RESULTS_CACHE_PATH, "w") as f:
        json.dump(cache, f, indent=2)


# ──────────────────────────────────────────────
# IMAGE DOWNLOAD WITH CACHE
# ──────────────────────────────────────────────


def get_or_download_screenshot(drive_link):
    """Download screenshot only if not already cached locally."""
    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

    file_id = extract_file_id(drive_link)
    if not file_id:
        return None

    local_path = os.path.join(SCREENSHOTS_DIR, f"{file_id}.jpg")

    if os.path.exists(local_path):
        return local_path  # already downloaded

    try:
        download_file(drive_link, local_path)
        return local_path
    except Exception as e:
        print(f"Failed to download {drive_link}: {e}")
        return None


# ──────────────────────────────────────────────
# OCR READING (EasyOCR + preprocessing — Vatsal's approach)
# ──────────────────────────────────────────────


def preprocess(image_path):
    """
    Use the full image (no crop, since amount position varies across
    different payment app layouts), convert to grayscale, and upscale
    2x for clarity.
    """
    img = cv2.imread(image_path)

    if img is None:
        return None

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)

    return gray


def extract_text_with_positions(image_path):
    """
    Run EasyOCR on the full preprocessed image and return text fragments
    along with their vertical (y) position, so we can prioritize matches
    found higher up on screen (amount is rarely in the bottom 20%, where
    transaction IDs/bank details usually sit).
    """
    img = preprocess(image_path)
    if img is None:
        return []

    result = reader.readtext(img, detail=1)  # detail=1 gives bounding boxes
    img_height = img.shape[0]

    fragments = []
    for bbox, text, conf in result:
        # bbox is 4 corner points; average y-coordinate gives vertical position
        y_coords = [point[1] for point in bbox]
        avg_y = sum(y_coords) / len(y_coords)
        relative_y = avg_y / img_height  # 0 = top, 1 = bottom
        fragments.append((text, relative_y, conf))

    return fragments


def extract_text(image_path):
    """Run EasyOCR on the preprocessed (full, upscaled) image — kept for
    backward compatibility / simple text dump."""
    fragments = extract_text_with_positions(image_path)
    return " ".join(f[0] for f in fragments)


def extract_amount_from_text(text, expected_amount=None):
    """
    Extract the payment amount from plain OCR text (no position info).
    Since competition fees are fixed tiers (e.g. 600 or 800), this checks
    for those specific known amounts after fixing common OCR digit/letter
    confusions (e.g. 'o' misread for '0'). Falls back to a general numeric
    pattern if no known tier amount is found.
    """
    if not isinstance(text, str):
        return None

    text = text.lower()

    # Fix common OCR confusions for o/0 within number-like sequences
    text = re.sub(r"(\d)o(\d)", r"\g<1>0\g<2>", text)
    text = text.replace("8oo", "800")
    text = text.replace("80o", "800")
    text = text.replace("o80", "080")
    text = text.replace("6oo", "600")
    text = text.replace("60o", "600")
    text = text.replace("o60", "060")

    known_amounts = [600, 800]
    if expected_amount in known_amounts:
        known_amounts.remove(expected_amount)
        known_amounts.insert(0, expected_amount)

    for amount in known_amounts:
        patterns = [
            rf"\b{amount}\.00\b",
            rf"\b{amount}\b",
            rf"r\s*{amount}\b",
            rf"rs\.?\s*{amount}\b",
        ]
        for pattern in patterns:
            if re.search(pattern, text):
                return float(amount)

    patterns = [
        r"[\u20b97]\s*([0-9]{2,6}(?:\.[0-9]{1,2})?)",
        r"r\s*([0-9]{2,6}(?:\.[0-9]{1,2})?)",
        r"rs\.?\s*([0-9]{2,6}(?:\.[0-9]{1,2})?)",
        r"inr\s*([0-9]{2,6}(?:\.[0-9]{1,2})?)",
        r"\b([0-9]{2,6}\.[0-9]{2})\b",
    ]
    for pattern in patterns:
        matches = re.findall(pattern, text)
        if matches:
            amounts = [float(m) for m in matches if 10 <= float(m) <= 50000]
            if amounts:
                return max(set(amounts), key=amounts.count)

    return None


def strip_date_time_patterns(text):
    """
    Remove date/time-like patterns (e.g. '11 Feb 2026, 10:27 PM' or
    '10.27 PM') before generic numeric fallback runs — otherwise a
    misread time like '10.27' can be mistaken for a payment amount.
    """
    # Remove "<digits> <Month> <year>, <time>" style dates
    text = re.sub(
        r"\d{1,2}\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\s+\d{4}[,.\s]*\d{1,2}[:.]\d{2}\s*(am|pm)?",
        " ",
        text,
        flags=re.IGNORECASE,
    )
    # Remove standalone time-like fragments "10.27 pm" / "10:27 PM"
    text = re.sub(r"\b\d{1,2}[:.]\d{2}\s*(am|pm)\b", " ", text, flags=re.IGNORECASE)
    return text


def extract_amount_from_fragments(fragments, expected_amount=None):
    """
    Extract the amount using position-weighted fragments. Prioritizes
    known fee tiers (600/800) found in the TOP 50% of the image (amount
    is rarely below this point, where transaction IDs/timestamps/bank
    details sit), falling back to looser matching only if nothing is
    found there.
    """
    if not fragments:
        return None

    known_amounts = [600, 800]
    if expected_amount in known_amounts:
        known_amounts.remove(expected_amount)
        known_amounts.insert(0, expected_amount)

    def clean(text):
        text = text.lower()
        text = re.sub(r"(\d)o(\d)", r"\g<1>0\g<2>", text)
        text = text.replace("8oo", "800").replace("80o", "800")
        text = text.replace("6oo", "600").replace("60o", "600")
        return text

    def standalone_match(cleaned_text, amount):
        """
        Require the amount to be a STANDALONE number — not preceded or
        followed by another digit. This avoids matching '800' inside
        '98005...' (a transaction ID fragment) while still allowing
        '₹800', 'r800', '800.00' etc.
        """
        pattern = rf"(?<!\d){amount}(?:\.00)?(?!\d)"
        if re.search(pattern, cleaned_text):
            return True

        # Also check for the ₹ symbol commonly misread as a leading
        # stray digit directly fused with the amount (e.g. '₹600' ->
        # '2600', '₹800' -> '7800' or '8800'). Only strip a SINGLE
        # leading stray digit if doing so produces an exact, standalone
        # known amount — this avoids accidentally truncating genuine
        # larger numbers.
        for prefix in ("2", "7", "8", "9"):
            fused = f"{prefix}{amount}"
            fused_pattern = rf"(?<!\d){fused}(?:\.00)?(?!\d)"
            if re.search(fused_pattern, cleaned_text):
                return True

        return False

    # Pass 1 — known tiers, only in top 50% of image, as standalone numbers
    for text, rel_y, conf in fragments:
        if rel_y > 0.50:
            continue
        cleaned = clean(text)
        for amount in known_amounts:
            if standalone_match(cleaned, amount):
                return float(amount)

    # Pass 2 — known tiers in top 70%, still standalone (slightly wider net)
    for text, rel_y, conf in fragments:
        if rel_y > 0.70:
            continue
        cleaned = clean(text)
        for amount in known_amounts:
            if standalone_match(cleaned, amount):
                return float(amount)

    # Pass 3 — known tiers anywhere, standalone only (avoids txn ID grabs)
    full_text = " ".join(clean(f[0]) for f in fragments)
    for amount in known_amounts:
        if standalone_match(full_text, amount):
            return float(amount)

    # Pass 4 — last resort generic numeric fallback on full text,
    # with date/time patterns stripped out first to avoid misreading
    # a time like '10.27 PM' as a payment amount
    full_text_no_dates = strip_date_time_patterns(full_text)
    return extract_amount_from_text(full_text_no_dates, expected_amount)


def read_amount_from_screenshot(image_path, expected_amount=None):
    """
    Runs preprocessing + EasyOCR on the screenshot and extracts the amount,
    using vertical position of text to prioritize matches near the top
    (where the amount almost always appears) over the bottom (transaction
    IDs, bank details, timestamps).
    Returns a dict: {"amount": float or None, "confidence": "high"/"low", "notes": str}
    """
    try:
        fragments = extract_text_with_positions(image_path)
    except Exception as e:
        return {"amount": None, "confidence": "low", "notes": f"OCR failed: {e}"}

    amount = extract_amount_from_fragments(fragments, expected_amount=expected_amount)

    if amount is None:
        return {
            "amount": None,
            "confidence": "low",
            "notes": "Could not detect amount in screenshot",
        }

    return {"amount": amount, "confidence": "high", "notes": ""}


# ──────────────────────────────────────────────
# MAIN VERIFICATION FUNCTION (with caching)
# ──────────────────────────────────────────────


def verify_payment_screenshot(person_key, drive_links, expected_amount):
    """
    person_key: unique identifier (wca_id or name) used as cache key
    drive_links: list of Google Drive share links (handles split payments)
    expected_amount: amount calculated by fee_calculator

    Returns a dict with verification result. Sums amounts across all screenshots.
    """
    cache = load_results_cache()

    # Already verified before? Return cached result instantly.
    if person_key in cache:
        cached = dict(cache[person_key])
        cached["from_cache"] = True
        return cached

    if not drive_links:
        result = {
            "amount_detected": None,
            "confidence": "low",
            "notes": "No screenshot provided",
            "status": "MANUAL REVIEW",
        }
        cache[person_key] = result
        save_results_cache(cache)
        return {**result, "from_cache": False}

    total_detected = 0
    all_notes = []
    lowest_confidence = "high"
    any_amount_found = False

    for link in drive_links:
        local_path = get_or_download_screenshot(link)

        if not local_path:
            all_notes.append("Could not download one screenshot")
            lowest_confidence = "low"
            continue

        ocr_result = read_amount_from_screenshot(
            local_path, expected_amount=expected_amount
        )
        amount = ocr_result.get("amount")
        confidence = ocr_result.get("confidence", "low")
        notes = ocr_result.get("notes", "")

        if amount is None:
            lowest_confidence = "low"
            all_notes.append(notes or "Could not read amount from one screenshot")
        else:
            total_detected += amount
            any_amount_found = True
            if confidence == "low":
                lowest_confidence = "low"
            if notes:
                all_notes.append(notes)

    if not any_amount_found:
        status = "MANUAL REVIEW"
        amount_detected = None
    else:
        amount_detected = total_detected

        # Sanity check — if detected amount is wildly higher than expected
        # (more than 3x), it's more likely a misread digit than a genuine
        # overpayment
        if amount_detected > expected_amount * 3:
            lowest_confidence = "low"
            all_notes.append(
                f"Detected amount ({amount_detected}) implausibly high vs "
                f"expected ({expected_amount}) — likely misread"
            )

        if lowest_confidence == "low":
            status = "MANUAL REVIEW"
        elif amount_detected == expected_amount:
            status = "VERIFIED"
        elif amount_detected < expected_amount:
            status = f"UNDERPAID by Rs.{expected_amount - amount_detected}"
        else:
            status = f"OVERPAID by Rs.{amount_detected - expected_amount}"

    result = {
        "amount_detected": amount_detected,
        "confidence": lowest_confidence,
        "notes": "; ".join(all_notes) if all_notes else "",
        "status": status,
    }

    cache[person_key] = result
    save_results_cache(cache)

    return {**result, "from_cache": False}


# ──────────────────────────────────────────────
# BATCH PROCESSING (for use in dashboard with progress bar)
# ──────────────────────────────────────────────


def verify_all_screenshots(
    matched_df, screenshot_links_column="screenshot_links", progress_callback=None
):
    """
    matched_df must have: wca_id, name, expected_amount, screenshot_links_column (list of links)
    progress_callback: optional function(current, total) for UI progress bars
    """
    results = []
    total = len(matched_df)

    for i, row in enumerate(matched_df.itertuples()):
        person_key = str(getattr(row, "wca_id", None) or getattr(row, "name"))
        drive_links = getattr(row, screenshot_links_column, None) or []
        expected = getattr(row, "expected_amount", 0)

        result = verify_payment_screenshot(person_key, drive_links, expected)

        results.append({
            "name": getattr(row, "name"),
            "wca_id": getattr(row, "wca_id", None),
            "expected_amount": expected,
            **result,
        })

        if progress_callback:
            progress_callback(i + 1, total)

    return results

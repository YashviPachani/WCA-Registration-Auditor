import pandas as pd


def calculate_expected_fee(num_events):

    if num_events <= 3:
        return 600

    return 800


def verify_payments(matched_df, ocr_df):

    results = []

    ocr_lookup = {}

    for _, row in ocr_df.iterrows():
        filename = row["file"]

        ocr_lookup[filename] = row["amount"]

    for _, row in matched_df.iterrows():
        if row["missing_in_wca"] or row["missing_in_form"]:
            continue

        expected = calculate_expected_fee(len(row["events_form"]))

        screenshot_file = row["screenshot_file"]

        detected = ocr_lookup.get(screenshot_file)

        if detected is None:
            status = "OCR FAILED"

        elif detected == expected:
            status = "VERIFIED"

        elif detected < expected:
            status = "UNDERPAID"

        else:
            status = "OVERPAID"

        results.append({
            "name": row["name"],
            "expected": expected,
            "detected": detected,
            "status": status,
        })

    return pd.DataFrame(results)

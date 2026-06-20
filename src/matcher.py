import pandas as pd
import re
from rapidfuzz import fuzz


def normalize_wca_id(value):
    if pd.isna(value):
        return None

    value = str(value).strip().upper()

    if value == "NAN":  # ← add this check
        return None

    pattern = r"^\d{4}[A-Z]{4}\d{2}$"
    if re.match(pattern, value):
        return value

    return None


def normalize_name(name):
    if pd.isna(name):
        return ""
    name = str(name).lower().strip().replace(".", "")
    # Remove single-character middle tokens (initials)
    tokens = [t for t in name.split() if len(t) > 1]
    return " ".join(tokens)


def find_best_name_match(name, candidates, threshold=75):

    best_score = 0
    best_idx = None

    for idx, candidate in candidates.items():
        score = fuzz.token_sort_ratio(
            normalize_name(name),
            normalize_name(candidate),
        )

        if score > best_score:
            best_score = score
            best_idx = idx

    if best_score >= threshold:
        return best_idx

    return None


def match_competitors(wca_df, form_df):

    wca_df = wca_df.copy()
    form_df = form_df.copy()

    wca_df["wca_id"] = wca_df["wca_id"].apply(normalize_wca_id)
    form_df["wca_id"] = form_df["wca_id"].apply(normalize_wca_id)

    matched_rows = []

    used_wca = set()
    used_form = set()

    # --------------------------------------------------
    # STEP 1: MATCH BY VALID WCA ID
    # --------------------------------------------------

    form_lookup = {}

    for idx, row in form_df.iterrows():
        wca_id = row["wca_id"]
        if wca_id is not None and pd.notna(wca_id):
            form_lookup[wca_id] = idx

    for wca_idx, wca_row in wca_df.iterrows():
        wca_id = wca_row["wca_id"]

        if wca_id is not None and pd.notna(wca_id) and wca_id in form_lookup:
            form_idx = form_lookup[wca_id]
            form_row = form_df.loc[form_idx]

            matched_rows.append(
                build_match_row(
                    wca_row,
                    form_row,
                    False,
                    False,
                )
            )

            used_wca.add(wca_idx)
            used_form.add(form_idx)

    # --------------------------------------------------
    # STEP 1.5: MATCH REMAINING BY EMAIL
    # --------------------------------------------------

    remaining_form = form_df.drop(index=list(used_form))
    remaining_wca = wca_df.drop(index=list(used_wca))

    # Build email lookup from remaining WCA rows
    wca_email_lookup = {}
    for idx, row in remaining_wca.iterrows():
        if pd.notna(row.get("email_wca")):
            wca_email_lookup[row["email_wca"].strip().lower()] = idx

    for form_idx, form_row in remaining_form.iterrows():
        form_email = str(form_row.get("email", "")).strip().lower()
        if form_email and form_email in wca_email_lookup:
            wca_idx = wca_email_lookup[form_email]

            matched_rows.append(
                build_match_row(wca_df.loc[wca_idx], form_row, False, False)
            )
            used_wca.add(wca_idx)
            used_form.add(form_idx)

    # --------------------------------------------------
    # STEP 2: MATCH REMAINING BY NAME
    # --------------------------------------------------

    remaining_form = form_df.drop(index=list(used_form))

    for wca_idx, wca_row in wca_df.iterrows():
        if wca_idx in used_wca:
            continue

        match_idx = find_best_name_match(
            wca_row["name"],
            remaining_form["name"],
        )

        if match_idx is not None:
            form_row = remaining_form.loc[match_idx]

            matched_rows.append(
                build_match_row(
                    wca_row,
                    form_row,
                    False,
                    False,
                )
            )

            used_wca.add(wca_idx)
            used_form.add(match_idx)

            remaining_form = remaining_form.drop(match_idx)

    # --------------------------------------------------
    # STEP 3: MISSING IN FORM
    # --------------------------------------------------

    for wca_idx, wca_row in wca_df.iterrows():
        if wca_idx in used_wca:
            continue

        matched_rows.append(
            build_match_row(
                wca_row,
                None,
                False,
                True,
            )
        )

    # --------------------------------------------------
    # STEP 4: MISSING IN WCA
    # --------------------------------------------------

    for form_idx, form_row in form_df.iterrows():
        if form_idx in used_form:
            continue

        matched_rows.append(
            build_match_row(
                None,
                form_row,
                True,
                False,
            )
        )

    return pd.DataFrame(matched_rows)


def build_match_row(
    wca_row,
    form_row,
    missing_in_wca,
    missing_in_form,
):

    return {
        "wca_id": wca_row["wca_id"] if wca_row is not None else form_row["wca_id"],
        "name": wca_row["name"] if wca_row is not None else form_row["name"],
        "email": form_row["email"] if form_row is not None else None,
        "events_wca": wca_row["events_wca"] if wca_row is not None else None,
        "events_form": form_row["events_form"] if form_row is not None else None,
        "amount_paid": form_row["amount_paid"] if form_row is not None else None,
        "participant_filename": form_row["participant_filename"]
        if form_row is not None
        else None,
        "missing_in_wca": missing_in_wca,
        "missing_in_form": missing_in_form,
    }

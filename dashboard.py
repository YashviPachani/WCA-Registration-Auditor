import streamlit as st
import pandas as pd
import tempfile
import os

from src.data_loader import load_file, prepare_wca_dataframe, prepare_form_dataframe

from src.matcher import match_competitors
from src.validator import (
    find_missing_in_wca,
    find_missing_in_form,
    find_event_mismatches,
    # find_duplicates,
)
from src.fee_calculator import verify_payment

from src.payment_verifier import verify_payments

st.set_page_config(page_title="WCA Registration Auditor", page_icon="🎲", layout="wide")

st.title("🎲 WCA Registration Auditor")

wca_file = st.file_uploader("Upload WCA Export", type=["csv", "xlsx"])

form_file = st.file_uploader("Upload Google Form Export", type=["csv", "xlsx"])


def calculate_expected_fee(num_events):

    if num_events <= 3:
        return 600

    return 800


if wca_file and form_file:
    wca_raw = load_file(wca_file)
    form_raw = load_file(form_file)

    print("WCA Columns:")
    print(wca_raw.columns.tolist())

    print("Form Columns:")
    print(form_raw.columns.tolist())

    print("Sample Form Event Value:")
    print(form_raw["Events you wish to participate in:"].iloc[0])
    wca_df = prepare_wca_dataframe(wca_raw)
    form_df = prepare_form_dataframe(form_raw)

    print("FORM EVENTS:")
    print(form_df["events_form"].head(10).tolist())
    print(form_raw["Events you wish to participate in:"].head(10).tolist())

    print("\nWCA EVENTS:")
    print(wca_df["events_wca"].head(10).tolist())

    matched_df = match_competitors(wca_df, form_df)
    OCR_RESULTS = "data/processed/ocr_results.csv"

    if os.path.exists(OCR_RESULTS):
        ocr_df = pd.read_csv(OCR_RESULTS)
    else:
        st.error("ocr_results.csv not found. Run OCR first.")
        st.stop()
    payment_rows = []

    ocr_lookup = {}

    for _, row in ocr_df.iterrows():
        ocr_lookup[row["file"]] = row["amount"]

    ocr_files = list(ocr_lookup.keys())
    print("\nFIRST 10 OCR FILES:")
    print(list(ocr_lookup.keys())[:10])

    for _, row in matched_df.iterrows():
        if row["missing_in_wca"] or row["missing_in_form"]:
            continue

        expected = calculate_expected_fee(len(row["events_form"]))

        participant = row["participant_filename"]

        filename = None

        for f in ocr_files:
            if participant in f:
                filename = f
                break
        if filename is None:
            print("NO OCR FILE:", participant)

        detected = ocr_lookup.get(filename)

        if detected is None:
            print("NOT FOUND:", filename)

        if pd.isna(detected):
            status = "OCR FAILED"

        elif detected == expected:
            status = "VERIFIED"

        elif detected < expected:
            status = "UNDERPAID"

        else:
            status = "OVERPAID"

        payment_rows.append({
            "name": row["name"],
            "expected": expected,
            "detected": detected,
            "status": status,
            "file": filename,
        })

    payment_results = pd.DataFrame(payment_rows)
    failed_ocr_files = set(ocr_df[ocr_df["amount"].isna()]["file"])

    payment_failed_files = set(
        payment_results[payment_results["status"] == "OCR FAILED"]["file"]
    )

    print("\nOCR FAILURES NOT IN DASHBOARD:")
    print(failed_ocr_files - payment_failed_files)

    print("\nCount:", len(failed_ocr_files - payment_failed_files))
    print("\nPAYMENT RESULT FILES:")
    print(payment_results[["name", "file"]].head(10))
    missing_wca = find_missing_in_wca(matched_df)
    missing_form = find_missing_in_form(matched_df)
    event_mismatches = find_event_mismatches(matched_df)
    print(event_mismatches[event_mismatches["wca_id"].isna()].head(20))
    # duplicates = find_duplicates(form_df)
    st.header("Summary")

    c1, c2, c3, c4, c5 = st.columns(5)

    c1.metric("Competitors", len(matched_df))
    c2.metric("Missing in WCA", len(missing_wca))
    c3.metric("Missing in Form", len(missing_form))
    c4.metric("Event Mismatches", len(event_mismatches))
    # duplicate_count = len(duplicates["email"]) + len(duplicates["wca_id"])
    # c5.metric("Duplicates", duplicate_count)

    tab1, tab2, tab3, tab4 = st.tabs([
        "Matched Data",
        "Missing Registrations",
        "Event Mismatches",
        "Payment Verification",
    ])

    with tab1:
        st.dataframe(matched_df)

    with tab2:
        st.subheader("Missing in WCA")
        st.dataframe(missing_wca)

        st.subheader("Missing in Form")
        st.dataframe(missing_form)

    with tab3:
        st.dataframe(event_mismatches)

    with tab4:
        st.subheader("Payment Verification")

        verified = len(payment_results[payment_results["status"] == "VERIFIED"])

        failed = len(payment_results[payment_results["status"] == "OCR FAILED"])

        underpaid = len(payment_results[payment_results["status"] == "UNDERPAID"])

        overpaid = len(payment_results[payment_results["status"] == "OVERPAID"])

        c1, c2, c3, c4 = st.columns(4)

        c1.metric("Verified", verified)

        c2.metric("OCR Failed", failed)

        c3.metric("Underpaid", underpaid)

        c4.metric("Overpaid", overpaid)

        st.divider()

        st.dataframe(payment_results, use_container_width=True)

        st.subheader("Manual Review Required")

        failed_df = payment_results[payment_results["status"] == "OCR FAILED"]

        st.dataframe(failed_df, use_container_width=True)

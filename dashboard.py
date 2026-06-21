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
from src.payment_verifier import verify_all_screenshots
from src.fee_calculator import calculate_expected_fee

st.set_page_config(page_title="WCA Registration Auditor", page_icon="🎲", layout="wide")

st.title("🎲 WCA Registration Auditor")

wca_file = st.file_uploader("Upload WCA Export", type=["csv", "xlsx"])

form_file = st.file_uploader("Upload Google Form Export", type=["csv", "xlsx"])

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
    print(matched_df[["name", "screenshot_links"]].head()) 
    missing_wca = find_missing_in_wca(matched_df)
    missing_form = find_missing_in_form(matched_df)
    event_mismatches = find_event_mismatches(matched_df)
    # duplicates = find_duplicates(form_df)
    st.header("Summary")

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Competitors", len(matched_df))
    c2.metric("Missing in WCA", len(missing_wca))
    c3.metric("Missing in Form", len(missing_form))
    c4.metric("Event Mismatches", len(event_mismatches))

    # duplicate_count = len(duplicates["email"]) + len(duplicates["wca_id"])
    # c5.metric("Duplicates", duplicate_count)

    tab1, tab2, tab3 = st.tabs([
        "Matched Data",
        "Missing Registrations",
        "Event Mismatches",
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

    st.header("💰 AI Payment Verification")
    st.caption("This checks payment screenshots using AI. Already-verified people are skipped automatically (cached).")

    if st.button("🔍 Verify Payment Screenshots"):
        verify_df = matched_df[~matched_df["missing_in_wca"] & ~matched_df["missing_in_form"]].copy()
        verify_df["expected_amount"] = verify_df["events_form"].apply(
            lambda events: calculate_expected_fee(len(events)) if isinstance(events, list) else 0
        )

        progress_bar = st.progress(0)
        status_text = st.empty()

        def update_progress(current, total):
            progress_bar.progress(current / total)
            status_text.text(f"Processing {current}/{total}...")

        results = verify_all_screenshots(verify_df, progress_callback=update_progress)

        status_text.text("Done!")
        results_df = pd.DataFrame(results)
        st.dataframe(results_df)
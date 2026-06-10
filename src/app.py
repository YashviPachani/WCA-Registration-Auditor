import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from data_loader    import load_file, prepare_wca_dataframe, prepare_form_dataframe
from matcher        import match_by_wca_id
from validator      import find_missing_in_wca, find_missing_in_form, find_event_mismatches, find_duplicates
from fee_calculator import verify_payment
from reports        import generate_report


def run_audit(wca_path, form_path, report_path='data/processed/report.xlsx'):

    # ── 1. Load raw files ──────────────────────────────────────
    print("Loading files...")
    wca_raw  = load_file(wca_path)
    form_raw = load_file(form_path)

    # ── 2. Clean into standard DataFrames ─────────────────────
    print("Preparing data...")
    wca_df  = prepare_wca_dataframe(wca_raw)
    form_df = prepare_form_dataframe(form_raw)

    # ── 3. Match competitors ───────────────────────────────────
    print("Matching competitors...")
    matched_df = match_by_wca_id(wca_df, form_df)

    # ── 4. Run all checks ──────────────────────────────────────
    print("Running audit checks...")
    missing_wca      = find_missing_in_wca(matched_df)
    missing_form     = find_missing_in_form(matched_df)
    event_mismatches = find_event_mismatches(matched_df)
    duplicates       = find_duplicates(form_df)
    payment_df       = verify_payment(matched_df)

    # ── 5. Generate Excel report ───────────────────────────────
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    generate_report(
        missing_wca=missing_wca,
        missing_form=missing_form,
        event_mismatches=event_mismatches,
        duplicates=duplicates,
        payment_df=payment_df,
        output_path=report_path,
    )

    # ── 6. Print summary ───────────────────────────────────────
    verified  = len(payment_df[payment_df['status'] == 'VERIFIED'])
    underpaid = len(payment_df[payment_df['status'].str.contains('UNDERPAID', na=False)])
    overpaid  = len(payment_df[payment_df['status'].str.contains('OVERPAID',  na=False)])

    print(f"\n{'═'*42}")
    print(f"   WCA REGISTRATION AUDIT REPORT")
    print(f"{'═'*42}")
    print(f"  Total competitors:   {len(matched_df)}")
    print(f"  Missing in WCA:      {len(missing_wca)}")
    print(f"  Missing in Form:     {len(missing_form)}")
    print(f"  Event mismatches:    {len(event_mismatches)}")
    print(f"  Duplicate emails:    {len(duplicates['email'])}")
    print(f"  Duplicate WCA IDs:   {len(duplicates['wca_id'])}")
    print(f"\n  Payment Summary:")
    print(f"    ✅ Verified:        {verified}")
    print(f"    ❌ Underpaid:       {underpaid}")
    print(f"    ⚠️  Overpaid:        {overpaid}")
    print(f"\n  Report saved → {report_path}")
    print(f"{'═'*42}\n")

    if len(event_mismatches) > 0:
        print("Event Mismatches Detail:")
        print(event_mismatches.to_string(index=False))
        print()

    if len(missing_wca) > 0:
        print("Missing in WCA:")
        print(missing_wca.to_string(index=False))
        print()

    if len(missing_form) > 0:
        print("Missing in Form:")
        print(missing_form.to_string(index=False))
        print()

    print("Payment Status:")
    print(payment_df[['name', 'events', 'expected', 'paid', 'status']].to_string(index=False))


if __name__ == "__main__":
    # Paths relative to project root
    base = os.path.dirname(os.path.dirname(__file__))
    run_audit(
        wca_path    = os.path.join(base, 'data/raw/wca_sample.csv'),
        form_path   = os.path.join(base, 'data/raw/form_sample.csv'),
        report_path = os.path.join(base, 'data/processed/report.xlsx'),
    )
import pandas as pd
 
BASE_FEE      = 300
PER_EVENT_FEE = 50
FREE_EVENTS   = 1   # first event included in base fee
 
 
def calculate_expected_fee(num_events: int) -> int:
    extra = max(0, num_events - FREE_EVENTS)
    return BASE_FEE + extra * PER_EVENT_FEE
 
 
def verify_payment(matched_df):
    """Only check payment for people who are present in both WCA and form."""
    both = matched_df[~matched_df['missing_in_wca'] & ~matched_df['missing_in_form']].copy()
    results = []
 
    for _, row in both.iterrows():
        num_events = len(row['events_form']) if isinstance(row['events_form'], list) else 0
        expected   = calculate_expected_fee(num_events)
        paid       = row.get('amount_paid', None)
 
        if pd.isna(paid):
            status = 'UNKNOWN'
        else:
            diff = int(paid) - expected
            if diff == 0:
                status = 'VERIFIED'
            elif diff < 0:
                status = f'UNDERPAID by ₹{abs(diff)}'
            else:
                status = f'OVERPAID by ₹{diff}'
 
        results.append({
            'name':     row['name'],
            'wca_id':   row['wca_id'],
            'events':   num_events,
            'expected': expected,
            'paid':     paid,
            'status':   status,
        })
 
    return pd.DataFrame(results)
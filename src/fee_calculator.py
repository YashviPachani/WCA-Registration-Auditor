import pandas as pd
# fee_calculator.py

BASE_FEE = 300       # change to your competition's actual fee
PER_EVENT_FEE = 50   # change accordingly
FREE_EVENTS = 1      # first event included in base fee (adjust if needed)

def calculate_expected_fee(num_events: int) -> int:
    extra = max(0, num_events - FREE_EVENTS)
    return BASE_FEE + extra * PER_EVENT_FEE

def verify_payment(form_df):
    """
    Expects form_df to have:
    - 'events_form': list of events
    - 'amount_paid': amount from payment screenshot / manual entry
    """
    results = []
    for _, row in form_df.iterrows():
        num_events = len(row['events_form'])
        expected = calculate_expected_fee(num_events)
        paid = row.get('amount_paid', None)
        
        status = 'UNKNOWN'
        diff = None
        if paid is not None:
            diff = paid - expected
            if diff == 0:
                status = 'VERIFIED'
            elif diff < 0:
                status = f'UNDERPAID by ₹{abs(diff)}'
            else:
                status = f'OVERPAID by ₹{diff}'
        
        results.append({
            'name': row['name'],
            'wca_id': row['wca_id'],
            'events': num_events,
            'expected': expected,
            'paid': paid,
            'status': status
        })
    
    return pd.DataFrame(results)
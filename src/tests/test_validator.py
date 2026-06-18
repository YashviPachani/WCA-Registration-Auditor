# test_validator.py
import pandas as pd
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from validator import find_missing_in_wca, find_missing_in_form, find_event_mismatches, find_duplicates
from fee_calculator import calculate_expected_fee, verify_payment
from reports import generate_report

# ─────────────────────────────────────────────
# DUMMY DATA
# ─────────────────────────────────────────────

# WCA registered competitors
wca_df = pd.DataFrame([
    {'wca_id': '2019MORI01', 'name': 'Vatsal Mori',   'events_wca': ['3x3', '2x2', 'Pyraminx']},
    {'wca_id': '2021SHAH02', 'name': 'Yashvi Shah',   'events_wca': ['3x3', 'OH', 'Clock']},
    {'wca_id': '2020PATE03', 'name': 'Raj Patel',     'events_wca': ['3x3', '4x4']},
    {'wca_id': '2022KUMA04', 'name': 'Priya Kumar',   'events_wca': ['3x3']},
    # Registered on WCA but never filled the form ↓
    {'wca_id': '2023GHOS05', 'name': 'Anik Ghosh',    'events_wca': ['3x3', '2x2']},
])

# Google Form responses
form_df = pd.DataFrame([
    # Normal - matches WCA exactly
    {'wca_id': '2019MORI01', 'name': 'Vatsal Mori',  'email': 'vatsal@gmail.com',
     'events_form': ['3x3', '2x2', 'Pyraminx'], 'amount_paid': 400},   # 300 + 2*50 = 400 ✓

    # Event mismatch - Clock missing in form vs WCA
    {'wca_id': '2021SHAH02', 'name': 'Yashvi Shah',  'email': 'yashvi@gmail.com',
     'events_form': ['3x3', 'OH'], 'amount_paid': 400},                 # paid for 3 events but only listed 2

    # Underpayment - registered 2 events, only paid for 1
    {'wca_id': '2020PATE03', 'name': 'Raj Patel',    'email': 'raj@gmail.com',
     'events_form': ['3x3', '4x4'], 'amount_paid': 300},                # expected 350, paid 300

    # Overpayment
    {'wca_id': '2022KUMA04', 'name': 'Priya Kumar',  'email': 'priya@gmail.com',
     'events_form': ['3x3'], 'amount_paid': 500},                       # expected 300, paid 500

    # Filled form but NOT on WCA
    {'wca_id': '2024DESAI6', 'name': 'Arjun Desai',  'email': 'arjun@gmail.com',
     'events_form': ['3x3', '2x2'], 'amount_paid': 350},

    # Duplicate email (same person submitted twice)
    {'wca_id': '2019MORI01', 'name': 'Vatsal Mori',  'email': 'vatsal@gmail.com',
     'events_form': ['3x3'], 'amount_paid': 300},
])

# ─────────────────────────────────────────────
# TESTS
# ─────────────────────────────────────────────

PASS = '✅ PASS'
FAIL = '❌ FAIL'

def section(title):
    print(f'\n{"─"*50}')
    print(f'  {title}')
    print(f'{"─"*50}')

# ── Test 1: Missing in WCA ──
section('TEST 1: Missing in WCA (filled form but not registered)')
missing_wca = find_missing_in_wca(wca_df, form_df)
print(missing_wca.to_string(index=False) if not missing_wca.empty else '  (none)')
expected_ids = {'2024DESAI6'}
found_ids = set(missing_wca['wca_id'].values)
# Note: duplicate entry of 2019MORI01 is already in WCA, so only DESAI6 should appear
result = expected_ids == found_ids
print(f'\nResult: {PASS if result else FAIL}')
print(f'  Expected: {expected_ids}')
print(f'  Got:      {found_ids}')

# ── Test 2: Missing in Form ──
section('TEST 2: Missing in Form (registered on WCA but no form)')
missing_form = find_missing_in_form(wca_df, form_df)
print(missing_form.to_string(index=False) if not missing_form.empty else '  (none)')
expected_ids = {'2023GHOS05'}
found_ids = set(missing_form['wca_id'].values)
result = expected_ids == found_ids
print(f'\nResult: {PASS if result else FAIL}')
print(f'  Expected: {expected_ids}')
print(f'  Got:      {found_ids}')

# ── Test 3: Event Mismatches ──
section('TEST 3: Event Mismatches')
mismatches = find_event_mismatches(wca_df, form_df)
print(mismatches.to_string(index=False) if not mismatches.empty else '  (none)')
# Yashvi has Clock on WCA but not in form
yashvi_mismatch = mismatches[mismatches['wca_id'] == '2021SHAH02']
result = not yashvi_mismatch.empty and 'Clock' in str(yashvi_mismatch['in_wca_not_form'].values)
print(f'\nResult: {PASS if result else FAIL}')
print(f'  Expected: Clock flagged for Yashvi Shah')

# ── Test 4: Duplicate Detection ──
section('TEST 4: Duplicate Detection')
dupes = find_duplicates(form_df)
print('Duplicate emails:')
print(dupes['email'][['name','email','wca_id']].to_string(index=False) if not dupes['email'].empty else '  (none)')
print('\nDuplicate WCA IDs:')
print(dupes['wca_id'][['name','email','wca_id']].to_string(index=False) if not dupes['wca_id'].empty else '  (none)')
result = len(dupes['email']) == 2 and len(dupes['wca_id']) == 2
print(f'\nResult: {PASS if result else FAIL}')
print(f'  Expected: 2 rows each for email and wca_id duplicates')

# ── Test 5: Fee Calculator ──
section('TEST 5: Fee Calculator')
cases = [
    (1, 300),   # base only
    (2, 350),   # base + 1 extra
    (3, 400),   # base + 2 extra
    (5, 500),   # base + 4 extra
]
all_pass = True
for events, expected in cases:
    got = calculate_expected_fee(events)
    ok = got == expected
    all_pass = all_pass and ok
    print(f'  {events} events → expected ₹{expected}, got ₹{got}  {PASS if ok else FAIL}')
print(f'\nResult: {PASS if all_pass else FAIL}')

# ── Test 6: Payment Verification ──
section('TEST 6: Payment Verification')
# Use a clean slice (no duplicates) for payment check
clean_form = form_df.drop_duplicates(subset='wca_id', keep='first').reset_index(drop=True)
payment_report = verify_payment(clean_form)
print(payment_report[['name', 'events', 'expected', 'paid', 'status']].to_string(index=False))

# Check specific cases
vatsal_status  = payment_report[payment_report['wca_id'] == '2019MORI01']['status'].values[0]
raj_status     = payment_report[payment_report['wca_id'] == '2020PATE03']['status'].values[0]
priya_status   = payment_report[payment_report['wca_id'] == '2022KUMA04']['status'].values[0]

r1 = vatsal_status == 'VERIFIED'
r2 = 'UNDERPAID' in raj_status
r3 = 'OVERPAID'  in priya_status
print(f'\n  Vatsal verified:  {PASS if r1 else FAIL}  ({vatsal_status})')
print(f'  Raj underpaid:    {PASS if r2 else FAIL}  ({raj_status})')
print(f'  Priya overpaid:   {PASS if r3 else FAIL}  ({priya_status})')

# ── Test 7: Full Report Generation ──
section('TEST 7: Excel Report Generation')
try:
    generate_report(
        missing_wca=missing_wca,
        missing_form=missing_form,
        event_mismatches=mismatches,
        duplicates=dupes,
        payment_df=payment_report,
        output_path='/home/claude/wca_test/report.xlsx'
    )
    print(f'  {PASS} report.xlsx generated successfully')
except Exception as e:
    print(f'  {FAIL} {e}')

# ── Summary ──
section('SUMMARY')
print(f'  Missing in WCA:    {len(missing_wca)} person(s)')
print(f'  Missing in Form:   {len(missing_form)} person(s)')
print(f'  Event mismatches:  {len(mismatches)} person(s)')
print(f'  Duplicate emails:  {len(dupes["email"])} row(s)')
print(f'  Duplicate WCA IDs: {len(dupes["wca_id"])} row(s)')
verified  = len(payment_report[payment_report['status'] == 'VERIFIED'])
underpaid = len(payment_report[payment_report['status'].str.contains('UNDERPAID', na=False)])
overpaid  = len(payment_report[payment_report['status'].str.contains('OVERPAID',  na=False)])
print(f'\n  Payments:')
print(f'    ✅ Verified:   {verified}')
print(f'    ❌ Underpaid:  {underpaid}')
print(f'    ⚠️  Overpaid:   {overpaid}')

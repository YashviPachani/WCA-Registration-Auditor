# validator.py
import pandas as pd

def find_missing_in_wca(wca_df, form_df):
    """People who filled the form but never registered on WCA."""
    form_ids = set(form_df['wca_id'].dropna())
    wca_ids = set(wca_df['wca_id'].dropna())
    missing = form_ids - wca_ids
    return form_df[form_df['wca_id'].isin(missing)][['name', 'email', 'wca_id']]

def find_missing_in_form(wca_df, form_df):
    """People registered on WCA but never filled the form."""
    wca_ids = set(wca_df['wca_id'].dropna())
    form_ids = set(form_df['wca_id'].dropna())
    missing = wca_ids - form_ids
    return wca_df[wca_df['wca_id'].isin(missing)][['name', 'wca_id']]

def find_event_mismatches(wca_df, form_df):
    """Events selected on WCA but not on form, or vice versa."""
    results = []
    merged = pd.merge(wca_df, form_df, on='wca_id', suffixes=('_wca', '_form'))
    
    for _, row in merged.iterrows():
        wca_events = set(row['events_wca'])
        form_events = set(row['events_form'])
        only_wca = wca_events - form_events
        only_form = form_events - wca_events
        
        if only_wca or only_form:
            results.append({
                'name': row['name_wca'],
                'wca_id': row['wca_id'],
                'in_wca_not_form': list(only_wca),
                'in_form_not_wca': list(only_form)
            })
    
    return pd.DataFrame(results)

def find_duplicates(form_df):
    """Same email, WCA ID, or phone submitted twice."""
    dupes = {}
    dupes['email'] = form_df[form_df.duplicated('email', keep=False)]
    dupes['wca_id'] = form_df[form_df.duplicated('wca_id', keep=False)]
    return dupes
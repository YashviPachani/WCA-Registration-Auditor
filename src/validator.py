import pandas as pd
 
 
def find_missing_in_wca(matched_df):
    """People who filled the form but never registered on WCA."""
    return matched_df[matched_df['missing_in_wca']][['name', 'email', 'wca_id']].reset_index(drop=True)
 
 
def find_missing_in_form(matched_df):
    """People registered on WCA but never filled the form."""
    return matched_df[matched_df['missing_in_form']][['name', 'wca_id']].reset_index(drop=True)
 
 
def find_event_mismatches(matched_df):
    """Events selected on WCA but not on form, or vice versa."""
    results = []
    both = matched_df[~matched_df['missing_in_wca'] & ~matched_df['missing_in_form']]
 
    for _, row in both.iterrows():
        wca_events  = set(row['events_wca'])
        form_events = set(row['events_form'])
        only_wca    = wca_events - form_events
        only_form   = form_events - wca_events
 
        if only_wca or only_form:
            results.append({
                'name':            row['name'],
                'wca_id':          row['wca_id'],
                'in_wca_not_form': ', '.join(sorted(only_wca)),
                'in_form_not_wca': ', '.join(sorted(only_form)),
            })
 
    return pd.DataFrame(results)
 
 
def find_duplicates(form_df):
    """Same email or WCA ID submitted more than once."""
    return {
        'email':  form_df[form_df.duplicated('email',  keep=False)],
        'wca_id': form_df[form_df.duplicated('wca_id', keep=False)],
    }
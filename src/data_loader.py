import pandas as pd


def load_file(file_path):
    if file_path.endswith(".csv"):
        return pd.read_csv(file_path)

    elif file_path.endswith(".xlsx"):
        return pd.read_excel(file_path)

    else:
        raise ValueError("Unsupported file format")


def clean_name(name):
    return str(name).strip().lower()


def clean_email(email):
    return str(email).strip().lower()


def clean_events(event_string):
    if pd.isna(event_string):
        return []

    return [event.strip().lower() for event in str(event_string).split(",")]


def prepare_wca_dataframe(df):

    return pd.DataFrame({
        "wca_id": df["WCA ID"],
        "name": df["Name"].str.strip().str.lower(),
        "events_wca": df["Events"].apply(clean_events),
    })


def prepare_form_dataframe(df):

    return pd.DataFrame({
        "wca_id": df["WCA ID"],
        "name": df["Name"].str.strip().str.lower(),
        "email": df["Email"].str.strip().str.lower(),
        "events_form": df["Events"].apply(clean_events),
        "amount_paid": pd.to_numeric(df["Amount Paid"], errors="coerce"),
    })


def save_clean_data(df, output_path):
    df.to_csv(output_path, index=False)

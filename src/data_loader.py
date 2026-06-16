import pandas as pd


def load_file(file):

    if file.name.endswith(".csv"):
        return pd.read_csv(file)

    elif file.name.endswith(".xlsx"):
        return pd.read_excel(file)

    else:
        raise ValueError("Unsupported file format")


def clean_name(name):
    return str(name).strip().lower()


def clean_email(email):
    return str(email).strip().lower()


def clean_events(event_string):

    if pd.isna(event_string):
        return []

    event_map = {
        "3x3x3 cube": "333",
        "2x2x2 cube": "222",
        "4x4x4 cube": "444",
        "5x5x5 cube": "555",
        "3x3x3 one-handed": "333oh",
        "3x3x3 blindfolded": "333bf",
        "3x3x3 fewest moves": "333fm",
        "clock": "clock",
        "pyraminx": "pyram",
        "megaminx": "minx",
        "skewb": "skewb",
        "square1": "sq1",
    }

    events = []

    for event in str(event_string).split(","):
        event = event.strip().lower()

        if event in event_map:
            events.append(event_map[event])

    return events


def prepare_wca_dataframe(df):

    EVENT_CODES = {
        "333",
        "222",
        "444",
        "555",
        "666",
        "777",
        "333bf",
        "333fm",
        "333oh",
        "clock",
        "minx",
        "pyram",
        "skewb",
        "sq1",
        "444bf",
        "555bf",
        "333mbf",
    }

    # Detect which WCA events actually exist in this export
    available_events = [col for col in df.columns if col in EVENT_CODES]

    print("Detected events:", available_events)

    def extract_events(row):

        events = []

        for event in available_events:
            value = row[event]

            # WCA exports typically use 1/0 for selected events
            if pd.notna(value) and str(value).strip() == "1":
                events.append(event)

        return events

    return pd.DataFrame({
        "wca_id": df["WCA ID"],
        "name": df["Name"].astype(str).str.strip().str.lower(),
        "email_wca": (
            df["Email"].astype(str).str.strip().str.lower()
            if "Email" in df.columns
            else None
        ),
        "events_wca": df.apply(extract_events, axis=1),
    })


def prepare_form_dataframe(df):
    if "Timestamp" in df.columns:
        df = df.sort_values("Timestamp", ascending=False)

    return pd.DataFrame({
        "wca_id": df["WCA ID (if available)"],
        "name": df["Participant Name"].str.strip().str.lower(),
        "email": df["E-mail ID:"].str.strip().str.lower(),
        "events_form": df["Events you wish to participate in:"].apply(clean_events),
        "amount_paid": pd.to_numeric(df["Total"], errors="coerce"),
    })


def save_clean_data(df, output_path):
    df.to_csv(output_path, index=False)

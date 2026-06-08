import pandas as pd


def match_by_wca_id(wca_df, form_df):

    matched_df = pd.merge(
        wca_df, form_df, on="wca_id", how="outer", suffixes=("_wca", "_form")
    )
    matched_df["name"] = matched_df.apply(combine_names, axis=1)
    matched_df["missing_in_wca"] = matched_df["events_wca"].isna()

    matched_df["missing_in_form"] = matched_df["events_form"].isna()

    final_df = matched_df[
        [
            "wca_id",
            "name",
            "email",
            "events_wca",
            "events_form",
            "amount_paid",
            "missing_in_wca",
            "missing_in_form",
        ]
    ]
    return final_df


def combine_names(row):

    if pd.notna(row["name_wca"]):
        return row["name_wca"]

    return row["name_form"]


def save_matched_data(df):

    df.to_csv("data/processed/matched_data.csv", index=False)


def generate_summary(df):

    print("Missing in WCA:", df["missing_in_wca"].sum())

    print("Missing in Form:", df["missing_in_form"].sum())

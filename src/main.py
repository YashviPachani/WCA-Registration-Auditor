from src.data_loader import load_file, prepare_wca_dataframe, prepare_form_dataframe

from src.matcher import match_by_wca_id


def main():

    print("Loading files...")

    wca_raw = load_file("data/raw/wca_sample.csv")
    form_raw = load_file("data/raw/form_sample.csv")

    print("Preparing data...")

    wca_df = prepare_wca_dataframe(wca_raw)
    form_df = prepare_form_dataframe(form_raw)

    print("\nWCA Data:")
    print(wca_df)

    print("\nForm Data:")
    print(form_df)

    print("\nMatching competitors...")

    matched_df = match_by_wca_id(wca_df, form_df)

    print("\nMatched Data:")
    print(matched_df)

    print("\nSummary:")
    print("Missing in WCA:", matched_df["missing_in_wca"].sum())

    print("Missing in Form:", matched_df["missing_in_form"].sum())

    matched_df.to_csv("data/processed/matched_data.csv", index=False)

    print("\nSaved to: data/processed/matched_data.csv")


if __name__ == "__main__":
    main()

from data_loader import load_file, prepare_wca_dataframe, prepare_form_dataframe


def main():

    print("Loading files...")

    wca_raw = load_file("data/raw/DAU cube open wca.csv")
    form_raw = load_file("data/raw/DAU cube open form.csv")

    print("Preparing data...")

    wca_df = prepare_wca_dataframe(wca_raw)
    form_df = prepare_form_dataframe(form_raw)
    print(form_df["data/raw/DAU cube open form.csv"].head(10).tolist())
    print(wca_df["data/raw/DAU cube open wca.csv"].head(10).tolist())


if __name__ == "__main__":
    main()

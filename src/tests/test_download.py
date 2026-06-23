import pandas as pd

from src.data_loader import load_file, prepare_form_dataframe

from src.download_screenshots import extract_file_id

form_raw = pd.read_csv("data/raw/Syno26 form.csv")

form_df = prepare_form_dataframe(form_raw)

sample_link = form_df.iloc[0]["screenshot_link"]

print("LINK:")
print(sample_link)

file_id = extract_file_id(sample_link)

print("\nFILE ID:")
print(file_id)

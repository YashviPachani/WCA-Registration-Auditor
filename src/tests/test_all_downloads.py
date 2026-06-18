import sys
import os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

sys.path.insert(0, project_root)
import pandas as pd

from src.data_loader import prepare_form_dataframe

from src.download_screenshots import download_all_screenshots

form_raw = pd.read_csv("data/raw/Syno26 form.csv")

form_df = prepare_form_dataframe(form_raw)

download_all_screenshots(form_df)

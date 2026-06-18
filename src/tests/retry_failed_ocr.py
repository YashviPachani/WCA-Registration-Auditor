import sys
import os
import pandas as pd

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

sys.path.insert(0, project_root)

from src.ocr import extract_text, extract_amount


OCR_FILE = "data/processed/ocr_results.csv"
SCREENSHOT_DIR = "data/screenshots"


def retry_failed():

    df = pd.read_csv(OCR_FILE)

    failed = df[df["amount"].isna()]

    print(f"Retrying {len(failed)} failed screenshots...\n")

    for idx, row in failed.iterrows():
        filename = row["file"]

        image_path = os.path.join(SCREENSHOT_DIR, filename)

        if not os.path.exists(image_path):
            print(f"Missing file: {filename}")
            continue

        text = extract_text(image_path)

        amount = extract_amount(text)

        df.loc[idx, "ocr_text"] = text
        df.loc[idx, "amount"] = amount

        print(f"{filename} -> {amount}")

    df.to_csv(OCR_FILE, index=False)

    print("\nUpdated OCR results saved.")


if __name__ == "__main__":
    retry_failed()

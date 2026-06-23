import sys
import os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

sys.path.insert(0, project_root)

from src.payment_ocr import process_all_screenshots

if __name__ == "__main__":
    df = process_all_screenshots()

    os.makedirs("data/processed", exist_ok=True)

    df.to_csv("data/processed/ocr_results.csv", index=False)

    print("\nSaved to data/processed/ocr_results.csv")

    print("\nOCR Failures:", df["amount"].isna().sum())

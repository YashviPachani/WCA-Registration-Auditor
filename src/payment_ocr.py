import os
import pandas as pd

from src.ocr import extract_text, extract_amount


def process_all_screenshots():

    folder = "data/screenshots"

    results = []

    files = [
        f for f in os.listdir(folder) if f.lower().endswith((".jpg", ".jpeg", ".png"))
    ]

    total = len(files)

    for i, file in enumerate(files, start=1):
        image_path = os.path.join(folder, file)

        text = extract_text(image_path)

        amount = extract_amount(text)

        print(f"[{i}/{total}] {file} -> {amount}")

        results.append({"file": file, "amount": amount, "ocr_text": text})

    return pd.DataFrame(results)

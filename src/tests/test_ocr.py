import sys
import os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

sys.path.insert(0, project_root)
from src.ocr import extract_text, extract_amount

text = extract_text("data/screenshots/test.jpeg")

print(text)

print("Amount:", extract_amount(text))

import sys
import os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

sys.path.insert(0, project_root)
import re


def extract_file_id(url):

    match = re.search(r"id=([a-zA-Z0-9_-]+)", str(url))

    if match:
        return match.group(1)

    return None


url = "https://drive.google.com/open?id=1C8-od-UMekABfze94RKLEKlcKyNe4bN2"

print(extract_file_id(url))

import sys
import os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

sys.path.insert(0, project_root)

from src.download_screenshots import download_file

file_id = "1FR0KDgQBvsVqQkAFGPgMSCNpfeiHIO0D"

download_file(file_id, "test.jpg")

print("Download Complete")

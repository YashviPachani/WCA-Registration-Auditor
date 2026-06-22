"""
drive_reader.py
Downloads files from Google Drive using a Service Account.
"""
import io
import os
import re
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
CREDENTIALS_PATH = 'credentials.json'  # path to your service account JSON


def get_drive_service():
    creds = service_account.Credentials.from_service_account_file(
        CREDENTIALS_PATH, scopes=SCOPES
    )
    return build('drive', 'v3', credentials=creds)


def extract_file_id(drive_link):
    """Extract the file ID from various Google Drive link formats."""
    if not drive_link or not isinstance(drive_link, str):
        return None

    # Format: https://drive.google.com/open?id=FILE_ID
    match = re.search(r'id=([a-zA-Z0-9_-]+)', drive_link)
    if match:
        return match.group(1)

    # Format: https://drive.google.com/file/d/FILE_ID/view
    match = re.search(r'/d/([a-zA-Z0-9_-]+)', drive_link)
    if match:
        return match.group(1)

    return None


def download_file(drive_link, output_path):
    """Download a file from Google Drive given its share link."""
    file_id = extract_file_id(drive_link)
    if not file_id:
        raise ValueError(f"Could not extract file ID from link: {drive_link}")

    service = get_drive_service()
    request = service.files().get_media(fileId=file_id)

    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()

    with open(output_path, 'wb') as f:
        f.write(fh.getvalue())

    return output_path


if __name__ == "__main__":
    # Test with the sample link
    test_link = "https://drive.google.com/open?id=1C8-od-UMekABfze94RKLEKlcKyNe4bN2"
    output = download_file(test_link, "test_screenshot.jpg")  # save in current folder
    print(f"Downloaded successfully to: {output}")
    print(f"File size: {os.path.getsize(output)} bytes")
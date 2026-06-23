import io
import os
import re

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload


SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

creds = Credentials.from_service_account_file("credentials.json", scopes=SCOPES)

drive_service = build("drive", "v3", credentials=creds)


def extract_file_id(url):

    match = re.search(r"id=([a-zA-Z0-9_-]+)", str(url))

    if match:
        return match.group(1)

    return None


def safe_filename(name):

    return str(name).replace(" ", "_").replace("/", "_").replace("\\", "_")


def download_file(file_id, output_path):

    request = drive_service.files().get_media(fileId=file_id)

    fh = io.FileIO(output_path, "wb")

    downloader = MediaIoBaseDownload(fh, request)

    done = False

    while not done:
        status, done = downloader.next_chunk()

    print(f"Downloaded: {output_path}")


def download_all_screenshots(df):

    os.makedirs("data/screenshots", exist_ok=True)

    success = 0
    failed = 0

    for _, row in df.iterrows():
        try:
            link = row.get("screenshot_link")

            if not link:
                print("Skipping empty screenshot link")
                continue

            file_id = extract_file_id(link)

            if not file_id:
                print(f"Invalid link: {link}")
                failed += 1
                continue

            participant = safe_filename(row["name"])

            wca_id = row.get("wca_id")

            if (
                wca_id is not None
                and str(wca_id).strip() != ""
                and str(wca_id).lower() != "nan"
            ):
                filename = f"{wca_id}_{participant}.jpg"
            else:
                filename = f"{participant}.jpg"

            output_path = os.path.join("data/screenshots", filename)

            print("\n" + "=" * 60)
            print(f"Participant : {participant}")
            print(f"File ID     : {file_id}")
            print(f"Saving to   : {output_path}")

            download_file(file_id, output_path)

            success += 1

        except Exception as e:
            failed += 1

            print(f"FAILED for {row.get('name', 'Unknown')}")

            print(e)

    print("\n" + "=" * 60)
    print("DOWNLOAD SUMMARY")
    print("=" * 60)
    print(f"Downloaded : {success}")
    print(f"Failed     : {failed}")

    os.makedirs("data/screenshots", exist_ok=True)

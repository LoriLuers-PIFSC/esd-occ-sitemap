import csv
import json
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from pathlib import Path


BUCKET = "nmfs_odp_pifsc"
BUCKET_ROOT = "PIFSC/ESD/ARP/Fixed_Sites_Projects/occ_map_maker"
OBJECTS_API = f"https://storage.googleapis.com/storage/v1/b/{BUCKET}/o"
DATA_DIR = Path(__file__).resolve().parents[1] / "_data"

COLLECTIONS = {
    "2024": "HARAMP2024_FIXED_photos",
    "2025": "CNMI_RAMP_2025_FIXED_photos",
    "2026": "PRIA_ASRAMP2026_FIXED_photos",
}
CATEGORIES = {
    "Site_Photos": "Site Photos",
    "STR_Photos": "STR Photos",
}
FIELDS = ["site_id", "category", "photo_name", "bucket_folder"]
PHOTO_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".tif", ".tiff"}


def list_objects(prefix):
    page_token = None
    while True:
        params = {"prefix": prefix, "maxResults": 1000}
        if page_token:
            params["pageToken"] = page_token
        request = Request(f"{OBJECTS_API}?{urlencode(params)}")
        try:
            with urlopen(request, timeout=60) as response:
                page = json.load(response)
        except (HTTPError, URLError, TimeoutError) as error:
            raise RuntimeError(f"Could not list GCS objects under {prefix}: {error}") from error

        yield from page.get("items", [])
        page_token = page.get("nextPageToken")
        if not page_token:
            break


def build_index(year, collection):
    prefix = f"{BUCKET_ROOT}/{collection}/"
    rows = []

    for item in list_objects(prefix):
        relative_path = item["name"][len(prefix):]
        parts = relative_path.split("/")
        if len(parts) != 3 or parts[0] not in CATEGORIES:
            continue
        if Path(parts[2]).suffix.lower() not in PHOTO_EXTENSIONS:
            continue

        bucket_folder = parts[1]
        site_id = re.sub(r"\s+\([^)]*\)$", "", bucket_folder).strip()
        rows.append(
            {
                "site_id": site_id,
                "category": CATEGORIES[parts[0]],
                "photo_name": parts[2],
                "bucket_folder": bucket_folder,
            }
        )

    output_path = DATA_DIR / f"bucket_photo_index_{year}.csv"
    with output_path.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    return output_path, len(rows)


def main():
    for year, collection in COLLECTIONS.items():
        output_path, count = build_index(year, collection)
        print(f"Wrote {count} photo entries to {output_path}")


if __name__ == "__main__":
    main()

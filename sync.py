import pandas as pd
import json
import os
import requests
from slugify import slugify

# === CONFIGURATION ===
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS6DwoZGGGSoNgv4N3CccevntUCCHhaYNWR4MyQi_GlgfqRTTwgcSGgtNeIh-PmiKLLhKzY2dc-4-mE/pub?output=csv"
JSON_FILE = "igbo_cosmology.json"
AUDIO_DIR = "assets/pronunciations"
IMAGE_DIR = "assets/images"

# === CREATE FOLDERS IF THEY DON'T EXIST ===
os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(IMAGE_DIR, exist_ok=True)

# === UTILS ===
def convert_google_drive_url(url):
    if "drive.google.com" in url:
        if "/d/" in url:
            try:
                file_id = url.split("/d/")[1].split("/")[0]
                return f"https://drive.google.com/uc?export=download&id={file_id}"
            except Exception:
                return ""
        elif "id=" in url:
            file_id = url.split("id=")[-1]
            return f"https://drive.google.com/uc?export=download&id={file_id}"
    return url  # Return original if it's not a recognized Drive link

def download_file(url, path):
    try:
        response = requests.get(url, stream=True)
        content_type = response.headers.get('Content-Type', '')

        if response.status_code == 200 and 'text/html' not in content_type:
            with open(path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"✅ Downloaded: {path}")
            return True
        else:
            print(f"❌ Invalid content at {url} — Content-Type: {content_type}")
            return False
    except Exception as e:
        print(f"❌ Error downloading {path}: {e}")
        return False

# === LOAD SHEET AND JSON ===
df = pd.read_csv(CSV_URL).fillna("")

# Load existing JSON data
try:
    with open(JSON_FILE, "r", encoding="utf-8") as f:
        existing_data = json.load(f)
except FileNotFoundError:
    existing_data = []

# Create set of existing keys using the correct column names
existing_keys = {(item["section"], item["name"]) for item in existing_data}
new_entries = []

# === PROCESS NEW ENTRIES ===
for _, row in df.iterrows():
    key = (row["Section"], row["Name"])
    if key in existing_keys:
        continue
    
    slug = slugify(row["Name"])
    
    # === AUDIO ===
    audio_url = convert_google_drive_url(row["Audio"])
    audio_filename = f"pronunciation_ig_{slug}.mp3"
    audio_path = os.path.join(AUDIO_DIR, audio_filename)
    audio_github_url = f"https://raw.githubusercontent.com/ezeanyimhenry/igbo-cosmology/main/{AUDIO_DIR}/{audio_filename}"
    
    # === IMAGE ===
    image_url = convert_google_drive_url(row["Image"])
    image_filename = f"{slug}.jpg"
    image_path = os.path.join(IMAGE_DIR, image_filename)
    image_github_url = f"https://raw.githubusercontent.com/ezeanyimhenry/igbo-cosmology/main/{IMAGE_DIR}/{image_filename}"
    
    # === DOWNLOAD FILES ===
    if row["Audio"]:
        download_file(audio_url, audio_path)
    if row["Image"]:
        download_file(image_url, image_path)
    
    # === ADD NEW ENTRY ===
    new_entries.append({
        "section": row["Section"],
        "name": row["Name"],
        "image": image_github_url if row["Image"] else "",
        "audio": audio_github_url if row["Audio"] else "",
        "description": row["Description"]
    })

# === SAVE UPDATED JSON ===
if new_entries:
    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(existing_data + new_entries, f, ensure_ascii=False, indent=2)
    print(f"✅ Added {len(new_entries)} new entries to {JSON_FILE}.")
else:
    print("ℹ️ No new entries to add.")

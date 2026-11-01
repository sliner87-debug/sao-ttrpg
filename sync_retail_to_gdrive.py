import os, sys, pathlib
os.chdir(r"H:\Antigravity\SAO Mockup")
sys.path.insert(0, os.getcwd())

from gdrive_sync import authenticate
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

ROOT_FOLDER_ID = "10N4BYRQ4g3-NOJsTm26ah3WD8fKPsBr3" # SAO Sandbox v2
SUITE_FOLDER_NAME = "Millennium_Breach_Retail_Suite"

print("Authenticating with Google Drive...")
creds = authenticate()
service = build('drive', 'v3', credentials=creds)

# 1. Get or create Millennium_Breach_Retail_Suite subfolder
q = f"name='{SUITE_FOLDER_NAME}' and '{ROOT_FOLDER_ID}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
res = service.files().list(q=q, fields='files(id, name)').execute()
items = res.get('files', [])

if items:
    suite_id = items[0]['id']
    print(f"Found existing '{SUITE_FOLDER_NAME}' folder: {suite_id}")
else:
    meta = {
        'name': SUITE_FOLDER_NAME,
        'parents': [ROOT_FOLDER_ID],
        'mimeType': 'application/vnd.google-apps.folder'
    }
    folder = service.files().create(body=meta, fields='id').execute()
    suite_id = folder.get('id')
    print(f"Created new '{SUITE_FOLDER_NAME}' folder: {suite_id}")

# 2. Upload retail files
dist_dir = pathlib.Path(r"H:\Antigravity\SAO Mockup\dist")
reviews_dir = pathlib.Path(r"H:\Antigravity\SAO Mockup\reviews")

files_to_sync = [
    dist_dir / "BOX_SET_1_THE_SPARK_OF_THE_BREACH.epub",
    dist_dir / "BOX_SET_1_THE_SPARK_OF_THE_BREACH.md",
    dist_dir / "BOX_SET_2_THE_IRON_PERIMETER.epub",
    dist_dir / "BOX_SET_2_THE_IRON_PERIMETER.md",
    dist_dir / "BOX_SET_3_THE_FIFTH_IRON_SUN.epub",
    dist_dir / "BOX_SET_3_THE_FIFTH_IRON_SUN.md",
    dist_dir / "MILLENNIUM_BREACH_COMPLETE_15_BOOK_SAGA_OMNIBUS.epub",
    dist_dir / "MILLENNIUM_BREACH_COMPLETE_15_BOOK_SAGA_OMNIBUS.md",
    dist_dir / "RETAIL_METADATA_AND_MARKETING_SUITE.md",
    reviews_dir / "MILLENNIUM_BREACH_SERIES_MASTER_CRITICAL_REVIEW.md"
]

for p in files_to_sync:
    fname = p.name
    mime = "application/epub+zip" if fname.endswith(".epub") else "text/markdown"
    print(f"Syncing {fname} ({p.stat().st_size:,} bytes)...")
    
    # Check if exists
    search_q = f"name='{fname}' and '{suite_id}' in parents and trashed=false"
    existing = service.files().list(q=search_q, fields="files(id)").execute().get("files", [])
    
    media = MediaFileUpload(str(p), mimetype=mime, resumable=True)
    if existing:
        file_id = existing[0]["id"]
        service.files().update(fileId=file_id, media_body=media).execute()
        print(f"  [OK] Updated existing file: {file_id}")
    else:
        created = service.files().create(body={"name": fname, "parents": [suite_id]}, media_body=media, fields="id").execute()
        print(f"  [OK] Created new file: {created.get('id')}")

print("\nALL 10 RETAIL ASSETS SUCCESSFULLY SYNCED TO GOOGLE DRIVE!")

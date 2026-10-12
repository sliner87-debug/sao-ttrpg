import os
import io
import json
import argparse
from datetime import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload

# Scopes allow full read/write access to Drive metadata and file contents
SCOPES = ['https://www.googleapis.com/auth/drive']

def authenticate():
    creds = None
    # The file gdrive_tokens.json stores the user's access and refresh tokens.
    if os.path.exists('gdrive_tokens.json'):
        creds = Credentials.from_authorized_user_file('gdrive_tokens.json', SCOPES)
    
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('drive_credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('gdrive_tokens.json', 'w') as token:
            token.write(creds.to_json())
            
    return creds

def get_or_create_folder(service, folder_name="saosaves"):
    print(f"Searching for '{folder_name}' folder...")
    results = service.files().list(
        q=f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false", 
        spaces='drive', 
        fields='files(id, name)'
    ).execute()
    
    items = results.get('files', [])
    
    if items:
        print(f"Found folder '{items[0]['name']}'.")
        return items[0]['id']
    else:
        print(f"Could not find folder '{folder_name}'. Creating it now...")
        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        folder = service.files().create(body=file_metadata, fields='id').execute()
        print(f"Folder created with ID: {folder.get('id')}")
        return folder.get('id')

def download_latest_save():
    print("Authenticating with Google Drive...")
    try:
        creds = authenticate()
        service = build('drive', 'v3', credentials=creds)
    except Exception as e:
        print(f"Failed to authenticate: {e}")
        print("Please ensure 'drive_credentials.json' is in the root directory.")
        return

    folder_id = get_or_create_folder(service)
    
    print("Searching for JSON saves inside...")
    # Find all JSON files in that folder, ordered by newest first
    results = service.files().list(
        q=f"'{folder_id}' in parents and mimeType='application/json' and trashed=false", 
        orderBy="createdTime desc", 
        spaces='drive', 
        fields='files(id, name, createdTime)'
    ).execute()
    
    saves = results.get('files', [])
    
    if not saves:
        print("No JSON files found inside the 'saosaves' folder.")
        return
        
    latest_save = saves[0]
    print(f"Downloading latest save: {latest_save['name']} (Uploaded: {latest_save['createdTime']})")
    
    request = service.files().get_media(fileId=latest_save['id'])
    
    # Download directly to 'save1.json' so the game automatically picks it up!
    file_io = io.FileIO('save1.json', 'wb')
    downloader = MediaIoBaseDownload(file_io, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()
        print(f"Download {int(status.progress() * 100)}%.")
        
    print(f"Successfully downloaded and overwrote local game save!")
    print("Refresh your Streamlit app now to load the restored data.")

def upload_save(file_path="save1.json"):
    print("Authenticating with Google Drive...")
    try:
        creds = authenticate()
        service = build('drive', 'v3', credentials=creds)
    except Exception as e:
        print(f"Failed to authenticate: {e}")
        print("Please ensure 'drive_credentials.json' is in the root directory.")
        return

    if not os.path.exists(file_path):
        print(f"File {file_path} does not exist locally. Cannot upload.")
        return

    folder_id = get_or_create_folder(service)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"save_{timestamp}.json"
    
    file_metadata = {
        'name': file_name,
        'parents': [folder_id]
    }
    media = MediaFileUpload(file_path, mimetype='application/json', resumable=True)
    
    print(f"Uploading {file_path} to Google Drive as {file_name}...")
    file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    print(f"Successfully uploaded save! File ID: {file.get('id')}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Sync SAO saves with Google Drive.")
    parser.add_argument('--upload', action='store_true', help="Upload the local save1.json to Google Drive")
    parser.add_argument('--download', action='store_true', help="Download the latest save from Google Drive")
    parser.add_argument('--file', type=str, default="save1.json", help="Specify a file to upload (default: save1.json)")
    
    args = parser.parse_args()
    
    if args.upload:
        upload_save(args.file)
    elif args.download:
        download_latest_save()
    else:
        # Default behavior if no flag is provided
        print("Please specify --upload or --download.")
        print("Example: python gdrive_sync.py --upload")

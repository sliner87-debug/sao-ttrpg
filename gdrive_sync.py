import os
import io
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

# Scopes allow read-only access to Drive metadata and file contents
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

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

def download_latest_save():
    print("Authenticating with Google Drive...")
    try:
        creds = authenticate()
        service = build('drive', 'v3', credentials=creds)
    except Exception as e:
        print(f"Failed to authenticate: {e}")
        print("Please ensure 'drive_credentials.json' is in the root directory.")
        return

    print("Searching for 'saosaves' folder...")
    results = service.files().list(
        q="name='saosaves' and mimeType='application/vnd.google-apps.folder' and trashed=false", 
        spaces='drive', 
        fields='files(id, name)'
    ).execute()
    
    items = results.get('files', [])
    
    if not items:
        print("Could not find a folder named 'saosaves' in your Google Drive.")
        return
        
    folder_id = items[0]['id']
    print(f"Found folder '{items[0]['name']}'. Searching for JSON saves inside...")
    
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

if __name__ == '__main__':
    download_latest_save()

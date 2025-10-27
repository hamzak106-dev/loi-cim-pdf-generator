import os
from typing import Optional
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

class GoogleDriveUploader:
    def __init__(self, credentials_path: str, folder_id: Optional[str] = None):
        self.credentials_path = credentials_path
        self.folder_id = folder_id
        self.service = None
        self._authenticate()
    
    def _authenticate(self):
        try:
            credentials = service_account.Credentials.from_service_account_file(
                self.credentials_path,
                scopes=['https://www.googleapis.com/auth/drive']
            )
            self.service = build('drive', 'v3', credentials=credentials)
            print(f"✅ Google Drive authentication successful")
        except Exception as e:
            print(f"❌ Google Drive authentication failed: {str(e)}")
            raise
    
    def upload_file(self, file_path: str, file_name: Optional[str] = None, mime_type: Optional[str] = None) -> dict:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if not file_name:
            file_name = os.path.basename(file_path)
        
        if not mime_type:
            mime_type = 'application/octet-stream'
        
        file_metadata = {
            'name': file_name,
            'mimeType': mime_type
        }
        
        if self.folder_id:
            file_metadata['parents'] = [self.folder_id]
        
        try:
            media = MediaFileUpload(
                file_path,
                mimetype=mime_type,
                resumable=True
            )
            
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, name, webViewLink',
                supportsAllDrives=True
            ).execute()
            
            file_id = file.get('id')
            self._make_shareable(file_id)
            shareable_url = f"https://drive.google.com/file/d/{file_id}/view?usp=sharing"
            
            result = {
                'file_id': file_id,
                'file_name': file.get('name'),
                'shareable_url': shareable_url
            }
        
            print(f"✅ File uploaded to Google Drive: {file_name}")
            print(f"📎 Shareable URL: {shareable_url}")
            return result
            
        except HttpError as error:
            print(f"❌ Google Drive upload failed: {error}")
            raise
    
    def upload_pdf(self, pdf_path: str, file_name: Optional[str] = None) -> dict:
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        if not file_name:
            file_name = os.path.basename(pdf_path)
        
        file_metadata = {
            'name': file_name,
            'mimeType': 'application/pdf'
        }
        
        if self.folder_id:
            file_metadata['parents'] = [self.folder_id]
        
        try:
            media = MediaFileUpload(
                pdf_path,
                mimetype='application/pdf',
                resumable=True
            )
            
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, name, webViewLink',
                supportsAllDrives=True
            ).execute()
            
            file_id = file.get('id')
            self._make_shareable(file_id)
            shareable_url = f"https://drive.google.com/file/d/{file_id}/view?usp=sharing"
            
            result = {
                'file_id': file_id,
                'file_name': file.get('name'),
                'shareable_url': shareable_url
            }
        
            print(f"✅ PDF uploaded to Google Drive: {file_name}")
            print(f"📎 Shareable URL: {shareable_url}")
            return result
            
        except HttpError as error:
            print(f"❌ Google Drive upload failed: {error}")
            raise
    
    def _make_shareable(self, file_id: str):
        try:
            permission = {
                'type': 'anyone',
                'role': 'reader'
            }
            self.service.permissions().create(
                fileId=file_id,
                body=permission,
                supportsAllDrives=True
            ).execute()
        except HttpError as error:
            print(f"⚠️ Could not make file shareable: {error}")
    
    def _get_shareable_link(self, file_id: str) -> str:
        try:
            file = self.service.files().get(
                fileId=file_id,
                fields='webViewLink',
                supportsAllDrives=True
            ).execute()
            return file.get('webViewLink', f"https://drive.google.com/file/d/{file_id}/view?usp=sharing")
        except HttpError:
            return f"https://drive.google.com/file/d/{file_id}/view?usp=sharing"
    
    def delete_file(self, file_id: str) -> bool:
        try:
            self.service.files().delete(
                fileId=file_id,
                supportsAllDrives=True
            ).execute()
            print(f"🗑️ File deleted from Google Drive: {file_id}")
            return True
        except HttpError as error:
            print(f"❌ Failed to delete file: {error}")
            return False

def create_drive_uploader(credentials_path: str = "service_account.json", 
                         folder_id: Optional[str] = None) -> GoogleDriveUploader:
    return GoogleDriveUploader(credentials_path, folder_id)

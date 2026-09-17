import os
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
import io

# گوگل ڈرائیو سیٹ اپ
SCOPES = ['https://www.googleapis.com/auth/drive']
FOLDER_ID = os.environ.get('GOOGLE_DRIVE_FOLDER_ID')

def convert_word_to_pdf_gdrive(docx_path, output_pdf_path):
    creds_json = json.loads(os.environ.get('GOOGLE_CREDENTIALS_JSON'))
    creds = service_account.Credentials.from_service_account_info(creds_json, scopes=SCOPES)
    drive_service = build('drive', 'v3', credentials=creds)

    # 1. ورڈ فائل گوگل ڈرائیو پر اپ لوڈ کریں (Google Drive خود اسے Docs میں بدل دے گا)
    file_metadata = {
        'name': 'temp_docx_file',
        'parents': [FOLDER_ID],
        'mimeType': 'application/vnd.google-apps.document'
    }
    media = MediaFileUpload(docx_path, mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document', resumable=True)
    
    uploaded_file = drive_service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id'
    ).execute()
    
    file_id = uploaded_file.get('id')

    try:
        # 2. اسے PDF فارمیٹ میں ڈاؤن لوڈ کریں
        request = drive_service.files().export_media(fileId=file_id, mimeType='application/pdf')
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        
        done = False
        while not done:
            status, done = downloader.next_chunk()

        with open(output_pdf_path, 'wb') as f:
            f.write(fh.getvalue())

    finally:
        # 3. ڈرائیو سے عارضی فائل ڈیلیٹ کر دیں تاکہ فولڈر ہمیشہ خالی رہے
        drive_service.files().delete(fileId=file_id).execute()

import os
import json
from flask import Flask, request, send_file
from flask_cors import CORS
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
import io
import traceback

app = Flask(__name__)
CORS(app)

SCOPES = ['https://www.googleapis.com/auth/drive']
FOLDER_ID = os.environ.get('GOOGLE_DRIVE_FOLDER_ID')

def convert_word_to_pdf_gdrive(docx_path, output_pdf_path):
    creds_json = json.loads(os.environ.get('GOOGLE_CREDENTIALS_JSON'))
    creds = service_account.Credentials.from_service_account_info(creds_json, scopes=SCOPES)
    drive_service = build('drive', 'v3', credentials=creds)

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
        request_drive = drive_service.files().export_media(fileId=file_id, mimeType='application/pdf')
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request_drive)
        
        done = False
        while not done:
            status, done = downloader.next_chunk()

        with open(output_pdf_path, 'wb') as f:
            f.write(fh.getvalue())

    finally:
        drive_service.files().delete(fileId=file_id).execute()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'file' not in request.files:
            return 'No file selected', 400
        
        file = request.files['file']
        if file.filename == '':
            return 'Filename is empty', 400
        
        if file:
            input_path = 'temp.docx'
            output_path = 'output.pdf'
            file.save(input_path)
            
            try:
                convert_word_to_pdf_gdrive(input_path, output_path)
                return send_file(output_path, as_attachment=True, download_name='converted.pdf')
            except Exception as e:
                tb = traceback.format_exc()
                api_content = getattr(e, 'content', b'').decode('utf-8', errors='ignore')
                return f'''
                <h3 style="color: red;">Google Drive API Error Details:</h3>
                <pre style="background: #f8f9fa; padding: 15px; border: 1px solid #ccc; white-space: pre-wrap;">{tb}\n\nGoogle API Response:\n{api_content}</pre>
                <br><a href="/">Go Back</a>
                ''', 500
            finally:
                if os.path.exists(input_path):
                    os.remove(input_path)

    return '''
    <!doctype html>
    <html>
    <head><title>Word to PDF Converter</title></head>
    <body style="font-family: Arial; text-align: center; margin-top: 50px;">
        <h2>Word to PDF Converter (Google Drive API)</h2>
        <form method="post" enctype="multipart/form-data">
            <input type="file" name="file" accept=".docx" required style="padding: 10px; margin: 10px;">
            <br>
            <button type="submit" style="padding: 10px 20px; background: #007BFF; color: white; border: none; cursor: pointer;">Convert to PDF</button>
        </form>
    </body>
    </html>
    '''

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

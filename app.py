import os
import json
from flask import Flask, request, send_file, render_template_string
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
import io

app = Flask(__name__)

# گوگل ڈرائیو سیٹ اپ
SCOPES = ['https://www.googleapis.com/auth/drive']
FOLDER_ID = os.environ.get('GOOGLE_DRIVE_FOLDER_ID')

def convert_word_to_pdf_gdrive(docx_path, output_pdf_path):
    creds_json = json.loads(os.environ.get('GOOGLE_CREDENTIALS_JSON'))
    creds = service_account.Credentials.from_service_account_info(creds_json, scopes=SCOPES)
    drive_service = build('drive', 'v3', credentials=creds)

    # 1. ورڈ فائل گوگل ڈرائیو پر اپ لوڈ کریں
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
        request_drive = drive_service.files().export_media(fileId=file_id, mimeType='application/pdf')
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request_drive)
        
        done = False
        while not done:
            status, done = downloader.next_chunk()

        with open(output_pdf_path, 'wb') as f:
            f.write(fh.getvalue())

    finally:
        # 3. ڈرائیو سے عارضی فائل ڈیلیٹ کر دیں
        drive_service.files().delete(fileId=file_id).execute()

# ہوم پیج کا روٹ (جہاں ورڈ فائل اپ لوڈ کرنے کا فارم آئے گا)
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'file' not in request.files:
            return 'کوئی فائل منتخب نہیں کی گئی', 400
        
        file = request.files['file']
        if file.filename == '':
            return 'فائل کا نام خالی ہے', 400
        
        if file:
            input_path = 'temp.docx'
            output_path = 'output.pdf'
            
            file.save(input_path)
            
            try:
                # گوگل ڈرائیو کنورژن فنکشن کال کریں
                convert_word_to_pdf_gdrive(input_path, output_path)
                return send_file(output_path, as_attachment=True, download_name='converted.pdf')
            except Exception as e:
                return f'خرابی پیش آئی: {str(e)}', 500
            finally:
                # لوکل عارضی فائلیں ڈیلیٹ کریں
                if os.path.exists(input_path):
                    os.remove(input_path)

    # سادہ سا HTML فارم جو یوزر کو دکھائے گا
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

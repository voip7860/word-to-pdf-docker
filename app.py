import os
import requests
import traceback
from flask import Flask, request, send_file
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

GOTENBERG_URL = "http://localhost:3000/forms/libreoffice/convert"

@app.route('/convert-word', methods=['POST'])
def convert_word_to_pdf():
    docx_path = None
    pdf_path = None
    try:
        if 'file' not in request.files:
            return 'No file uploaded', 400
        
        file = request.files['file']
        filename_base = os.path.splitext(file.filename)[0]
        safe_filename_base = "".join([c if c.isalnum() else "_" for c in filename_base])
        
        docx_path = f"/tmp/{safe_filename_base}.docx"
        pdf_path = f"/tmp/{safe_filename_base}.pdf"
        file.save(docx_path)

        with open(docx_path, 'rb') as f:
            files = {'files': (f"{safe_filename_base}.docx", f)}
            response = requests.post(GOTENBERG_URL, files=files, timeout=120)

        if response.status_code == 200:
            with open(pdf_path, 'wb') as f_out:
                f_out.write(response.content)
            return send_file(pdf_path, as_attachment=True, download_name=f"{filename_base}.pdf")
        else:
            return f"Gotenberg Error: {response.text}", 500

    except Exception as e:
        return f"Conversion Error: {str(e)}\n{traceback.format_exc()}", 500

    finally:
        if docx_path and os.path.exists(docx_path):
            try:
                os.remove(docx_path)
            except:
                pass

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

import os
import subprocess
import traceback
from flask import Flask, request, send_file
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

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
        
        docx_path = os.path.join("/tmp", f"{safe_filename_base}.docx")
        file.save(docx_path)
        
        # Convert directly using optimized headless engine
        cmd = [
            "libreoffice",
            "--headless",
            "--invisible",
            "--nocrashdump",
            "--nodefault",
            "--nofirststartwizard",
            "--nolockcheck",
            "--nologo",
            "--norestore",
            "--convert-to", "pdf",
            "--outdir", "/tmp",
            docx_path
        ]
        
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=90)
        
        pdf_filename = f"{safe_filename_base}.pdf"
        pdf_path = os.path.join("/tmp", pdf_filename)
        
        if os.path.exists(pdf_path):
            return send_file(pdf_path, as_attachment=True, download_name=f"{filename_base}.pdf")
        else:
            return f"Conversion failed: {result.stderr}", 500
            
    except Exception as e:
        return f"Server Error: {str(e)}\n{traceback.format_exc()}", 500
        
    finally:
        if docx_path and os.path.exists(docx_path):
            try:
                os.remove(docx_path)
            except:
                pass

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

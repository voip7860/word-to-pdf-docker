import os
import subprocess
import traceback
from flask import Flask, request, send_file
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/convert-word', methods=['POST'])
def convert_word_to_pdf():
    try:
        if 'file' not in request.files:
            return 'No file uploaded', 400
        
        file = request.files['file']
        filename_base = os.path.splitext(file.filename)[0]
        docx_path = f"temp_{filename_base}.docx"
        output_dir = "/tmp"
        pdf_path = os.path.join(output_dir, f"{filename_base}.pdf")
        
        file.save(docx_path)
        
        cmd = ["soffice", "--headless", "--convert-to", "pdf", "--outdir", output_dir, docx_path]
        subprocess.run(cmd, check=True)
        
        if os.path.exists(pdf_path):
            return send_file(pdf_path, as_attachment=True, download_name=f"{filename_base}.pdf")
        else:
            return "PDF generation failed", 500
            
    except Exception as e:
        error_details = traceback.format_exc()
        print(error_details)
        return f"Conversion Error: {str(e)}\n{error_details}", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

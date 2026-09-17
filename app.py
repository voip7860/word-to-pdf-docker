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
    temp_pdf_path = None
    try:
        if 'file' not in request.files:
            return 'No file uploaded', 400
        
        file = request.files['file']
        filename_base = os.path.splitext(file.filename)[0]
        # Clean the base filename to avoid spaces/special char issues in linux shell
        safe_filename_base = "".join([c if c.isalnum() else "_" for c in filename_base])
        
        docx_filename = f"temp_{safe_filename_base}.docx"
        docx_path = os.path.abspath(docx_filename)
        output_dir = "/tmp"
        
        # LibreOffice names the output PDF matching the input file's base name
        temp_pdf_path = os.path.join(output_dir, f"temp_{safe_filename_base}.pdf")
        final_pdf_path = os.path.join(output_dir, f"{safe_filename_base}.pdf")
        
        file.save(docx_path)
        
        cmd = ["soffice", "--headless", "--convert-to", "pdf", "--outdir", output_dir, docx_path]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        if result.returncode != 0:
            return f"LibreOffice Error: {result.stderr}", 500
        
        # Check if LibreOffice created the file with 'temp_' prefix
        if os.path.exists(temp_pdf_path):
            # Rename it to clean name
            if os.path.exists(final_pdf_path):
                os.remove(final_pdf_path)
            os.rename(temp_pdf_path, final_pdf_path)
            pdf_path = final_pdf_path
        elif os.path.exists(final_pdf_path):
            pdf_path = final_pdf_path

        if pdf_path and os.path.exists(pdf_path):
            return send_file(pdf_path, as_attachment=True, download_name=f"{filename_base}.pdf")
        else:
            return f"PDF generation failed. LibreOffice output: {result.stdout} {result.stderr}", 500
            
    except Exception as e:
        error_details = traceback.format_exc()
        print(error_details)
        return f"Conversion Error: {str(e)}\n{error_details}", 500
        
    finally:
        # Cleanup temporary input file
        if docx_path and os.path.exists(docx_path):
            try:
                os.remove(docx_path)
            except:
                pass

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

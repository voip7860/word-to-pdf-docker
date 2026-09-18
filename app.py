import os
import traceback
import cloudconvert
from flask import Flask, request, send_file
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# یہاں اپنی CloudConvert کی API Key پیسٹ کریں
CLOUDCONVERT_API_KEY = "YOUR_CLOUDCONVERT_API_KEY_HERE"

cloudconvert.configure(api_key=CLOUDCONVERT_API_KEY)

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
        
        docx_filename = f"{safe_filename_base}.docx"
        pdf_filename = f"{safe_filename_base}.pdf"
        
        docx_path = os.path.join("/tmp", docx_filename)
        pdf_path = os.path.join("/tmp", pdf_filename)
        
        file.save(docx_path)
        
        # CloudConvert Job Creation for MS Word exact rendering
        job = cloudconvert.Job.create(payload={
            "tasks": {
                "import-my-file": {
                    "operation": "upload"
                },
                "convert-my-file": {
                    "operation": "convert",
                    "input": "import-my-file",
                    "output_format": "pdf",
                    "engine": "office"
                },
                "export-my-file": {
                    "operation": "export",
                    "input": "convert-my-file"
                }
            }
        })
        
        # Upload docx file to CloudConvert
        upload_task = [task for task in job['tasks'] if task['name'] == 'import-my-file'][0]
        cloudconvert.Task.upload(file_name=docx_path, task=upload_task)
        
        # Wait for conversion to finish
        cloudconvert.Job.wait(id=job['id'])
        
        # Download converted PDF
        export_task = [task for task in job['tasks'] if task['name'] == 'export-my-file'][0]
        file_info = export_task['result']['files'][0]
        cloudconvert.Task.download(file_name=pdf_path, task=export_task)
        
        if os.path.exists(pdf_path):
            return send_file(pdf_path, as_attachment=True, download_name=f"{filename_base}.pdf")
        else:
            return "PDF Download failed from CloudConvert", 500

    except Exception as e:
        return f"CloudConvert Error: {str(e)}\n{traceback.format_exc()}", 500

    finally:
        if docx_path and os.path.exists(docx_path):
            try:
                os.remove(docx_path)
            except:
                pass
        if pdf_path and os.path.exists(pdf_path):
            try:
                os.remove(pdf_path)
            except:
                pass

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

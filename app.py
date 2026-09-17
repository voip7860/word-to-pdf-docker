import os
import cloudconvert
from flask import Flask, request, send_file
from flask_cors import CORS
import traceback
import urllib.request

app = Flask(__name__)
CORS(app)  # Enable CORS for cross-origin requests from your main site

# CloudConvert API Setup
CLOUDCONVERT_API_KEY = os.environ.get('CLOUDCONVERT_API_KEY')
cloudconvert.configure(api_key=CLOUDCONVERT_API_KEY, sandbox=False)

# Conversion API endpoint matching your PHP/frontend structure
@app.route('/convert-word', methods=['POST'])
def convert_word():
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
            # CloudConvert Job Creation
            job = cloudconvert.Job.create(payload={
                "tasks": {
                    "import-1": {
                        "operation": "import/upload"
                    },
                    "convert-1": {
                        "operation": "convert",
                        "input": "import-1",
                        "output_format": "pdf"
                    },
                    "export-1": {
                        "operation": "export/url",
                        "input": "convert-1"
                    }
                }
            })

            # Find upload task and upload the file
            upload_task_id = job['result'][0]['id']
            upload_task = cloudconvert.Task.find(id=upload_task_id)
            
            with open(input_path, 'rb') as f:
                cloudconvert.Task.upload(upload_task=upload_task, file_object=f)

            # Wait for job completion and get download URL
            job = cloudconvert.Job.wait(id=job['id'])
            export_task = [task for task in job['tasks'] if task['name'] == 'export-1'][0]
            file_url = export_task['result']['files'][0]['url']
            
            # Download PDF and send back to frontend
            urllib.request.urlretrieve(file_url, output_path)

            return send_file(output_path, as_attachment=True, download_name='converted.pdf')
            
        except Exception as e:
            error_details = traceback.format_exc()
            return f'Conversion Error:\n{error_details}', 500
        finally:
            if os.path.exists(input_path):
                os.remove(input_path)

@app.route('/', methods=['GET'])
def index():
    return "CloudConvert Python Server for Word to PDF is Running Successfully!"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

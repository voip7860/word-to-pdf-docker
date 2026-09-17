import os
import cloudconvert
from flask import Flask, request, send_file
from flask_cors import CORS
import traceback
import urllib.request

app = Flask(__name__)
CORS(app)  # Enable CORS

# Hardcoded CloudConvert API Key
CLOUDCONVERT_API_KEY = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhdWQiOiIxIiwianRpIjoiYmU0NGRmMDAyMTA5NzBmNGE3NjNhOWM0Y2JlZWFhMGMwMzAzYTlkZjRkNDNmZjkyZjc2NmZiMGUyZmM2OWQ3ZGE0NjczNmFkZTFjYmNmYjAiLCJpYXQiOjE3ODk2Nzg0NjEuNzg0NzM4LCJuYmYiOjE3ODk2Nzg0NjEuNzg0NzQsImV4cCI6NDk0NTM1MjA2MS43NzY1MjgsInN1YiI6Ijc3MDA4MTE0Iiwic2NvcGVzIjpbInVzZXIucmVhZCIsInRhc2kucmVhZCIsInRhc2sud3JitelXRlswLmltU21rbVFjam04T3VjcXd1WkZVcklPaUV6Q1FDOGFPTnVuNDN3X205RVVfSTRSM2UwTWRuZW5aPnB2R0xNNFFybVBUcjNSNEVwczlGUjhLQ2tFNDVkRDRja1plWW1aZHZWTVMxMVRJRFBzWnFhQzRBVVlCeU5jZk5DelZ3MWxPQzdCY0lYaWQ5RkVPNGc5S0t2SFg2OF93MHFycGFmbFFCcFNCSWd4Q1dNOGlhZ3RCOXBsdDFqdXc1WnF5OGFnTHdBZaDo4bnhqV3MzNkhySk42cjU4Q2NqbUdocVFTcFpyenhwbDM3WFdsZGxOWll4RnVUU1RqU1hmdXNfemljZS0wblRuSzl3cTAwd0dtZGk2ZlRYaGFEVHNVcmwxVS10b3BGMTRtempqQUhJWFVHNl9WaFJuMHoxQlhULW1Xdlp3d2h2NjRFaExCcTdtV0MyS1E4cDJCUE5LdnBKcExkeHpLLUdtZTNybklBRWpXNnVpTDQ5N0xSWlh4T0lyc1I5bm9pS3JtZDNGN3h2ZGlPNXc4c0N1SlFwbkpYV19LT283ZVE4NjNOZUlyT2ZaRGVuX0lpMjItR2phYi15TF9meXRGaEdwZHNqYk1ka1pEeXdrT3BBQnZHTEFWaUhXamtLeWJUaDhpZUNpenhCU21mbUxiOHlqVkNST21aLWh6a2pyMUFLNmpObGstNllBTWxpNHpsMlB1aWZ1cEctSVVMbHVWcjQ5aS0xYjJtSkpDdzZZN2p6eW1EVDRaVkROREhHZTIrZG50OE1RaEg4enhWZ3ZoUzVaUU82YlNBWEJ2NWVNNGo2dnZnQUM2MFNud2k3dmdsQmFwcjlYN2Z6OU9wbWhhblNLRDBHckRNWjBEUXNLVDRzUWdQVm5jYWpNblJYeHRtbWpqXzFR"

cloudconvert.configure(api_key=CLOUDCONVERT_API_KEY, sandbox=False)

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

            # Safely extract tasks from job response
            job_id = job.get('id') or job.get('data', {}).get('id')
            tasks = job.get('tasks', [])
            if not tasks and 'data' in job:
                tasks = job['data'].get('tasks', [])

            upload_task = None
            for task in tasks:
                if task.get('name') == 'import-1':
                    upload_task = task
                    break

            if not upload_task:
                return "Error: Upload task not found in CloudConvert response.", 500

            with open(input_path, 'rb') as f:
                cloudconvert.Task.upload(upload_task=upload_task, file_object=f)

            # Wait for job completion
            job = cloudconvert.Job.wait(id=job_id)

            job_tasks = job.get('tasks', [])
            if not job_tasks and 'data' in job:
                job_tasks = job['data'].get('tasks', [])

            export_task = [task for task in job_tasks if task.get('name') == 'export-1'][0]
            file_url = export_task['result']['files'][0]['url']
            
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
    return "CloudConvert Python Server is Running Successfully!"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

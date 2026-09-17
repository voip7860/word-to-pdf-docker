import os
import cloudconvert
from flask import Flask, request, send_file
from flask_cors import CORS
import traceback
import urllib.request

app = Flask(__name__)
CORS(app)  # Enable CORS

# Hardcoded CloudConvert API Key
CLOUDCONVERT_API_KEY = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhdWQiOiIxIiwianRpIjoiYmU0NGRmMDAyMTA5NzBmNGE3NjNhOWM0Y2JlZWFhMGMwMzAzYTlkZjRkNDNmZjkyZjc2NmZiMGUyZmM2OWQ3ZGE0NjczNmFkZTFjYmNmYjAiLCJpYXQiOjE3ODk2Nzg0NjEuNzg0NzM4LCJuYmYiOjE3ODk2Nzg0NjEuNzg0NzQsImV4cCI6NDk0NTM1MjA2MS43NzY1MjgsInN1YiI6Ijc3MDA4MTE0Iiwic2NvcGVzIjpbInVzZXIucmVhZCIsInRhc2kucmVhZCIsInRhc2sud3JpdGUiXX0.mSMkmQcjm8Oucq7uZFUrIOiEzCQC8aONun43w_m9EU_I4R3e0MtnenZNpvGLM4QrmPTr3R5Eps9FR8KCkE45dD4ckZeYmZdvVMS11TIDPsZqaC4AUYByNcfNCzvw1rOC7BcIXid5FEO4g9KKvHX68_w0qrpaflQBpSBIgxCWM8iagtB8plt1juw5Zqy8agLwAdZ8nXjWs36HrJN6r58CcjmGH4QScZrxpl37XWldVLZYxFuTSTjSXfus_zice-0nTnK9wq0wwGmdi6fDXhaDTsUrl1U-topF14mzJjAHIXUG6_VhRn0z1BHT-mWvZwwhv64EhLBq7mWC2KQ8p2BP_NkvNJpLdxzK-Gme3rnIAejW6uiL497LRXZxOIrsR9noiKrmd3F7xvdiO5w8s4CuJQpJXUwKOo7eQ863NeIrOfZDen_Ii22-Gzab-yL_fytFhGpdJxbMdkZDywkOpABvGLAViHWjjKybTh8ieCizxBSmfmLb8yjVCROmZ-hzkjr1KI6jNlk-6YAMli4zl2PuifupG-IULluVb49i-1b2mJJCw6Y7jzymDT4ZVDNDhGe2kdnt8MQhOh8zxV6rgvhS5ZQO6bSAXBv5eM4j6vvg5AC60Snwi7vglBapr9X7fz9OpmhanSKD0GrDMZ9DQcXKT4sQgPVncajNmrXxtmjj_1Q"

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

            upload_task_id = job['result'][0]['id']
            upload_task = cloudconvert.Task.find(id=upload_task_id)
            
            with open(input_path, 'rb') as f:
                cloudconvert.Task.upload(upload_task=upload_task, file_object=f)

            job = cloudconvert.Job.wait(id=job['id'])
            export_task = [task for task in job['tasks'] if task['name'] == 'export-1'][0]
            file_url = export_task['result']['files'][0]['url']
            
            urllib.request.urlretrieve(file_url, output_path)

            return send_file(output_path, as_attachment=True, download_name='converted.pdf')
            
        except Exception as e:
            error_details = traceback.format_exc()
            return f'Conversion Error:\n{error_details}', 500
        finally:
            if os.path.exists(input_path):
                os.path.exists(input_path)
                if os.path.exists(output_path):
                    pass # Keep output until sent or let Flask handle cleanup

@app.route('/', methods=['GET'])
def index():
    return "CloudConvert Python Server is Running Successfully!"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

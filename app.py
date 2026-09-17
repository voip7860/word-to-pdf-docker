import os
import cloudconvert
from flask import Flask, request, send_file
from flask_cors import CORS
import traceback

app = Flask(__name__)
CORS(app)

# اپنی Cloudconvert کی API Key یہاں درج کریں
CLOUDCONVERT_API_KEY = os.environ.get('CLOUDCONVERT_API_KEY', 'YAHAPAPNIKEYDALEN')
cloudconvert.configure(api_key=CLOUDCONVERT_API_KEY, sandbox=False)

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
                # CloudConvert API کے ذریعے پرفیکٹ کنورژن
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

                # فائل اپ لوڈ کریں
                upload_task_id = job['result'][0]['id']
                upload_task = cloudconvert.Task.find(id=upload_task_id)
                
                with open(input_path, 'rb') as f:
                    cloudconvert.Task.upload(upload_task=upload_task, file_object=f)

                # جاب مکمل ہونے کا انتظار کریں اور ڈاؤن لوڈ کریں
                job = cloudconvert.Job.wait(id=job['id'])
                export_task = [task for task in job['tasks'] if task['name'] == 'export-1'][0]
                file_url = export_task['result']['files'][0]['url']
                
                # پی ڈی ایف ڈاؤن لوڈ کر کے یوزر کو بھیجیں
                import urllib.request
                urllib.request.urlretrieve(file_url, output_path)

                return send_file(output_path, as_attachment=True, download_name='converted.pdf')
                
            except Exception as e:
                tb = traceback.format_exc()
                return f'''
                <h3 style="color: red;">CloudConvert Error Details:</h3>
                <pre style="background: #f8f9fa; padding: 15px; border: 1px solid #ccc; white-space: pre-wrap;">{tb}</pre>
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
        <h2>Word to PDF Converter (CloudConvert API)</h2>
        <form method="post" enctype="multipart/form-data">
            <input type="file" name="file" accept=".docx" required style="padding: 10px; margin: 10px;">
            <br>
            <button type="submit" style="padding: 10px 20px; background: #28a745; color: white; border: none; cursor: pointer; border-radius: 5px;">Convert to PDF</button>
        </form>
    </body>
    </html>
    '''

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

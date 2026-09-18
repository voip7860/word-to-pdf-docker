import os
import requests
import traceback
import cloudconvert
from flask import Flask, request, send_file
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024

# Nayi CloudConvert API Key yahan set kar di gayi hai
CLOUDCONVERT_API_KEY = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhdWQiOiIxIiwianRpIjoiZDM2YzU4MGI3YWNhMTYxNjc0YzExYzYyMWUzMDFjN2Y0YTE3MTA4YTBiMjdkMTdkOTVmNDFiYmZjYWMxNGVjNzA2ZTIyNDcyYzVmMDViOWUiLCJpYXQiOjE3ODk3MTczMTIuODk5MjcyLCJuYmYiOjE3ODk3MTczMTIuODk5Mjc0LCJleHAiOjQ5NDUzOTA5MTIuODg5OTgzLCJzdWIiOiI3NzAwODExNCIsInNjb3BlcyI6WyJ1c2VyLnJlYWQiLCJ0YXNrLnJlYWQiLCJ0YXNrLndyaXRlIl19.owUABMIrA5LfMur67T6mskd5nkU6Iw9WFnjk50BIy4Wt9g9xoTglZWv9s7mEviJ-Z5VkrXU4Uc8f0nIYfsoLeGUYE5tQi_tTeIwBMuI793IaI4znoaQgqZU1xAN7XJAylU84_ITS83H_6BK3tuOCvQKDpUfckfdDsITRwTYqUogAefXoQNcxTELk96eQURa92iTqSUFQ59Vp2ifiJeE5lkTlFU8Os3LXXI66a0GTbBG1w_qTXSfZv_CnqnuYvKBHIipjSv4PE8qwjNM6X5utqPpFyBNfhws-wwkBXj-7E6si1M0p5VMtDlRWT5SNM5djYITsPrfFXBZxpI1slfglAX32LrpxCecfVZ06ZT54F6qL-cLAZcm5WlxFwz7tvinVtR9pdDmVQLvg2uuComJMa3peOm0dzsooA8oFi0WpwLu3RL9pzt_1YoFZ_uhK2osrUxgKGmSmnB8tqRj6BT04yiAlTEcL9NPxKtTx05YMPoz8MvZINbKiUITmIeWD-grXysCGnsLcOpamVtWro4_2KtAZviyqsfQ-K8Cx7CmBUffgG4ApXhn9WvcCnlwvukLKfXVos5dkTAh6kidbq_f_ju_OoLzQuyEpVurr-e-pk3weeyuB8x5mKEq1UNiOia_gS2vpNRkdQgpf4WHaYE4_h-KT7B8YNxnp0gKMNSPHCLk"

cloudconvert.configure(api_key=CLOUDCONVERT_API_KEY)

@app.route('/convert-word', methods=['POST'])
def convert_word_to_pdf():
    docx_path = None
    pdf_path = None
    try:
        if 'file' not in request.files:
            return 'No file uploaded', 400
        
        file = request.files['file']
        if file.filename == '':
            return 'No selected file', 400

        if not file.filename.lower().endswith('.docx'):
            return 'Only .docx files are allowed', 400

        docx_filename = "converted_document.docx"
        pdf_filename = "converted_document.pdf"
        
        docx_path = os.path.join("/tmp", docx_filename)
        pdf_path = os.path.join("/tmp", pdf_filename)
        
        file.save(docx_path)
        
        # CloudConvert Job Creation
        job = cloudconvert.Job.create(payload={
            "tasks": {
                "import-my-file": {
                    "operation": "import/upload"
                },
                "convert-my-file": {
                    "operation": "convert",
                    "input": "import-my-file",
                    "output_format": "pdf",
                    "engine": "office"
                },
                "export-my-file": {
                    "operation": "export/url",
                    "input": "convert-my-file"
                }
            }
        })
        
        if not job or 'tasks' not in job:
            return f"CloudConvert Error: Failed to create job. Response: {job}", 500
        
        # Upload docx file to CloudConvert
        upload_task = None
        for task in job['tasks']:
            if task.get('name') == 'import-my-file':
                upload_task = task
                break
                
        if not upload_task:
            return f"CloudConvert Error: 'import-my-file' task not found in job data: {job}", 500

        cloudconvert.Task.upload(file_name=docx_path, task=upload_task)
        
        # Wait for conversion job to complete
        job = cloudconvert.Job.wait(id=job['id'])
        
        if not job or 'tasks' not in job:
            return "CloudConvert Error: Job execution failed or returned invalid data.", 500

        # Get exported file URL and download PDF
        export_task = None
        for task in job['tasks']:
            if task.get('name') == 'export-my-file':
                export_task = task
                break

        if not export_task or 'result' not in export_task or 'files' not in export_task['result']:
            return "CloudConvert Error: Export task result not found.", 500

        file_info = export_task['result']['files'][0]
        file_url = file_info['url']
        
        # Download PDF using requests
        res = requests.get(file_url)
        with open(pdf_path, 'wb') as f:
            f.write(res.content)
        
        if os.path.exists(pdf_path):
            return send_file(pdf_path, as_attachment=True, download_name="converted.pdf")
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

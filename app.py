import os
import requests
import traceback
import cloudconvert
from flask import Flask, request, send_file
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024

# CloudConvert API Key
CLOUDCONVERT_API_KEY = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhdWQiOiIxIiwianRpIjoiNTBjMzYxNGM2M2FkM2RmYWUyMWIyNDI3YmI2MGZjMmU4MjNjOWUxZjQyOGUyNTNmNDE4NmY4MmE0ZTUwYWIxNmNhOWM4ZDczNGQ1OWMyZDgiLCJpYXQiOjE3ODk2NzAzNzEuMDUwMzA1LCJuYmYiOjE3ODk2NzAzNzEuMDUwMzA3LCJleHAiOjQ5NDUzNDM5NzEuMDQxNjc1LCJzdWIiOiI3NzAwODExNCIsInNjb3BlcyI6WyJ1c2VyLnJlYWQiLCJ0YXNrLnJlYWQiLCJ0YXNrLndyaXRlIl19.VC3egQDirvbmCSKWBqZSeNxuQxzakS49AtosMIYlb6FLc94_No4SZrs5i_VbC3kpwhHt1cpCI63ItrPEiuUsEzt_VdnsXSetyONSgFgzfikvPgjVyb3wC08dXqVEcpRiDUEpfCT0TQlbRSfCSTrwvOOI7JwuDH4Ow1JAk3F9wTsCBxRBbxStlfVUM0NkqodbvitiDaksQymGwAmUNT12wIIGWFe0vWQPz-SxEjGqrFxZDEg7heLMDWR4O6c2t2Zy1i140TB_3OSj_Lkf-XuoCsXkQc9DhlPscrsT0Efk9_qQy3SQhUCwlvMQskpezV-r7y1Na_LTNm-WUEVy96fwM20AJKZesztTszGx9KEEkSyebVzxisMHo971o7QZsliQc1AfntHS0hTCeFlB4IidvwzYrCCdMXOdDK2fiJ2ExgRxd311AZ13EuZl99v0gtEiVp8HnRIWLQ_E3YypP-tZKUE_FYsRhkxfII3PIl0Sue8qcFAt0UqyyoPbm1DIpLk5iwdTElDoZo1c9jpxo7I-FUrjxYwTQbwkARl8B-os0IZBkCGQmCfSzakK9p4usnRoCKY9mHs-p5idycUPP_P-As4YZxiE0dFkXe8L0j_AjbXXRKF8S19-GJ7kzg1o4C6TXZz_NSlnKk1YEB6APOZ0ONEW_Om7Pb_-DNF-R9uplPI"

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
        
        # چیک کریں کہ آیا جاب کامیابی سے بنی ہے یا نہیں
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

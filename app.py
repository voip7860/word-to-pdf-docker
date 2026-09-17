import os
import subprocess
import traceback
import pdfkit
import mammoth
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
        
        docx_path = f"temp_{safe_filename_base}.docx"
        output_dir = "/tmp"
        pdf_path = os.path.join(output_dir, f"{safe_filename_base}.pdf")
        
        file.save(docx_path)
        
        # Step 1: Convert Word (.docx) to clean HTML using mammoth
        with open(docx_path, "rb") as docx_file:
            result_mammoth = mammoth.convert_to_html(docx_file)
            html_content = result_mammoth.value
            
        # Add professional CSS styling to preserve table layout, borders, and margins exactly like Word
        styled_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 20px;
                    color: #000;
                    line-height: 1.4;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin-bottom: 20px;
                    table-layout: fixed;
                }}
                th, td {{
                    border: 1px solid #b0b0b0;
                    padding: 8px;
                    word-wrap: break-word;
                    vertical-align: top;
                }}
                img {{
                    max-width: 100%;
                    height: auto;
                }}
            </style>
        </head>
        <body>
            {html_content}
        </body>
        </html>
        """
        
        # Step 2: Convert HTML to PDF using pdfkit (wkhtmltopdf) for crisp, perfect multi-page alignment
        options = {
            'page-size': 'A4',
            'margin-top': '10mm',
            'margin-bottom': '10mm',
            'margin-left': '10mm',
            'margin-right': '10mm',
            'encoding': "UTF-8",
            'no-outline': None
        }
        
        pdfkit.from_string(styled_html, pdf_path, options=options)
        
        if os.path.exists(pdf_path):
            return send_file(pdf_path, as_attachment=True, download_name=f"{filename_base}.pdf")
        else:
            return "PDF generation failed", 500
            
    except Exception as e:
        error_details = traceback.format_exc()
        print(error_details)
        return f"Conversion Error: {str(e)}\n{error_details}", 500
        
    finally:
        if docx_path and os.path.exists(docx_path):
            try:
                os.remove(docx_path)
            except:
                pass

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

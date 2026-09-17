import os
import traceback
from docx import Document
from flask import Flask, request, send_file
from flask_cors import CORS
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

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
        
        # Read Word file using python-docx
        doc = Document(docx_path)
        
        # Setup ReportLab PDF document
        pdf_doc = SimpleDocTemplate(
            pdf_path,
            pagesize=A4,
            rightMargin=30, leftMargin=30,
            topMargin=30, bottomMargin=30
        )
        
        styles = getSampleStyleSheet()
        normal_style = styles['Normal']
        normal_style.fontSize = 10
        normal_style.leading = 12
        
        story = []
        
        # Extract paragraphs and tables from Word and build clean ReportLab flowables
        for element in doc.element.body:
            if element.tag.endswith('p'):
                # Paragraph
                para_text = "".join([node.text for node in element.iter() if node.text])
                if para_text.strip():
                    story.append(Paragraph(para_text, normal_style))
                    story.append(Spacer(1, 4))
            elif element.tag.endswith('tbl'):
                # Table handling
                for table in doc.tables:
                    table_data = []
                    for row in table.rows:
                        row_data = []
                        for cell in row.cells:
                            row_data.append(Paragraph(cell.text, normal_style))
                        table_data.append(row_data)
                    
                    if table_data:
                        # Create ReportLab table with exact borders
                        rl_table = Table(table_data)
                        rl_table.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.whitesmoke),
                            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.grey),
                            ('BOX', (0, 0), (-1, -1), 1, colors.grey),
                            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                            ('TOPPADDING', (0, 0), (-1, -1), 6),
                        ]))
                        story.append(rl_table)
                        story.append(Spacer(1, 10))
                    break # Process table once per loop match

        # Build PDF
        pdf_doc.build(story)
        
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

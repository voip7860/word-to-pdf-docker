# ہوم پیج کا روٹ (جہاں ورڈ فائل اپ لوڈ کرنے کا فارم آئے گا)
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'file' not in request.files:
            return 'کوئی فائل منتخب نہیں کی گئی', 400
        
        file = request.files['file']
        if file.filename == '':
            return 'فائل کا نام خالی ہے', 400
        
        if file:
            input_path = 'temp.docx'
            output_path = 'output.pdf'
            
            file.save(input_path)
            
            try:
                # گوگل ڈرائیو کنورژن فنکشن کال کریں
                convert_word_to_pdf_gdrive(input_path, output_path)
                return send_file(output_path, as_attachment=True, download_name='converted.pdf')
            except Exception as e:
                # اب اصل ایرر براؤزر پر سکرین پر نظر آ جائے گا
                import traceback
                error_details = traceback.format_exc()
                return f'''
                <h3 style="color: red;">کنورژن میں خرابی پیش آئی ہے:</h3>
                <pre style="background: #f8f9fa; padding: 15px; border: 1px solid #ccc;">{error_details}</pre>
                <br><a href="/">واپس جائیں</a>
                ''', 500
            finally:
                # لوکل عارضی فائلیں ڈیلیٹ کریں
                if os.path.exists(input_path):
                    os.remove(input_path)

    # سادہ سا HTML فارم جو یوزر کو دکھائے گا
    return '''
    <!doctype html>
    <html>
    <head><title>Word to PDF Converter</title></head>
    <body style="font-family: Arial; text-align: center; margin-top: 50px;">
        <h2>Word to PDF Converter (Google Drive API)</h2>
        <form method="post" enctype="multipart/form-data">
            <input type="file" name="file" accept=".docx" required style="padding: 10px; margin: 10px;">
            <br>
            <button type="submit" style="padding: 10px 20px; background: #007BFF; color: white; border: none; cursor: pointer;">Convert to PDF</button>
        </form>
    </body>
    </html>
    '''

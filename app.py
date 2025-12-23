from flask import Flask, request, send_file, after_this_request
from flask_cors import CORS
from pdf2docx import Converter
import os
import tempfile
import uuid

app = Flask(__name__)
CORS(app)

@app.route('/convert-pdf-to-word', methods=['POST'])
def convert_pdf_to_word():
    # Check file upload
    if 'file' not in request.files:
        return {"error": "No file uploaded"}, 400
    
    file = request.files['file']
    if file.filename == '':
        return {"error": "No file selected"}, 400

    # Temp locations
    unique_id = str(uuid.uuid4())
    temp_dir = tempfile.gettempdir()
    temp_pdf = os.path.join(temp_dir, f"{unique_id}.pdf")
    temp_docx = os.path.join(temp_dir, f"{unique_id}.docx")

    try:
        # Save PDF
        file.save(temp_pdf)

        # Convert
        cv = Converter(temp_pdf)
        cv.convert(temp_docx, start=0, end=None)
        cv.close()

        # Cleanup after sending
        @after_this_request
        def remove_files(response):
            try:
                if os.path.exists(temp_pdf): os.remove(temp_pdf)
                if os.path.exists(temp_docx): os.remove(temp_docx)
                print(f"Cleaned: {unique_id}")
            except Exception as e:
                print(f"Error cleaning: {e}")
            return response

        # Send File
        return send_file(
            temp_docx, 
            as_attachment=True, 
            download_name=file.filename.replace('.pdf', '.docx'),
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )

    except Exception as e:
        return {"error": str(e)}, 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

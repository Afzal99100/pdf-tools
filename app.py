from flask import Flask, request, send_file, after_this_request
from flask_cors import CORS
from pdf2docx import Converter
import os
import tempfile
import uuid
import gc

app = Flask(__name__)
CORS(app)

@app.route('/convert-pdf-to-word', methods=['POST'])
def convert_pdf_to_word():
    if 'file' not in request.files:
        return {"error": "No file uploaded"}, 400
    
    file = request.files['file']
    if file.filename == '':
        return {"error": "No file selected"}, 400

    unique_id = str(uuid.uuid4())
    temp_dir = tempfile.gettempdir()
    temp_pdf = os.path.join(temp_dir, f"{unique_id}.pdf")
    temp_docx = os.path.join(temp_dir, f"{unique_id}.docx")

    try:
        file.save(temp_pdf)

        # 1. Converter Initialize
        cv = Converter(temp_pdf)

        # 2. Table Detection Settings (Ye lines help karengi table dhoondne me)
        # Hum intersection aur lines ko scanning force kar rahe hain
        settings = {
            "detect_vertical": True,   # Khadi lines dhoondho
            "detect_horizontal": True, # Leti hui lines dhoondho
            "connected_border": True,  # Border jude hue hain kya?
            "snap_tolerance": 4,       # Thoda gap ho tab bhi jod do
            "join_tolerance": 4,
        }

        # 3. Conversion with Settings
        # multi_processing=False (RAM bachane ke liye zaroori hai)
        cv.convert(temp_docx, start=0, end=None, multi_processing=False, **settings)
        
        cv.close()
        
        # 4. Memory Cleanup
        del cv
        gc.collect() 

        @after_this_request
        def remove_files(response):
            try:
                if os.path.exists(temp_pdf): os.remove(temp_pdf)
                if os.path.exists(temp_docx): os.remove(temp_docx)
            except Exception as e:
                print(f"Error cleaning: {e}")
            return response

        return send_file(
            temp_docx, 
            as_attachment=True, 
            download_name=file.filename.replace('.pdf', '.docx'),
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )

    except Exception as e:
        gc.collect()
        # Agar RAM full hone se crash ho, to ye error dikhega
        print(f"Error: {e}")
        return {"error": "PDF Table too complex for free server. Try ConvertAPI."}, 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

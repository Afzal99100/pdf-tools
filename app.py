from flask import Flask, request, send_file, after_this_request
from flask_cors import CORS
from pdf2docx import Converter
import os
import tempfile
import uuid
import gc  # Garbage Collector (Memory safayi ke liye)

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

        # --- MEMORY SAVING TRICK ---
        # Hum converter ko initialize karenge
        cv = Converter(temp_pdf)
        
        # 'cpu_count' kam karke aur batch processing se crash rokne ki koshish
        # Hum multi-processing band kar rahe hain taaki RAM na bhare
        cv.convert(temp_docx, start=0, end=None, multi_processing=False)
        
        cv.close()
        
        # Memory Turant Saf karo
        del cv
        gc.collect() 
        # ---------------------------

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
        # Error aane par bhi safayi karo
        gc.collect()
        return {"error": "File too heavy for free server. Try smaller PDF."}, 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

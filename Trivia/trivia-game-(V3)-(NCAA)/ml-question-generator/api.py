from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import tempfile
from main import extract_text_from_pdf, generate_questions_json

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
DB_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "database"))

def safe_db_path(filename):
    if not filename:
        return None
    candidate = os.path.abspath(os.path.join(DB_DIR, filename))
    if not candidate.startswith(DB_DIR):
        return None
    return candidate

@app.route('/generate-questions', methods=['POST'])
def generate_questions():
    if 'pdf' not in request.files:
        return jsonify({'error': 'No PDF uploaded'}), 400
    pdf_file = request.files['pdf']
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
        pdf_file.save(tmp.name)
        text, pages_data = extract_text_from_pdf(tmp.name)
        questions = generate_questions_json(text, max_questions=40, section_size=5, pages_data=pages_data)
        os.unlink(tmp.name)
    return jsonify(questions)

@app.route('/list-db-pdfs', methods=['GET'])
def list_db_pdfs():
    if not os.path.isdir(DB_DIR):
        return jsonify([])
    files = [f for f in os.listdir(DB_DIR) if f.lower().endswith(".pdf")]
    return jsonify(sorted(files))

@app.route('/generate-questions-from-db', methods=['POST'])
def generate_questions_from_db():
    data = request.get_json(silent=True) or {}
    pdf_name = data.get("pdf_name")
    if not pdf_name:
        return jsonify({'error': 'No PDF selected'}), 400
    pdf_path = safe_db_path(pdf_name)
    if not pdf_path or not os.path.isfile(pdf_path):
        return jsonify({'error': 'PDF not found'}), 404
    text, pages_data = extract_text_from_pdf(pdf_path)
    questions = generate_questions_json(text, max_questions=40, section_size=5, pages_data=pages_data)
    return jsonify(questions)

if __name__ == '__main__':
    app.run(debug=True)

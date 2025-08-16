from flask import Flask, request, jsonify, render_template
from werkzeug.utils import secure_filename
import os
import docx2txt
import PyPDF2
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

# Configure Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files.get('document')
    if not file:
        return jsonify({'status': 'fail', 'error': 'No file uploaded'}), 400

    filename = secure_filename(file.filename)
    ext = filename.rsplit('.', 1)[-1].lower()

    try:
        if ext == 'txt':
            text = file.read().decode('utf-8')
        elif ext == 'pdf':
            reader = PyPDF2.PdfReader(file)
            text = ''.join(page.extract_text() or '' for page in reader.pages)
        elif ext == 'docx':
            text = docx2txt.process(file)
        else:
            return jsonify({'status': 'fail', 'error': 'Unsupported file format'}), 400

        return jsonify({'status': 'success', 'content': text})
    except Exception as e:
        return jsonify({'status': 'fail', 'error': str(e)}), 500

@app.route('/generate-paper', methods=['POST'])
def generate_paper():
    data = request.get_json()
    concept = data.get("concept", "").strip()

    if not concept:
        return jsonify({'error': 'No content provided'}), 400

    prompt = (
        f"You are an expert paper setter.\n"
        f"Based on the following content:\n\n\"\"\"\n{concept}\n\"\"\"\n\n"
        f"🎯 Generate a question paper:\n"
        f"- 5 questions of 2 marks\n"
        f"- 3 questions of 8 marks\n"
        f"- Don't include answers.\n"
        f"- Format output cleanly in markdown with headers like '**2 Marks Questions**', '**8 Marks Questions**'."
    )

    try:
        response = model.generate_content(prompt)
        return jsonify({'paper': response.text})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/ask', methods=['POST'])
def ask():
    data = request.get_json()
    question = data.get("question", "").strip()
    paper = data.get("doc", "").strip()

    if not question or not paper:
        return jsonify({'error': 'Missing question or paper content'}), 400

    prompt = (
        f"Here is a generated question paper:\n\n\"\"\"\n{paper}\n\"\"\"\n\n"
        f"User asks: \"{question}\"\n\n"
        f"Respond appropriately using markdown formatting.\n"
        f"If they reference a question number like 'Q6', extract and explain it.\n"
        f"Otherwise, answer normally."
    )

    try:
        response = model.generate_content(prompt)
        return jsonify({'answer': response.text})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)

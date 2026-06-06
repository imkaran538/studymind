"""
api/index.py
Flask entry point for the AI Study Assistant — Vercel-compatible.
"""

import os
import sys

# Allow imports from the project root (one level up from api/)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import google.generativeai as genai
from flask import Flask, render_template, request, jsonify, session
from werkzeug.utils import secure_filename

# ─── Gemini API — configured once here for the entire app ──────────────────────
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

from pdf_handler import allowed_file, save_pdf, extract_text, list_uploaded_pdfs, UPLOAD_FOLDER
from summarizer import summarize
from quiz_generator import generate_mcq, generate_short_answer, evaluate_answer
from planner import generate_plan, ask_doubt

# Templates are one level up from api/
template_dir = os.path.join(os.path.dirname(__file__), "..", "templates")
app = Flask(__name__, template_folder=template_dir)
app.secret_key = os.environ.get("FLASK_SECRET", "study-assistant-secret-2024")
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB max upload

# In-memory store for extracted PDF text (keyed by filename)
pdf_text_store: dict[str, str] = {}

# Ensure upload dir exists at startup
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ─── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html", pdfs=list_uploaded_pdfs())


# ── PDF Upload ──────────────────────────────────────────────────────────────────

@app.route("/upload", methods=["POST"])
def upload_pdf():
    if "pdf" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["pdf"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "Only PDF files are allowed"}), 400

    path = save_pdf(file)
    filename = secure_filename(file.filename)
    text = extract_text(path)

    if not text.strip():
        return jsonify({"error": "Could not extract text from this PDF (it may be scanned/image-based)."}), 400

    pdf_text_store[filename] = text
    return jsonify({"message": f"✅ '{filename}' uploaded successfully.", "filename": filename, "char_count": len(text)})


@app.route("/load_pdf", methods=["POST"])
def load_pdf():
    """Load a previously uploaded PDF into the active session."""
    filename = request.json.get("filename")
    if not filename:
        return jsonify({"error": "No filename provided"}), 400

    if filename not in pdf_text_store:
        path = os.path.join(UPLOAD_FOLDER, filename)
        if not os.path.exists(path):
            return jsonify({"error": "File not found on disk"}), 404
        text = extract_text(path)
        pdf_text_store[filename] = text

    session["active_pdf"] = filename
    return jsonify({"message": f"📄 '{filename}' loaded.", "char_count": len(pdf_text_store[filename])})


# ── Summarizer ─────────────────────────────────────────────────────────────────

@app.route("/summarize", methods=["POST"])
def summarize_pdf():
    data = request.json or {}
    filename = data.get("filename") or session.get("active_pdf")
    style = data.get("style", "detailed")

    text = _get_text(filename)
    if isinstance(text, tuple):
        return text

    result = summarize(text, style=style)
    return jsonify({"summary": result, "style": style})


# ── Quiz Generator ─────────────────────────────────────────────────────────────

@app.route("/quiz/mcq", methods=["POST"])
def quiz_mcq():
    data = request.json or {}
    filename = data.get("filename") or session.get("active_pdf")
    num = int(data.get("num_questions", 5))

    text = _get_text(filename)
    if isinstance(text, tuple):
        return text

    questions = generate_mcq(text, num_questions=num)
    return jsonify({"questions": questions})


@app.route("/quiz/short", methods=["POST"])
def quiz_short():
    data = request.json or {}
    filename = data.get("filename") or session.get("active_pdf")
    num = int(data.get("num_questions", 5))

    text = _get_text(filename)
    if isinstance(text, tuple):
        return text

    questions = generate_short_answer(text, num_questions=num)
    return jsonify({"questions": questions})


@app.route("/quiz/evaluate", methods=["POST"])
def quiz_evaluate():
    data = request.json or {}
    question = data.get("question", "")
    user_answer = data.get("user_answer", "")
    sample_answer = data.get("sample_answer", "")

    if not question or not user_answer:
        return jsonify({"error": "Question and user_answer are required"}), 400

    result = evaluate_answer(question, user_answer, sample_answer)
    return jsonify(result)


# ── Study Planner ──────────────────────────────────────────────────────────────

@app.route("/plan", methods=["POST"])
def study_plan():
    data = request.json or {}
    topics = data.get("topics", [])
    days = int(data.get("days", 7))
    hours = float(data.get("hours_per_day", 3))
    exam_name = data.get("exam_name", "Exam")

    if not topics:
        return jsonify({"error": "Please provide at least one topic"}), 400

    plan = generate_plan(topics, days, hours, exam_name)
    return jsonify({"plan": plan})


# ── Doubt Solver ───────────────────────────────────────────────────────────────

@app.route("/ask", methods=["POST"])
def ask():
    data = request.json or {}
    question = data.get("question", "").strip()
    filename = data.get("filename") or session.get("active_pdf")

    if not question:
        return jsonify({"error": "Please enter a question"}), 400

    context = ""
    if filename:
        text = _get_text(filename)
        if not isinstance(text, tuple):
            context = text

    answer = ask_doubt(context, question)
    return jsonify({"answer": answer})


# ── Helpers ────────────────────────────────────────────────────────────────────

def _get_text(filename: str | None):
    """Return extracted text for filename, or a JSON error tuple."""
    if not filename:
        return jsonify({"error": "No PDF loaded. Please upload or select a PDF first."}), 400
    if filename not in pdf_text_store:
        path = os.path.join(UPLOAD_FOLDER, filename)
        if not os.path.exists(path):
            return jsonify({"error": f"'{filename}' not found. Please upload it first."}), 404
        pdf_text_store[filename] = extract_text(path)
    return pdf_text_store[filename]


# ── Local dev entrypoint ───────────────────────────────────────────────────────
if __name__ == "__main__":
    print("🎓 Study Assistant running at http://localhost:5000")
    app.run(debug=True, port=5000)

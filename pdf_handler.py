"""
pdf_handler.py
Handles PDF upload, text extraction, and chunking.
"""

import os
import PyPDF2
from werkzeug.utils import secure_filename

# Use /tmp for Vercel (read-only filesystem except /tmp)
UPLOAD_FOLDER = "/tmp/uploads"
ALLOWED_EXTENSIONS = {"pdf"}
MAX_CHUNK_CHARS = 4000  # safe for Gemini context windows


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def save_pdf(file_storage) -> str:
    """Save an uploaded FileStorage object and return the saved path."""
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    filename = secure_filename(file_storage.filename)
    path = os.path.join(UPLOAD_FOLDER, filename)
    file_storage.save(path)
    return path


def extract_text(pdf_path: str) -> str:
    """Extract all text from a PDF file."""
    text_parts = []
    with open(pdf_path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text.strip())
    return "\n\n".join(text_parts)


def chunk_text(text: str, chunk_size: int = MAX_CHUNK_CHARS) -> list[str]:
    """Split text into chunks without breaking sentences mid-way."""
    chunks = []
    while len(text) > chunk_size:
        split_at = text.rfind(". ", 0, chunk_size)
        if split_at == -1:
            split_at = chunk_size
        chunks.append(text[:split_at + 1].strip())
        text = text[split_at + 1:].strip()
    if text:
        chunks.append(text)
    return chunks


def list_uploaded_pdfs() -> list[str]:
    """Return filenames of all uploaded PDFs."""
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    return [f for f in os.listdir(UPLOAD_FOLDER) if f.lower().endswith(".pdf")]

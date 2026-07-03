"""
pdf_parser.py - Extracts raw text from PDF and DOCX resume files.
Falls back from PyMuPDF to pdfplumber automatically.
"""

import os


def extract_text_from_pdf(file_path: str) -> str:
    """
    Attempts to extract text using PyMuPDF (fitz) first.
    Falls back to pdfplumber if PyMuPDF fails (e.g., encrypted or complex PDFs).
    """
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(file_path)
        text = ""
        for page in doc:
            text += page.get_text("text")
        doc.close()
        if text.strip():
            return text
    except Exception:
        pass  # Fall through to pdfplumber

    try:
        import pdfplumber
        with pdfplumber.open(file_path) as pdf:
            text = ""
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text
    except Exception as e:
        raise RuntimeError(f"Failed to parse PDF '{file_path}': {e}")


def extract_text_from_bytes(file_bytes: bytes, filename: str) -> str:
    """
    Accepts raw bytes (from Streamlit file uploader) and writes to a temp file,
    then routes to the correct extractor based on file extension.
    """
    import tempfile

    ext = os.path.splitext(filename)[-1].lower()
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    try:
        if ext == ".pdf":
            return extract_text_from_pdf(tmp_path)
        else:
            raise ValueError(f"Unsupported file type: {ext}. Only PDF is currently supported.")
    finally:
        os.unlink(tmp_path)  # Always clean up temp file

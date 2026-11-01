"""Input Module: accepts a legal document from the keyboard, a .txt file or a .pdf file."""
from pathlib import Path

from modules.extraction_module import extract_text

SUPPORTED = (".txt", ".pdf")


def read_typed_text(text: str) -> dict:
    """Legal text typed or pasted by the user."""
    if not text or not text.strip():
        raise ValueError("Please enter or upload a legal document first.")
    return {"name": "Typed text", "text": text, "pages": None}


def read_upload(data: bytes, filename: str) -> dict:
    """File content already in memory (e.g. a Streamlit upload)."""
    if not filename.lower().endswith(SUPPORTED):
        raise ValueError("Unsupported file type. Please use a .txt or .pdf file.")
    text, pages = extract_text(data, filename)
    return {"name": filename, "text": text, "pages": pages}


def read_path(path: str) -> dict:
    """File on disk (used by the command-line menu)."""
    p = Path(path.strip().strip('"'))
    if not p.is_file():
        raise ValueError(f"File not found: {p}")
    return read_upload(p.read_bytes(), p.name)

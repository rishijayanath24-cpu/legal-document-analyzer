"""Extraction Module: pulls raw text out of .txt / .pdf files and describes the document."""
import io
import re

from pypdf import PdfReader

# (label, keywords) - checked against the title first, then the whole document
DOC_TYPES = [
    ("Non-Disclosure Agreement", ["non-disclosure", "nondisclosure", "nda"]),
    ("Employment Agreement", ["employment", "employee"]),
    ("Service Agreement", ["service agreement", "services agreement", "master services"]),
    ("Rental Agreement", ["rental", "lease", "tenant", "landlord"]),
    ("Loan Agreement", ["loan", "borrower", "lender"]),
    ("Sales Agreement", ["sales agreement", "sale of goods", "purchase agreement"]),
    ("Privacy Policy", ["privacy policy"]),
    ("Terms and Conditions", ["terms and conditions", "terms of service"]),
]


def extract_text(data: bytes, filename: str) -> tuple[str, int | None]:
    """Return (text, page_count). page_count is None for plain text."""
    if filename.lower().endswith(".pdf"):
        reader = PdfReader(io.BytesIO(data))
        text = "\n\n".join((page.extract_text() or "") for page in reader.pages)
        if not text.strip():
            raise ValueError("No text could be extracted from this PDF (it may be a scanned image).")
        return text, len(reader.pages)
    return data.decode("utf-8", errors="replace"), None


def guess_title(text: str) -> str:
    for line in text.splitlines():
        if line.strip():
            return line.strip()[:120]
    return "Untitled"


def guess_doc_type(text: str) -> str:
    title = guess_title(text).lower()
    lowered = text.lower()
    for scope in (title, lowered):
        for label, words in DOC_TYPES:
            if any(re.search(rf"\b{re.escape(w)}\b", scope) for w in words):
                return label
    return "Legal document (type not detected)"


def document_info(text: str, pages: int | None) -> dict:
    return {
        "Title": guess_title(text),
        "Document Type (detected)": guess_doc_type(text),
        "Pages": pages if pages is not None else "n/a (text input)",
        "Characters": len(text),
        "Words": len(text.split()),
        "Lines": len(text.splitlines()),
    }

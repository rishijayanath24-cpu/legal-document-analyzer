"""Preprocessing Module: clean and normalise the text, find sections, split into chunks."""
import re
import unicodedata

_REPLACEMENTS = {
    "‘": "'", "’": "'", "“": '"', "”": '"',
    "–": "-", "—": "-", "•": "-", " ": " ",
}
_PAGE_NOISE = re.compile(r"^\s*(page\s+\d+(\s+of\s+\d+)?|-\s*\d+\s*-)\s*$", re.IGNORECASE)
_HEADING = re.compile(
    r"^\s*(?:\d+(?:\.\d+)*[.)]?\s+)?[A-Z][A-Z0-9 ,&/'-]{3,70}$"      # 1. SCOPE OF SERVICES
    r"|^\s*\d+[.)]\s+[A-Z][A-Za-z ,&/'-]{2,60}$"                       # 1. Scope of services
)
_MONTHS = "jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec"
_DATE = re.compile(
    rf"\b\d{{1,2}}[-/.]\d{{1,2}}[-/.]\d{{2,4}}\b"
    rf"|\b\d{{4}}-\d{{2}}-\d{{2}}\b"
    rf"|\b\d{{1,2}}(?:st|nd|rd|th)?\s+(?:{_MONTHS})[a-z]*\.?,?\s+\d{{4}}\b"
    rf"|\b(?:{_MONTHS})[a-z]*\.?\s+\d{{1,2}}(?:st|nd|rd|th)?,?\s+\d{{4}}\b",
    re.IGNORECASE,
)
_AMOUNT = re.compile(r"(?:₹|Rs\.?|INR|\$|USD)\s?\d[\d,]*(?:\.\d+)?(?:\s?(?:per|/)\s?\w+)?", re.IGNORECASE)


def clean_text(raw: str) -> str:
    """Remove unwanted characters and unnecessary whitespace; normalise punctuation."""
    text = unicodedata.normalize("NFKC", raw)
    for old, new in _REPLACEMENTS.items():
        text = text.replace(old, new)
    text = re.sub(r"[​-‏⁠﻿]", "", text)                 # zero-width characters
    text = re.sub(r"[^\S\n]*[\x00-\x08\x0b\x0c\x0e-\x1f\x7f][^\S\n]*", " ", text)  # control chars
    lines = [re.sub(r"[ \t]+", " ", ln).strip() for ln in text.splitlines()]
    lines = [ln for ln in lines if not _PAGE_NOISE.match(ln)]               # "Page 1 of 3"
    text = "\n".join(lines)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def identify_sections(text: str) -> list[dict]:
    """Split cleaned text into sections at numbered / upper-case headings."""
    sections, heading, buf = [], "Preamble", []
    for line in text.splitlines():
        if line.strip() and _HEADING.match(line) and not line.rstrip().endswith("."):
            if "".join(buf).strip():
                sections.append({"heading": heading, "text": "\n".join(buf).strip()})
            heading, buf = line.strip(), [line.strip()]
        else:
            buf.append(line)
    if "".join(buf).strip():
        sections.append({"heading": heading, "text": "\n".join(buf).strip()})
    return sections


def _split_long(block: str, limit: int) -> list[str]:
    """Split an oversized block on paragraph, then sentence, boundaries."""
    parts, cur = [], ""
    for piece in re.split(r"(?<=\n\n)|(?<=[.;])\s+", block):
        if cur and len(cur) + len(piece) > limit:
            parts.append(cur.strip())
            cur = ""
        cur += piece + " "
    if cur.strip():
        parts.append(cur.strip())
    return parts


def chunk_sections(sections: list[dict], max_chars: int = 4500) -> list[str]:
    """Group whole sections into chunks of at most max_chars (long sections are split)."""
    chunks, cur = [], ""
    for sec in sections:
        pieces = [sec["text"]] if len(sec["text"]) <= max_chars else _split_long(sec["text"], max_chars)
        for piece in pieces:
            if cur and len(cur) + len(piece) + 2 > max_chars:
                chunks.append(cur.strip())
                cur = ""
            cur += piece + "\n\n"
    if cur.strip():
        chunks.append(cur.strip())
    return chunks


def detect_hints(text: str) -> dict:
    """Dates and money amounts found with regular expressions (passed to the prompt as hints)."""
    def uniq(items):
        return list(dict.fromkeys(i.strip() for i in items))
    return {"dates": uniq(_DATE.findall(text)), "amounts": uniq(_AMOUNT.findall(text))}


def preprocess(raw: str, max_chars: int = 4500) -> dict:
    cleaned = clean_text(raw)
    sections = identify_sections(cleaned)
    return {
        "cleaned": cleaned,
        "sections": sections,
        "chunks": chunk_sections(sections, max_chars),
        "hints": detect_hints(cleaned),
    }

"""Summary Module: runs the LLM (chunk by chunk when needed) and formats the structured report."""
import re

from modules.llm import ask_ollama
from modules.prompt_module import (
    ANALYSIS_TYPES, LIST_FIELDS, NOT_FOUND, build_chunk_prompt, build_prompt, build_summary_prompt,
)

_FIRST_VALUE_FIELDS = {"Document Type", "Parties", "Purpose", "Duration"}   # same in every chunk
_EMPTY = re.compile(r"(?i)(n/?a|none|not (mentioned|specified|available|provided|stated)"
                    r"( in the (document|text|part|agreement))?\.?)")


def _parse(raw: str, fields: list[str]) -> dict[str, str]:
    """Split the model answer at its headings; tolerate **bold**, numbering and case differences."""
    names = "|".join(re.escape(f) for f in fields)
    pattern = re.compile(rf"^\W*(?:\d+[.)]\s*)?\**\s*({names})\s*\**\s*:\s*\**\s*(.*)$", re.IGNORECASE)
    canonical = {f.lower(): f for f in fields}
    out, current = {}, None
    for line in raw.splitlines():
        m = pattern.match(line)
        if m:
            current = canonical[m.group(1).lower()]
            out[current] = [m.group(2).strip()] if m.group(2).strip() else []
        elif current is not None:
            out[current].append(line.rstrip())
    return {k: "\n".join(v).strip() for k, v in out.items()}


def _tidy(field: str, value: str) -> str:
    """Normalise one field; anything the model marks as missing becomes NOT_FOUND."""
    value = re.sub(r"\*\*", "", value).strip()
    if not value or _EMPTY.fullmatch(value):
        return NOT_FOUND
    bullet = re.compile(r"^(?:[-*•]\s*)+")
    if field in LIST_FIELDS:
        items = [bullet.sub("", ln).strip() for ln in value.splitlines() if ln.strip()]
        if len(items) == 1 and ";" in items[0]:
            items = [s.strip() for s in items[0].split(";") if s.strip()]
        items = [i for i in items if not _EMPTY.fullmatch(i)]
        return "\n".join(f"• {i}" for i in items) if items else NOT_FOUND
    return " ".join(bullet.sub("", ln).strip() for ln in value.splitlines() if ln.strip())


def _dedupe(values: list[str]) -> list[str]:
    """Drop repeats (case-insensitive) and values already contained in a longer value."""
    out = []
    for v in dict.fromkeys(values):
        if not any(v.lower() in o.lower() for o in values if len(o) > len(v)):
            out.append(v)
    return out


def _merge_partials(partials: list[str], fields: list[str]) -> dict[str, str]:
    """Combine per-chunk answers field by field in code (more reliable than asking the model)."""
    parsed = [_parse(p, fields) for p in partials]
    merged = {}
    for f in fields:
        values = [v for v in (_tidy(f, p.get(f, "")) for p in parsed) if v != NOT_FOUND]
        if not values:
            merged[f] = NOT_FOUND
        elif f in LIST_FIELDS:
            merged[f] = "\n".join(_dedupe([ln for v in values for ln in v.splitlines()]))
        elif f in _FIRST_VALUE_FIELDS or f == "Summary":
            merged[f] = values[0]
        else:
            merged[f] = " ".join(_dedupe(values))
    return merged


def analyze(chunks: list[str], analysis_type: str, hints: dict | None, llm=ask_ollama) -> dict:
    """Return the prompt(s) used and the model answer(s); the last response is the final analysis.

    One chunk -> a single prompt. Several chunks -> one prompt per chunk, a field-by-field merge,
    and a final prompt that writes the summary from the merged notes.
    """
    if len(chunks) == 1:
        prompt = build_prompt(chunks[0], analysis_type, hints)
        return {"prompts": [prompt], "responses": [llm(prompt)]}
    fields = ANALYSIS_TYPES[analysis_type]
    prompts, partials = [], []
    for i, chunk in enumerate(chunks, 1):
        prompts.append(build_chunk_prompt(chunk, i, len(chunks), analysis_type, hints))
        partials.append(llm(prompts[-1]))
    merged = _merge_partials(partials, fields)
    if "Summary" in fields:
        notes = "\n".join(f"{f}: {v}" for f, v in merged.items() if f != "Summary")
        prompts.append(build_summary_prompt(notes))
        merged["Summary"] = llm(prompts[-1])
    final = "\n".join(f"{f}: {merged[f]}" for f in fields)
    return {"prompts": prompts, "responses": partials + [final]}


def format_report(raw: str, analysis_type: str) -> str:
    """Rebuild the model answer in the fixed LEGAL DOCUMENT ANALYSIS layout."""
    fields = ANALYSIS_TYPES[analysis_type]
    parsed = _parse(raw, fields)
    title = "LEGAL DOCUMENT SUMMARY" if analysis_type == "Summary" else "LEGAL DOCUMENT ANALYSIS"
    body = "\n\n".join(f"{f}:\n{_tidy(f, parsed.get(f, ''))}" for f in fields)
    return f"{title}\n{'-' * 32}\n\n{body}\n"

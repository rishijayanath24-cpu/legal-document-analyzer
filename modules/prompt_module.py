"""Prompt Module: builds the instructions sent to the LLM (single-pass, per-chunk and merge prompts)."""

NOT_FOUND = "Not mentioned in the document."

FIELDS = [
    "Document Type", "Parties", "Purpose", "Duration", "Key Obligations", "Payment Terms",
    "Termination Conditions", "Important Dates", "Key Clauses", "Summary",
]
LIST_FIELDS = {"Key Obligations", "Important Dates", "Key Clauses"}

# Analysis Type (input parameter) -> fields requested
ANALYSIS_TYPES = {
    "Complete": FIELDS,
    "Summary": ["Document Type", "Parties", "Purpose", "Duration", "Summary"],
    "Clause": ["Document Type", "Parties", "Payment Terms", "Termination Conditions", "Key Clauses"],
    "Obligation": ["Document Type", "Parties", "Key Obligations", "Payment Terms", "Important Dates"],
}

_FIELD_HELP = {
    "Document Type": "kind of agreement, e.g. Service Agreement",
    "Parties": "who is entering the agreement",
    "Purpose": "one sentence on what the agreement is for",
    "Duration": "term of the agreement",
    "Key Obligations": "bullet list of what each party must do",
    "Payment Terms": "amounts, schedule and late-payment rules",
    "Termination Conditions": "how and when the agreement can end",
    "Important Dates": "bullet list: label and date",
    "Key Clauses": "bullet list of the main clauses present (e.g. Confidentiality, Liability, "
                   "Intellectual Property, Dispute Resolution, Governing Law)",
    "Summary": "2-4 plain-English sentences",
}

_ROLE = "You are a legal document analysis assistant."
_RULES = (
    "Rules:\n"
    "- Use only information present in the document. Do not invent information.\n"
    f'- If information is not available, write "{NOT_FOUND}"\n'
    '- Use short bullet points starting with "- " for list fields.\n'
    "- Keep each answer concise. Do not add any other headings or commentary."
)


def _format_spec(fields: list[str]) -> str:
    return "\n".join(f"{f}: ({_FIELD_HELP[f]})" for f in fields)


def _hint_block(hints: dict | None) -> str:
    if not hints or not (hints["dates"] or hints["amounts"]):
        return ""
    lines = ["Hints found by software (check them against the document before using):"]
    if hints["dates"]:
        lines.append("- Dates: " + "; ".join(hints["dates"]))
    if hints["amounts"]:
        lines.append("- Amounts: " + "; ".join(hints["amounts"]))
    return "\n".join(lines) + "\n\n"


def build_prompt(text: str, analysis_type: str = "Complete", hints: dict | None = None) -> str:
    fields = ANALYSIS_TYPES[analysis_type]
    return (
        f"{_ROLE}\n\n"
        "Task: Analyze the legal document below. Reply with exactly these headings, each on its "
        f"own line followed by a colon, in this order:\n{_format_spec(fields)}\n\n"
        f"{_RULES}\n\n{_hint_block(hints)}"
        f'DOCUMENT:\n"""\n{text}\n"""'
    )


def build_chunk_prompt(chunk: str, index: int, total: int, analysis_type: str, hints: dict | None) -> str:
    fields = ANALYSIS_TYPES[analysis_type]
    return (
        f"{_ROLE}\n\n"
        f"Task: The text below is part {index} of {total} of one legal document. Analyze this part "
        f"only. Reply with exactly these headings, each on its own line followed by a colon:\n"
        f"{_format_spec(fields)}\n\n{_RULES}\n"
        f'- For a field this part does not cover, write "{NOT_FOUND}"\n\n{_hint_block(hints)}'
        f'PART {index} OF {total}:\n"""\n{chunk}\n"""'
    )


def build_summary_prompt(notes: str) -> str:
    """Final step for long documents: write the summary from the merged per-chunk notes."""
    return (
        f"{_ROLE}\n\n"
        "Task: Below are notes extracted from one legal document. Write a 2-4 sentence plain-English "
        "summary of the agreement using only these notes. Do not invent information. "
        "Reply with the summary text only.\n\n"
        f'NOTES:\n"""\n{notes}\n"""'
    )

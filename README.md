# Automated Legal Document Analyzer using GPT-4

Course: 24CS2506 – Building Applications using GPT-4 | Experiment 5

Reads a legal contract (typed text, `.txt` or `.pdf`), cleans it, and asks a language model for a
structured analysis: document type, parties, purpose, duration, obligations, payment terms,
termination conditions, important dates, key clauses and a short summary. The report is saved to
`outputs/legal_analysis.txt`. Everything runs locally through Ollama – no cloud API needed.

## Workflow
```
Legal document → Input → Extraction → Preprocessing (clean, sections, chunks, date/amount hints)
              → Prompt → LLM (Ollama) → Summary / structured report → Save
```
Long documents are split into chunks, each chunk is analysed, the answers are merged field by
field in code, and the model writes the final summary from the merged notes.

The prompt tells the model to use only information in the document and to answer
"Not mentioned in the document." when something is missing.

## Setup
```bash
ollama pull qwen2.5:3b
ollama serve                      # keep running
pip install -r requirements.txt
streamlit run app.py              # web UI
python main.py                    # numbered command-line menu (Upload / Analyze / Summary / Save / Exit)
```
Set `LEGAL_MODEL` to use a different Ollama model (default `qwen2.5:3b`).
Try it with `samples/service_agreement.txt`.

## Project structure
```
├── app.py                    # Streamlit UI
├── main.py                   # command-line menu
├── modules/
│   ├── input_module.py       # keyboard / .txt / .pdf input
│   ├── extraction_module.py  # text extraction + document information
│   ├── preprocessing_module.py  # cleaning, sections, chunks, date/amount hints
│   ├── prompt_module.py      # prompts (single, per-chunk, summary)
│   ├── summary_module.py     # LLM calls, merge, report formatting
│   ├── save_module.py        # writes outputs/legal_analysis.txt
│   └── llm.py                # Ollama API wrapper
├── samples/service_agreement.txt
├── outputs/                  # saved reports
└── screenshots/              # output screenshots
```

## Tech stack
Python · Ollama (qwen2.5:3b) · Streamlit · Pandas · pypdf

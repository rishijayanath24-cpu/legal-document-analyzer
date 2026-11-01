"""Automated Legal Document Analyzer - Streamlit app (local LLM via Ollama).

Run with:  streamlit run app.py
"""
from pathlib import Path

import pandas as pd
import streamlit as st

from modules.extraction_module import document_info
from modules.input_module import read_typed_text, read_upload
from modules.llm import MODEL_NAME, OllamaError
from modules.preprocessing_module import preprocess
from modules.prompt_module import ANALYSIS_TYPES
from modules.save_module import save_report
from modules.summary_module import analyze, format_report

st.set_page_config(page_title="Legal Document Analyzer", page_icon="⚖️", layout="wide")
SAMPLE = Path("samples/service_agreement.txt")


def load_sample():
    st.session_state.doc_text = SAMPLE.read_text(encoding="utf-8")


def set_document(doc: dict):
    st.session_state.doc = doc
    st.session_state.result = None
    st.session_state.report = None
    st.session_state.saved = None


for key in ("doc", "result", "report", "saved"):
    st.session_state.setdefault(key, None)
st.session_state.setdefault("doc_text", "")


def show(label: str, text: str, height: int = 260):
    st.text_area(label, text, height=height, disabled=True)


# ---------------- Home screen ----------------
with st.sidebar:
    st.header("Menu")
    st.markdown("1. Upload / Enter Legal Document\n2. Analyze Document\n3. Generate Summary\n"
                "4. Save Report")
    if st.button("5. Exit"):
        st.session_state.clear()
        st.success("Application closed. You can close this tab.")
        st.stop()

st.title("⚖️ Automated Legal Document Analyzer")
st.caption(f"Local, private and cloud-free · LLM: {MODEL_NAME} via Ollama")
st.markdown(
    "Enter or upload a legal contract. The analyzer extracts and cleans the text, builds a prompt, "
    "asks the language model for a structured analysis (parties, obligations, payment, termination, "
    "dates and key clauses) and saves the report."
)

# ---------------- 1. Upload / Enter ----------------
st.header("1. Upload / Enter Legal Document")
tab_text, tab_file = st.tabs(["Enter text", "Upload .txt / .pdf"])
with tab_text:
    st.button("Load sample service agreement", on_click=load_sample)
    st.text_area("Legal document text", key="doc_text", height=240,
                 placeholder="Paste a contract here...")
    if st.button("Load document", key="load_text"):
        try:
            set_document(read_typed_text(st.session_state.doc_text))
        except ValueError as err:
            st.warning(str(err))
with tab_file:
    upload = st.file_uploader("Choose a file", type=["txt", "pdf"])
    if st.button("Load file", key="load_file"):
        if upload is None:
            st.warning("Please choose a .txt or .pdf file first.")
        else:
            try:
                set_document(read_upload(upload.getvalue(), upload.name))
            except ValueError as err:
                st.warning(str(err))

doc = st.session_state.doc
if doc:
    st.subheader("Document Information")
    info = document_info(doc["text"], doc["pages"])
    st.dataframe(pd.DataFrame({"Field": list(info), "Value": [str(v) for v in info.values()]}),
                 hide_index=True, use_container_width=True)

    # ---------------- 2. Analyze ----------------
    st.header("2. Analyze Document")
    a1, a2 = st.columns([1, 3])
    analysis_type = a1.selectbox("Analysis type", list(ANALYSIS_TYPES))
    if a1.button("Analyze Document"):
        pre = preprocess(doc["text"])
        try:
            with st.spinner(f"Analyzing with {MODEL_NAME} ({len(pre['chunks'])} chunk(s))..."):
                run = analyze(pre["chunks"], analysis_type, pre["hints"])
            st.session_state.result = {"pre": pre, "run": run, "type": analysis_type}
            st.session_state.report = None
            st.session_state.saved = None
        except OllamaError as err:
            st.error(str(err))

    result = st.session_state.result
    if result:
        pre, run = result["pre"], result["run"]
        st.subheader("Document Text Extraction")
        show("Extracted text", doc["text"])

        st.subheader("Preprocessed Text")
        show("Cleaned and normalised text", pre["cleaned"])
        st.dataframe(pd.DataFrame({
            "Section": range(1, len(pre["sections"]) + 1),
            "Heading": [s["heading"] for s in pre["sections"]],
            "Characters": [len(s["text"]) for s in pre["sections"]]}),
            hide_index=True, use_container_width=True, height=(len(pre["sections"]) + 1) * 35 + 3)
        st.caption(f"{len(pre['sections'])} sections · {len(pre['chunks'])} chunk(s) · "
                   f"dates detected: {', '.join(pre['hints']['dates']) or 'none'} · "
                   f"amounts detected: {', '.join(pre['hints']['amounts']) or 'none'}")

        st.subheader("Prompt Generation")
        show("Prompt sent to the model",
             "\n\n=====\n\n".join(run["prompts"]), height=320)

        st.subheader("GPT-4 Response")
        show("Raw model response", "\n\n=====\n\n".join(run["responses"]), height=320)

        # ---------------- 3. Generate Summary ----------------
        st.header("3. Generate Summary")
        if st.button("Generate Summary"):
            st.session_state.report = format_report(run["responses"][-1], result["type"])
        if st.session_state.report:
            st.code(st.session_state.report, language=None, wrap_lines=True)

            # ---------------- 4. Save Report ----------------
            st.header("4. Save Report")
            if st.button("Save Report"):
                st.session_state.saved = save_report(st.session_state.report, doc["name"])
            if st.session_state.saved:
                st.success(f"Report saved to {Path(st.session_state.saved).as_posix()}")

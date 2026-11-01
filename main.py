"""Automated Legal Document Analyzer - command-line menu (same modules as the Streamlit app).

Run with:  python main.py
"""
from modules.extraction_module import document_info
from modules.input_module import read_path, read_typed_text
from modules.llm import MODEL_NAME, OllamaError
from modules.preprocessing_module import preprocess
from modules.prompt_module import ANALYSIS_TYPES
from modules.save_module import save_report
from modules.summary_module import analyze, format_report

MENU = """
AUTOMATED LEGAL DOCUMENT ANALYZER
---------------------------------
1. Upload / Enter Legal Document
2. Analyze Document
3. Generate Summary
4. Save Report
5. Exit
"""


def load_document():
    print("Enter a .txt/.pdf file path, or press Enter to type the text yourself.")
    path = input("File path: ").strip()
    if path:
        return read_path(path)
    print("Type or paste the document. Finish with a line containing only END.")
    lines = []
    while (line := input()) != "END":
        lines.append(line)
    return read_typed_text("\n".join(lines))


def main():
    doc = run = report = None
    analysis_type = "Complete"
    while True:
        print(MENU)
        choice = input("Choose an option (1-5): ").strip()
        try:
            if choice == "1":
                doc, run, report = load_document(), None, None
                print("\nDOCUMENT INFORMATION")
                for field, value in document_info(doc["text"], doc["pages"]).items():
                    print(f"  {field}: {value}")
            elif choice == "2":
                if not doc:
                    print("Load a document first (option 1).")
                    continue
                kinds = list(ANALYSIS_TYPES)
                pick = input(f"Analysis type {kinds} [Complete]: ").strip().title() or "Complete"
                analysis_type = pick if pick in ANALYSIS_TYPES else "Complete"
                pre = preprocess(doc["text"])
                print(f"Preprocessed: {len(pre['sections'])} sections, {len(pre['chunks'])} chunk(s).")
                print(f"Asking {MODEL_NAME}... (this can take a minute)")
                run, report = analyze(pre["chunks"], analysis_type, pre["hints"]), None
                print("Analysis complete. Choose option 3 to generate the summary.")
            elif choice == "3":
                if not run:
                    print("Analyze the document first (option 2).")
                    continue
                report = format_report(run["responses"][-1], analysis_type)
                print("\n" + report)
            elif choice == "4":
                if not report:
                    print("Generate the summary first (option 3).")
                    continue
                print(f"Report saved to {save_report(report, doc['name']).as_posix()}")
            elif choice == "5":
                print("Goodbye.")
                break
            else:
                print("Please enter a number from 1 to 5.")
        except (ValueError, OllamaError) as err:
            print(f"Error: {err}")


if __name__ == "__main__":
    main()

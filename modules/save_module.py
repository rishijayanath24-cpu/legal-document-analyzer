"""Save Module: writes the generated analysis to outputs/legal_analysis.txt."""
from datetime import datetime
from pathlib import Path

DEFAULT_PATH = Path("outputs") / "legal_analysis.txt"


def save_report(report: str, source_name: str, path: Path = DEFAULT_PATH) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    path.write_text(f"{report}\n{'-' * 32}\nSource document: {source_name}\nGenerated: {stamp}\n",
                    encoding="utf-8")
    return path

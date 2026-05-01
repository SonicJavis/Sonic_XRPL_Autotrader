from pathlib import Path
from typing import Any

def write_adapter_report(path: Path, summary: Any):
    with open(path, "w") as f:
        f.write("# Phase 41: Data Adapter Report\n\n")
        f.write(f"- Source: {summary.source_type}\n")
        f.write(f"- Records Read: {summary.records_read}\n")
        f.write(f"- Quality Score: {summary.quality_score}\n\n")
        f.write("## Safety Status\n")
        f.write("READ-ONLY. NO WALLET. NO SIGNING. NO SUBMISSION.\n")

import json
from pathlib import Path
from typing import List, Dict, Any
from execution_prototype.paper_operator.models import PaperDecision, PaperLedgerState
from execution_prototype.paper_review.models import PaperTradeHistory
from execution_prototype.paper_review.trade_journal import create_paper_trade

def write_decisions(output_dir: Path, decisions: List[PaperDecision]):
    output_dir.mkdir(parents=True, exist_ok=True)
    with open(output_dir / "paper_decisions.jsonl", "w", encoding="utf-8") as f:
        for d in decisions:
            f.write(json.dumps(d.to_dict()) + "\n")

def write_ledger(output_dir: Path, ledger: PaperLedgerState):
    output_dir.mkdir(parents=True, exist_ok=True)
    with open(output_dir / "paper_ledger_state.json", "w", encoding="utf-8") as f:
        json.dump(ledger.to_dict(), f, indent=2)

def write_history(output_dir: Path, history: List[PaperTradeHistory]):
    output_dir.mkdir(parents=True, exist_ok=True)
    with open(output_dir / "paper_trade_history.jsonl", "w", encoding="utf-8") as f:
        for t in history:
            f.write(json.dumps(t.to_dict()) + "\n")

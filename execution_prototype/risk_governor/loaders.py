import json
from pathlib import Path
from typing import List, Dict, Any, Optional

def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    results = []
    if not path.exists():
        return results
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                results.append(json.loads(line))
    return results

def load_json(path: Path) -> Optional[Dict[str, Any]]:
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

# Phase 33
def load_early_warnings(phase33_dir: Path) -> List[Dict[str, Any]]:
    return load_jsonl(phase33_dir / "early_warnings.jsonl")

def load_drift_summary(phase33_dir: Path) -> Optional[Dict[str, Any]]:
    return load_json(phase33_dir / "drift_summary.json")

# Phase 34
def load_meme_candidates(phase34_dir: Path) -> List[Dict[str, Any]]:
    return load_jsonl(phase34_dir / "meme_candidates.jsonl")

# Phase 35
def load_paper_review(phase35_dir: Path) -> Optional[Dict[str, Any]]:
    return load_json(phase35_dir / "paper_performance_review.json")

# Phase 36
def load_paper_campaign(phase36_dir: Path) -> Optional[Dict[str, Any]]:
    return load_json(phase36_dir / "paper_campaign.json")

def load_paper_decisions(phase36_dir: Path) -> List[Dict[str, Any]]:
    return load_jsonl(phase36_dir / "paper_decisions.jsonl")

def load_paper_trades(phase36_dir: Path) -> List[Dict[str, Any]]:
    return load_jsonl(phase36_dir / "paper_trade_history.jsonl")

# Phase 37
def load_strategy_backtests(phase37_dir: Path) -> List[Dict[str, Any]]:
    return load_jsonl(phase37_dir / "strategy_backtest_results.jsonl")

def load_strategy_tournament(phase37_dir: Path) -> Optional[Dict[str, Any]]:
    return load_json(phase37_dir / "strategy_tournament_results.json")

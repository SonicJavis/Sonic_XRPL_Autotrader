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

def load_discovery_candidates(discovery_dir: Path) -> List[Dict[str, Any]]:
    return load_jsonl(discovery_dir / "meme_candidates.jsonl")

def load_paper_trades(paper_dir: Path) -> List[Dict[str, Any]]:
    return load_jsonl(paper_dir / "paper_trade_history.jsonl")

def load_paper_decisions(paper_dir: Path) -> List[Dict[str, Any]]:
    return load_jsonl(paper_dir / "paper_decisions.jsonl")

def load_paper_review(paper_dir: Path) -> Optional[Dict[str, Any]]:
    path = paper_dir / "paper_performance_review.json"
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def load_price_fixtures(fixtures_dir: Path) -> Dict[str, float]:
    prices = {}
    if fixtures_dir and fixtures_dir.exists():
        path = fixtures_dir / "prices.json"
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                prices = json.load(f)
    return prices

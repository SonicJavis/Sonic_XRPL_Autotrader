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

def load_discovery_candidates(directory: Path) -> List[Dict[str, Any]]:
    candidates_file = directory / "meme_candidates.jsonl"
    return load_jsonl(candidates_file)

def load_drift_warnings(directory: Path) -> List[Dict[str, Any]]:
    # Optional phase 33 drift warnings
    warnings_file = directory / "early_warnings.jsonl"
    return load_jsonl(warnings_file)

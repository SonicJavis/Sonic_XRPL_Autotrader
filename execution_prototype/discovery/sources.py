import json
from pathlib import Path
from typing import List, Dict, Any

def load_fixture_transactions(file_path: str) -> List[Dict[str, Any]]:
    path = Path(file_path)
    if not path.exists():
        return []
    
    # Simple JSON/JSONL reader for mock transactions
    txs = []
    with open(path, "r", encoding="utf-8") as f:
        if path.suffix == ".jsonl":
            for line in f:
                line = line.strip()
                if line:
                    txs.append(json.loads(line))
        else:
            data = json.load(f)
            if isinstance(data, list):
                txs.extend(data)
            else:
                txs.append(data)
                
    return txs

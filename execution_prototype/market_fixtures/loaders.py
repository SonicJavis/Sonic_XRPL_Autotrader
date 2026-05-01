import json
from pathlib import Path
from typing import List, Dict, Any
from .models import PriceSnapshot, LiquiditySnapshot

def load_price_snapshots(file_path: Path) -> List[Dict[str, Any]]:
    if not file_path.exists():
        return []
    
    snapshots = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                try:
                    snapshots.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return snapshots

def load_liquidity_snapshots(file_path: Path) -> List[Dict[str, Any]]:
    if not file_path.exists():
        return []
    
    snapshots = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                try:
                    snapshots.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return snapshots

def load_asset_metadata(file_path: Path) -> List[Dict[str, Any]]:
    if not file_path.exists():
        return []
    
    metadata = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                try:
                    metadata.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return metadata

import json
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional
from .models import BacktestDatasetSource

def get_deterministic_id(inputs: List[Any]) -> str:
    """Generate a deterministic SHA256 hash from sorted inputs."""
    # Convert all inputs to stable strings
    stable_strings = []
    for item in inputs:
        if isinstance(item, (dict, list)):
            stable_strings.append(json.dumps(item, sort_keys=True))
        else:
            stable_strings.append(str(item))
    
    combined = "|".join(stable_strings)
    return hashlib.sha256(combined.encode("utf-8")).hexdigest()

def get_file_hash(path: Path) -> str:
    """Calculate SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

class DatasetLoader:
    """Loads records from various source formats."""

    def load_jsonl(self, path: Path) -> List[Dict[str, Any]]:
        records = []
        if not path.exists():
            return records
        
        with open(path, "r") as f:
            for line in f:
                if line.strip():
                    records.append(json.loads(line))
        return records

    def identify_source(self, path: Path) -> BacktestDatasetSource:
        """Identify source type and metadata from a directory or file."""
        source_hash = ""
        records_loaded = 0
        source_type = "unknown"
        
        if path.is_file():
            source_hash = get_file_hash(path)
            # Rough identification by filename
            name = path.name
            if name in ["meme_candidates.jsonl", "discovery_scores.jsonl", "raw_discovery_events.jsonl"]:
                source_type = "discovery_report"
            elif name in ["normalized_price_snapshots.jsonl", "normalized_liquidity_snapshots.jsonl", "market_timelines.jsonl"]:
                source_type = "market_fixtures"
            elif name in ["raw_source_records.jsonl", "prices.jsonl", "liquidity.jsonl"]:
                source_type = "adapter_export"
            
            records_loaded = len(self.load_jsonl(path))
        
        source_id = get_deterministic_id([str(path), source_type, source_hash])
        
        return BacktestDatasetSource(
            source_id=source_id,
            source_type=source_type,
            source_path=str(path),
            source_hash=source_hash,
            records_loaded=records_loaded
        )

    def load_discovery_report(self, report_dir: Path) -> Dict[str, List[Dict[str, Any]]]:
        """Load Phase 34 discovery report files."""
        return {
            "candidates": self.load_jsonl(report_dir / "meme_candidates.jsonl"),
            "scores": self.load_jsonl(report_dir / "discovery_scores.jsonl"),
            "events": self.load_jsonl(report_dir / "raw_discovery_events.jsonl")
        }

    def load_market_fixtures(self, fixture_dir: Path) -> Dict[str, List[Dict[str, Any]]]:
        """Load Phase 40 market fixture files."""
        return {
            "prices": self.load_jsonl(fixture_dir / "normalized_price_snapshots.jsonl"),
            "liquidity": self.load_jsonl(fixture_dir / "normalized_liquidity_snapshots.jsonl"),
            "timelines": self.load_jsonl(fixture_dir / "market_timelines.jsonl")
        }

    def load_adapter_export(self, export_dir: Path) -> Dict[str, List[Dict[str, Any]]]:
        """Load Phase 41 adapter export files."""
        return {
            "raw_records": self.load_jsonl(export_dir / "raw_source_records.jsonl"),
            "prices": self.load_jsonl(export_dir / "prices.jsonl"),
            "liquidity": self.load_jsonl(export_dir / "liquidity.jsonl"),
            "amm_snapshots": self.load_jsonl(export_dir / "amm_snapshots.jsonl"),
            "orderbook_snapshots": self.load_jsonl(export_dir / "orderbook_snapshots.jsonl"),
            "asset_metadata": self.load_jsonl(export_dir / "asset_metadata.jsonl")
        }

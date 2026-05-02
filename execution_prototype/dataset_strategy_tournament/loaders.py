from __future__ import annotations
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List


def get_deterministic_id(inputs: List[Any]) -> str:
    combined = "|".join(sorted(str(i) for i in inputs))
    return hashlib.sha256(combined.encode()).hexdigest()


class DatasetLoader:
    def load_dataset_folder(self, folder: Path) -> dict:
        result: dict = {
            "manifest": {},
            "sources": [],
            "windows": [],
            "quality_report": {},
            "records_by_window": {
                "train": [],
                "validation": [],
                "test": [],
                "replay": [],
                "holdout": [],
            },
        }
        if not folder.exists():
            return result

        manifest_path = folder / "dataset_manifest.json"
        if manifest_path.exists():
            try:
                result["manifest"] = json.loads(manifest_path.read_text())
            except Exception:
                pass

        sources_path = folder / "dataset_sources.jsonl"
        if sources_path.exists():
            result["sources"] = self._load_jsonl(sources_path)

        windows_path = folder / "backtest_windows.jsonl"
        if windows_path.exists():
            result["windows"] = self._load_jsonl(windows_path)

        quality_path = folder / "dataset_quality_report.json"
        if quality_path.exists():
            try:
                result["quality_report"] = json.loads(quality_path.read_text())
            except Exception:
                pass

        for wtype in ("train", "validation", "test", "replay", "holdout"):
            rpath = folder / f"{wtype}_records.jsonl"
            if rpath.exists():
                result["records_by_window"][wtype] = self._load_jsonl(rpath)

        return result

    def load_strategy_report(self, folder: Path) -> dict:
        if not folder or not folder.exists():
            return {}
        for fname in ("strategy_report.json", "strategy_tournament_report.json", "tournament_report.json"):
            p = folder / fname
            if p.exists():
                try:
                    return json.loads(p.read_text())
                except Exception:
                    pass
        return {}

    def load_market_fixtures_report(self, folder: Path) -> dict:
        if not folder or not folder.exists():
            return {}
        for fname in ("market_fixtures_report.json", "fixtures_report.json", "market_report.json"):
            p = folder / fname
            if p.exists():
                try:
                    return json.loads(p.read_text())
                except Exception:
                    pass
        return {}

    def _load_jsonl(self, path: Path) -> List[dict]:
        records = []
        try:
            for line in path.read_text().splitlines():
                line = line.strip()
                if line:
                    try:
                        records.append(json.loads(line))
                    except Exception:
                        pass
        except Exception:
            pass
        return records

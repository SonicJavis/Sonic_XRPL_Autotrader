import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from .models import (
    BacktestDatasetManifest, 
    BacktestDatasetSource, 
    BacktestWindow, 
    BacktestDatasetQualityReport,
    DatasetExportSummary
)
from .loaders import get_deterministic_id

class DatasetExporter:
    """Exports dataset components to disk."""

    def export(
        self,
        output_base_dir: Path,
        manifest: BacktestDatasetManifest,
        sources: List[BacktestDatasetSource],
        windows: List[BacktestWindow],
        quality_report: BacktestDatasetQualityReport,
        split_records: Dict[str, List[Dict[str, Any]]]
    ) -> DatasetExportSummary:
        
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        export_dir = output_base_dir / manifest.dataset_id / timestamp
        export_dir.mkdir(parents=True, exist_ok=True)
        
        files_written = []
        total_records = 0
        
        # Write metadata files
        metadata_files = {
            "dataset_manifest.json": manifest,
            "dataset_quality_report.json": quality_report
        }
        
        for name, obj in metadata_files.items():
            path = export_dir / name
            with open(path, "w") as f:
                json.dump(self._to_dict(obj), f, indent=2)
            files_written.append(name)
            
        # Write list files
        list_files = {
            "dataset_sources.jsonl": sources,
            "backtest_windows.jsonl": windows
        }
        
        for name, items in list_files.items():
            path = export_dir / name
            with open(path, "w") as f:
                for item in items:
                    f.write(json.dumps(self._to_dict(item)) + "\n")
            files_written.append(name)
            
        # Write split records
        for split_name, records in split_records.items():
            if not records:
                continue
            name = f"{split_name}_records.jsonl"
            path = export_dir / name
            with open(path, "w") as f:
                for record in records:
                    f.write(json.dumps(record) + "\n")
            files_written.append(name)
            total_records += len(records)
            
        export_id = get_deterministic_id([manifest.dataset_id, timestamp, sorted(files_written)])
        
        summary = DatasetExportSummary(
            export_id=export_id,
            dataset_id=manifest.dataset_id,
            output_path=str(export_dir),
            files_written=files_written,
            records_written=total_records
        )
        
        # Save summary
        with open(export_dir / "dataset_export_summary.json", "w") as f:
            json.dump(self._to_dict(summary), f, indent=2)
        files_written.append("dataset_export_summary.json")
        
        return summary

    def _to_dict(self, obj: Any) -> Dict[str, Any]:
        """Convert dataclass to dict recursively."""
        from dataclasses import asdict
        return asdict(obj)

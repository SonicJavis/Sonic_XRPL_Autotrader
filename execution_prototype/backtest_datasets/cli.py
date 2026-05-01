import argparse
import sys
from pathlib import Path
from typing import List, Dict, Any

from .loaders import DatasetLoader
from .window_builder import WindowBuilder
from .splitter import DatasetSplitter
from .leakage_checks import LeakageChecker
from .quality_checks import QualityChecker
from .manifest import ManifestBuilder
from .exporter import DatasetExporter
from .report_writer import ReportWriter

def main():
    parser = argparse.ArgumentParser(description="Phase 42: Historical Backtest Dataset Builder")
    parser.add_argument("--dataset-name", required=True, help="Name of the dataset")
    parser.add_argument("--dataset-version", default="v1", help="Version of the dataset")
    parser.add_argument("--discovery-report", type=Path, help="Path to discovery report directory")
    parser.add_argument("--market-fixtures", type=Path, help="Path to market fixtures directory")
    parser.add_argument("--adapter-export", type=Path, help="Path to adapter export directory")
    parser.add_argument("--output-dir", type=Path, default=Path("./datasets/backtests"), help="Output directory")
    parser.add_argument("--split-strategy", default="chronological_60_20_20", help="Split strategy")
    parser.add_argument("--strict", action="store_true", help="Fail on critical issues")
    parser.add_argument("--dry-run", action="store_true", help="Dry run mode")

    args = parser.parse_args()

    print(f"--- Phase 42: Building Dataset '{args.dataset_name}' ({args.dataset_version}) ---")

    loader = DatasetLoader()
    builder = WindowBuilder()
    splitter = DatasetSplitter()
    leakage_checker = LeakageChecker()
    quality_checker = QualityChecker()
    manifest_builder = ManifestBuilder()
    exporter = DatasetExporter()
    report_writer = ReportWriter()

    all_records = []
    sources = []

    # Load data
    if args.discovery_report:
        print(f"Loading discovery report from {args.discovery_report}...")
        data = loader.load_discovery_report(args.discovery_report)
        for k, v in data.items():
            all_records.extend(v)
        sources.append(loader.identify_source(args.discovery_report))

    if args.market_fixtures:
        print(f"Loading market fixtures from {args.market_fixtures}...")
        data = loader.load_market_fixtures(args.market_fixtures)
        for k, v in data.items():
            all_records.extend(v)
        sources.append(loader.identify_source(args.market_fixtures))

    if args.adapter_export:
        print(f"Loading adapter export from {args.adapter_export}...")
        data = loader.load_adapter_export(args.adapter_export)
        for k, v in data.items():
            all_records.extend(v)
        sources.append(loader.identify_source(args.adapter_export))

    if not all_records:
        print("Error: No records found. Please provide at least one source.")
        sys.exit(1)

    print(f"Total records loaded: {len(all_records)}")

    # Check leakage
    leakage_issues = leakage_checker.check_future_leakage(all_records)
    
    # Quality check
    quality_report = quality_checker.generate_report("temp_id", all_records)
    
    if leakage_issues:
        # Update quality report with leakage info
        from dataclasses import replace
        quality_report = replace(
            quality_report, 
            future_leakage_count=len(leakage_issues),
            quality_score=min(quality_report.quality_score, 30),
            critical_issues=quality_report.critical_issues + leakage_issues
        )

    if args.strict and quality_report.critical_issues:
        print("Critical issues found in strict mode:")
        for issue in quality_report.critical_issues:
            print(f" - {issue}")
        sys.exit(1)

    # Build windows and split
    windows = builder.build_windows_by_ledger("temp_id", all_records)
    split_records = splitter.split_chronologically(all_records)
    
    # Build manifest
    limitations = []
    if not args.discovery_report: limitations.append("Missing discovery metadata.")
    if not args.market_fixtures and not args.adapter_export: limitations.append("Missing price/liquidity data.")

    manifest = manifest_builder.build_manifest(
        args.dataset_name,
        args.dataset_version,
        [s.source_id for s in sources],
        windows,
        all_records,
        quality_report.quality_score,
        limitations
    )

    # Re-link quality report and windows to final dataset_id
    from dataclasses import replace
    quality_report = replace(quality_report, dataset_id=manifest.dataset_id)
    windows = [replace(w, dataset_id=manifest.dataset_id) for w in windows]

    if args.dry_run:
        print("Dry run complete. No files written.")
        print(f"Dataset ID: {manifest.dataset_id}")
        print(f"Quality Score: {manifest.quality_score}")
        return

    # Export
    summary = exporter.export(
        args.output_dir,
        manifest,
        sources,
        windows,
        quality_report,
        split_records
    )

    # Write report
    report_path = Path(summary.output_path) / "dataset_report.md"
    report_writer.write_report(
        report_path,
        manifest,
        sources,
        quality_report,
        summary
    )

    print(f"Dataset successfully exported to: {summary.output_path}")
    print(f"Dataset Report: {report_path}")

if __name__ == "__main__":
    main()

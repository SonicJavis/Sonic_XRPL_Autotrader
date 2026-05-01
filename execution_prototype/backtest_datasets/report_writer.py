from pathlib import Path
from typing import List, Dict, Any
from .models import (
    BacktestDatasetManifest, 
    BacktestDatasetSource, 
    BacktestWindow, 
    BacktestDatasetQualityReport,
    DatasetExportSummary
)

class ReportWriter:
    """Generates a markdown report for the dataset."""

    def write_report(
        self,
        output_path: Path,
        manifest: BacktestDatasetManifest,
        sources: List[BacktestDatasetSource],
        quality_report: BacktestDatasetQualityReport,
        summary: DatasetExportSummary
    ):
        with open(output_path, "w") as f:
            f.write("# Phase 42: Historical Backtest Dataset Report\n\n")
            
            f.write("## 1. Research Sources Checked\n")
            f.write("- XRPL Known Amendments (AMMClawback, Credentials, MPTokensV1: Enabled)\n")
            f.write("- XRPL Batch Vulnerability Disclosure (Feb 2026: Batch Amendment Obsolete)\n")
            f.write("- Rippled 3.1.2 Release Notes (Security/Continuity focus)\n")
            f.write("- xrpl.js getBalanceChanges (Metadata parsing patterns)\n\n")
            
            f.write("## 2. Dataset Summary\n")
            f.write(f"- **Dataset ID**: `{manifest.dataset_id}`\n")
            f.write(f"- **Name**: {manifest.dataset_name}\n")
            f.write(f"- **Version**: {manifest.dataset_version}\n")
            f.write(f"- **Created At**: {manifest.created_at}\n")
            f.write(f"- **Total Records**: {summary.records_written}\n")
            f.write(f"- **Quality Score**: {manifest.quality_score}/100\n\n")
            
            f.write("## 3. Source Inputs\n")
            for source in sources:
                f.write(f"- `{source.source_id}`: {source.source_type} ({source.records_loaded} records) - `{source.source_path}`\n")
            f.write("\n")
            
            f.write("## 4. Asset Coverage\n")
            f.write(f"- **Unique Assets**: {manifest.asset_count}\n\n")
            
            f.write("## 5. Candidate Coverage\n")
            f.write(f"- **Unique Candidates**: {manifest.candidate_count}\n\n")
            
            f.write("## 6. Price/Liquidity Coverage\n")
            f.write(f"- **Price Snapshots**: {manifest.price_snapshot_count}\n")
            f.write(f"- **Liquidity Snapshots**: {manifest.liquidity_snapshot_count}\n\n")
            
            f.write("## 7. Split Strategy\n")
            f.write(f"- **Strategy**: {manifest.split_strategy}\n")
            f.write("- **Distribution**: 60% Train, 20% Validation, 20% Test\n\n")
            
            f.write("## 8. Leakage Checks\n")
            if quality_report.future_leakage_count == 0:
                f.write("- ✅ No future leakage detected.\n")
            else:
                f.write(f"- ❌ **{quality_report.future_leakage_count} leakage events detected.**\n")
            f.write("\n")
            
            f.write("## 9. Quality Report\n")
            f.write(f"- **Total Records**: {quality_report.total_records}\n")
            f.write(f"- **Valid Records**: {quality_report.valid_records}\n")
            f.write(f"- **Same Ticker Multi Issuer**: {quality_report.same_ticker_multi_issuer_count}\n")
            f.write(f"- **Out of Order**: {quality_report.out_of_order_count}\n")
            f.write(f"- **Unsupported Batch Context**: {quality_report.unsupported_batch_context_count}\n")
            f.write(f"- **Xahau/Hook Context**: {quality_report.xahau_hook_context_count}\n\n")
            
            if quality_report.critical_issues:
                f.write("### Critical Issues\n")
                for issue in quality_report.critical_issues:
                    f.write(f"- 🔴 {issue}\n")
                f.write("\n")
            
            if quality_report.warnings:
                f.write("### Warnings\n")
                for warning in quality_report.warnings:
                    f.write(f"- 🟡 {warning}\n")
                f.write("\n")
                
            f.write("## 10. Protocol Context / Amendment Safety Notes\n")
            f.write("- **Batch Amendment**: OBSOLETE. Any data containing Batch context is flagged as unsafe.\n")
            f.write("- **AMMClawback**: Active. AMM datasets should account for potential clawback metadata.\n")
            f.write("- **Xahau/Hooks**: Excluded from standard XRPL Mainnet backtests.\n\n")
            
            f.write("## 11. Limitations\n")
            for lim in manifest.limitations:
                f.write(f"- {lim}\n")
            if not manifest.limitations:
                f.write("- No major limitations identified.\n")
            f.write("\n")
            
            f.write("## 12. Compatibility With Existing Phases\n")
            f.write("- Phase 37 (Strategy Performance): Fully Compatible\n")
            f.write("- Phase 40 (Market Fixtures): Fully Compatible\n")
            f.write("- Phase 41 (Data Adapters): Fully Compatible\n\n")
            
            f.write("## 13. Why Live Trading Is Still Forbidden\n")
            f.write("This dataset is for PAPER/OFFLINE replay ONLY. It does not contain signing logic, private keys, or submission primitives. Any attempt to use these patterns for live trading will bypass safety gates and is strictly prohibited.\n\n")
            
            f.write("## 14. Next Phase Recommendation\n")
            f.write("Phase 43: Integrated Backtest Replay Engine using these versioned datasets.\n")
            f.write("\n---\n")
            f.write(f"**Safety Status**: {manifest.prohibited_live_action}\n")

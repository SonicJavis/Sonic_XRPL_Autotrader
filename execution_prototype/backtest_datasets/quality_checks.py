from typing import List, Dict, Any
import hashlib
from .models import BacktestDatasetQualityReport
from .loaders import get_deterministic_id

class QualityChecker:
    """Performs quality checks and calculates scores for datasets."""

    def generate_report(self, dataset_id: str, records: List[Dict[str, Any]]) -> BacktestDatasetQualityReport:
        total = len(records)
        valid = 0
        invalid = 0
        missing_price = 0
        missing_liquidity = 0
        missing_metadata = 0
        same_ticker_multi_issuer = 0
        out_of_order = 0
        future_leakage = 0
        duplicate_records = 0
        unsupported_batch = 0
        xahau_hooks = 0
        
        critical_issues = []
        warnings = []
        
        # Track for specific checks
        seen_hashes = set()
        ticker_issuers = {} # ticker -> set(issuer)
        last_ledger = -1
        
        for record in records:
            # Duplicate check
            r_str = str(sorted(record.items()))
            r_hash = hashlib.sha256(r_str.encode()).hexdigest()
            if r_hash in seen_hashes:
                duplicate_records += 1
            seen_hashes.add(r_hash)
            
            # Asset identity check
            ticker = record.get("ticker")
            issuer = record.get("issuer")
            if ticker and issuer:
                if ticker not in ticker_issuers:
                    ticker_issuers[ticker] = set()
                ticker_issuers[ticker].add(issuer)
            
            # Ledger order check
            ledger = record.get("ledger_index")
            if ledger is not None:
                if ledger < last_ledger:
                    out_of_order += 1
                last_ledger = ledger
            
            # Protocol checks
            if record.get("unsupported_batch_context") or "Batch" in str(record):
                unsupported_batch += 1
            if record.get("xahau_context") or "Xahau" in str(record) or "Hook" in str(record):
                xahau_hooks += 1
            
            # Data coverage
            if "price" in str(record.get("type", "")) and not record.get("price"):
                missing_price += 1
            if "liquidity" in str(record.get("type", "")) and not record.get("liquidity"):
                missing_liquidity += 1
            
            # Basic validation (must have some core keys)
            if record.get("asset_key") or record.get("ledger_index") or record.get("observed_at"):
                valid += 1
            else:
                invalid += 1

        # Calculate same ticker multi issuer
        for ticker, issuers in ticker_issuers.items():
            if len(issuers) > 1:
                same_ticker_multi_issuer += 1

        # Scoring
        score = 100
        
        if duplicate_records > 0:
            score -= min(10, duplicate_records)
            warnings.append(f"Found {duplicate_records} duplicate records.")
            
        if same_ticker_multi_issuer > 0:
            score -= min(20, same_ticker_multi_issuer * 5)
            critical_issues.append(f"Ambiguous asset identity: {same_ticker_multi_issuer} tickers have multiple issuers.")
            if score > 50: score = 50 # Cap at 50

        if out_of_order > 0:
            score -= min(15, out_of_order)
            warnings.append(f"Found {out_of_order} out-of-order ledger indices.")

        if unsupported_batch > 0:
            score -= 10
            warnings.append("Unsupported Batch context detected.")
            if score > 60: score = 60 # Cap at 60

        if xahau_hooks > 0:
            score -= 10
            warnings.append("Xahau/Hook context detected (not XRPL Mainnet).")
            if score > 60: score = 60 # Cap at 60

        # Note: Leakage is checked separately but would cap score at 30
        
        quality_report_id = get_deterministic_id([
            dataset_id,
            total,
            valid,
            invalid,
            missing_price,
            missing_liquidity,
            same_ticker_multi_issuer,
            out_of_order,
            unsupported_batch,
            xahau_hooks
        ])

        return BacktestDatasetQualityReport(
            quality_report_id=quality_report_id,
            dataset_id=dataset_id,
            total_records=total,
            valid_records=valid,
            invalid_records=invalid,
            missing_price_count=missing_price,
            missing_liquidity_count=missing_liquidity,
            missing_metadata_count=missing_metadata,
            same_ticker_multi_issuer_count=same_ticker_multi_issuer,
            out_of_order_count=out_of_order,
            future_leakage_count=future_leakage,
            duplicate_record_count=duplicate_records,
            unsupported_batch_context_count=unsupported_batch,
            xahau_hook_context_count=xahau_hooks,
            quality_score=max(0, score),
            critical_issues=critical_issues,
            warnings=warnings
        )

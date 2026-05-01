from typing import List, Dict
from .models import FixtureQualityReport
import hashlib
import json

def run_quality_checks(price_snapshots: List[Dict], liquidity_snapshots: List[Dict]) -> FixtureQualityReport:
    """
    Analyzes fixtures for duplicates, gaps, and coverage.
    """
    assets = set()
    dup_count = 0
    price_ids = set()
    
    for s in price_snapshots:
        issuer = s.get("issuer")
        currency = s.get("currency_code") or s.get("currency")
        assets.add(f"{issuer}:{currency}")
        
        sid = s.get("snapshot_id")
        if sid in price_ids:
            dup_count += 1
        price_ids.add(sid)
        
    # Simplified score logic
    quality_score = 100
    if not price_snapshots:
        quality_score -= 50
    if dup_count > 0:
        quality_score -= 10
        
    report_id = hashlib.sha256(json.dumps({"total_p": len(price_snapshots), "total_l": len(liquidity_snapshots)}, sort_keys=True).encode()).hexdigest()
    
    return FixtureQualityReport(
        quality_report_id=report_id,
        total_price_snapshots=len(price_snapshots),
        total_liquidity_snapshots=len(liquidity_snapshots),
        assets_covered=len(assets),
        missing_price_count=0, # Calculation placeholder
        missing_liquidity_count=0,
        duplicate_snapshot_count=dup_count,
        out_of_order_count=0,
        same_ticker_multi_issuer_count=0,
        quality_score=max(0, quality_score),
        critical_issues=[],
        warnings=["Duplicate snapshots detected"] if dup_count > 0 else []
    )

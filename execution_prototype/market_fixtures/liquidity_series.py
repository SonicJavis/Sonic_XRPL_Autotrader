from typing import List, Dict, Optional
import hashlib
import json
from .models import LiquiditySnapshot, AssetKey
from .normalizer import normalize_asset

def build_liquidity_timeline(snapshots: List[Dict], asset_key: AssetKey) -> List[LiquiditySnapshot]:
    """
    Filters and sorts snapshots for a specific asset into a deterministic timeline.
    """
    relevant = []
    for s in snapshots:
        s_issuer = s.get("issuer")
        s_currency = s.get("currency_code") or s.get("currency")
        if not s_currency:
            continue
            
        s_asset = normalize_asset(s_issuer, s_currency)
        
        if s_asset.asset_key_id == asset_key.asset_key_id:
            snapshot_id = s.get("snapshot_id") or hashlib.sha256(json.dumps(s, sort_keys=True).encode()).hexdigest()
            
            relevant.append(LiquiditySnapshot(
                snapshot_id=snapshot_id,
                asset_key_id=asset_key.asset_key_id,
                issuer=asset_key.issuer,
                currency_code=asset_key.currency_code,
                ledger_index=s.get("ledger_index"),
                observed_at=s.get("observed_at"),
                amm_present=bool(s.get("amm_present", False)),
                amm_liquidity_xrp=str(s.get("amm_liquidity_xrp")) if s.get("amm_liquidity_xrp") is not None else None,
                orderbook_liquidity_xrp=str(s.get("orderbook_liquidity_xrp")) if s.get("orderbook_liquidity_xrp") is not None else None,
                estimated_exit_capacity_xrp=str(s.get("estimated_exit_capacity_xrp")) if s.get("estimated_exit_capacity_xrp") is not None else None,
                spread_pct=str(s.get("spread_pct")) if s.get("spread_pct") is not None else None,
                slippage_estimate_pct=str(s.get("slippage_estimate_pct")) if s.get("slippage_estimate_pct") is not None else None,
                source_event_ids=s.get("source_event_ids", []),
                confidence=s.get("confidence", "medium"),
                limitations=s.get("limitations", [])
            ))
            
    relevant.sort(key=lambda x: (x.ledger_index or 0, x.observed_at or ""))
    return relevant

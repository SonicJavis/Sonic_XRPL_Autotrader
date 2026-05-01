from typing import List, Dict, Optional
from decimal import Decimal
import hashlib
import json
from .models import PaperMarkToMarketResult, PriceSnapshot, LiquiditySnapshot, AssetKey
from .price_series import get_nearest_price

def enrich_paper_positions(
    positions: List[Dict],
    price_snapshots: List[Dict],
    liquidity_snapshots: List[Dict],
    campaign_id: str
) -> List[PaperMarkToMarketResult]:
    """
    Enriches Phase 36 paper positions with mark-to-market data.
    """
    results = []
    
    # Pre-build timelines by asset key for efficiency
    timelines: Dict[str, List[PriceSnapshot]] = {}
    
    for pos in positions:
        pos_id = pos.get("position_id")
        cand_id = pos.get("candidate_id")
        issuer = pos.get("issuer")
        currency = pos.get("currency_code")
        
        # Sort and identify asset
        from .normalizer import normalize_asset
        asset = normalize_asset(issuer, currency)
        ak_id = asset.asset_key_id
        
        if ak_id not in timelines:
            from .price_series import build_price_timeline
            timelines[ak_id] = build_price_timeline(price_snapshots, asset)
            
        timeline = timelines[ak_id]
        
        # Entry Valuation
        entry_time = pos.get("entry_time")
        # For entry, we might use the paper entry price if provided, or look up nearest fixture
        entry_price = str(pos.get("entry_price")) if pos.get("entry_price") is not None else None
        
        # Latest Valuation (Mark-to-market)
        latest_snapshot = timeline[-1] if timeline else None
        latest_price = latest_snapshot.price_xrp if latest_snapshot else None
        
        # Exit Valuation (if closed)
        exit_time = pos.get("exit_time")
        exit_price = str(pos.get("exit_price")) if pos.get("exit_price") is not None else None
        
        # PnL Calculation
        unrealized_pnl = None
        pnl_pct = None
        outcome = "unknown"
        unknown_reason = None
        
        if entry_price and latest_price:
            try:
                ep = Decimal(entry_price)
                lp = Decimal(latest_price)
                size = Decimal(str(pos.get("size_paper", 0)))
                
                unrealized_pnl = str((lp - ep) * size)
                pnl_pct = str(((lp / ep) - 1) * 100)
                
                if lp > ep:
                    outcome = "win"
                elif lp < ep:
                    outcome = "loss"
                else:
                    outcome = "breakeven"
            except Exception as e:
                unknown_reason = f"PnL calculation error: {str(e)}"
        else:
            unknown_reason = "Missing entry or latest price snapshot"
            
        # Deterministic Result ID
        res_data = {
            "position_id": pos_id,
            "campaign_id": campaign_id,
            "latest_price": latest_price
        }
        res_id = hashlib.sha256(json.dumps(res_data, sort_keys=True).encode()).hexdigest()
        
        results.append(PaperMarkToMarketResult(
            result_id=res_id,
            position_id=pos_id,
            campaign_id=campaign_id,
            candidate_id=cand_id,
            asset_key_id=ak_id,
            entry_time=entry_time,
            entry_price_paper=entry_price,
            latest_price_paper=latest_price,
            exit_price_paper=exit_price,
            unrealized_pnl_xrp=unrealized_pnl,
            realized_pnl_xrp=None, # For future enrichment
            pnl_pct=pnl_pct,
            liquidity_exit_confidence="medium", # Placeholder for liquidity engine
            outcome=outcome,
            unknown_reason=unknown_reason,
            source_snapshot_ids=[latest_snapshot.snapshot_id] if latest_snapshot else [],
            limitations=[]
        ))
        
    return results

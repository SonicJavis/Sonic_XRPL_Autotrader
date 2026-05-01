import hashlib
import json
from typing import List, Dict, Optional
from datetime import datetime
from .models import PriceSnapshot, AssetKey
from .normalizer import normalize_asset

def build_price_timeline(snapshots: List[Dict], asset_key: AssetKey) -> List[PriceSnapshot]:
    """
    Filters and sorts snapshots for a specific asset into a deterministic timeline.
    """
    relevant = []
    for s in snapshots:
        # Normalize snapshot asset
        s_issuer = s.get("issuer")
        s_currency = s.get("currency_code") or s.get("currency")
        if not s_currency:
            continue
            
        s_asset = normalize_asset(s_issuer, s_currency)
        
        if s_asset.asset_key_id == asset_key.asset_key_id:
            # Create snapshot object
            snapshot_id = s.get("snapshot_id") or hashlib.sha256(json.dumps(s, sort_keys=True).encode()).hexdigest()
            
            relevant.append(PriceSnapshot(
                snapshot_id=snapshot_id,
                asset_key_id=asset_key.asset_key_id,
                issuer=asset_key.issuer,
                currency_code=asset_key.currency_code,
                ledger_index=s.get("ledger_index"),
                observed_at=s.get("observed_at"),
                price_xrp=str(s.get("price_xrp")) if s.get("price_xrp") is not None else None,
                price_usd=str(s.get("price_usd")) if s.get("price_usd") is not None else None,
                source_event_id=s.get("source_event_id"),
                source_tx_hash=s.get("source_tx_hash"),
                confidence=s.get("confidence", "medium"),
                limitations=s.get("limitations", [])
            ))
            
    # Sort by ledger index, then observed_at
    relevant.sort(key=lambda x: (x.ledger_index or 0, x.observed_at or ""))
    return relevant

def get_nearest_price(timeline: List[PriceSnapshot], target_ledger: Optional[int], target_time: Optional[str], mode: str = "nearest") -> Optional[PriceSnapshot]:
    """
    Finds the nearest price snapshot.
    mode: 'at_or_after' | 'at_or_before' | 'nearest'
    """
    if not timeline:
        return None
        
    if mode == "at_or_before":
        candidates = [s for s in timeline if (target_ledger and s.ledger_index and s.ledger_index <= target_ledger) or (target_time and s.observed_at and s.observed_at <= target_time)]
        return candidates[-1] if candidates else None
    elif mode == "at_or_after":
        candidates = [s for s in timeline if (target_ledger and s.ledger_index and s.ledger_index >= target_ledger) or (target_time and s.observed_at and s.observed_at >= target_time)]
        return candidates[0] if candidates else None
    else: # nearest
        # Simple fallback for now
        return timeline[0]

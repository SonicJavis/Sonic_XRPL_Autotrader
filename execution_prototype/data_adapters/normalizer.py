import hashlib
import json
from typing import List, Dict, Any, Optional
from decimal import Decimal
from .models import RawSourceRecord, FixtureExportRecord

def normalize_to_fixtures(records: List[RawSourceRecord]) -> List[FixtureExportRecord]:
    """
    Converts raw records into Phase 40 compatible fixtures.
    """
    fixtures = []
    for rec in records:
        if rec.record_type == "transaction":
            # Extract price/liquidity from tx metadata
            tx = rec.payload
            meta = tx.get("meta", {})
            
            # Example: Extract price from OfferCreate or Payment delivered_amount
            # This is where xrpl.utils.get_balance_changes would be used in a full implementation.
            
            # For now, we provide the mapping logic structure.
            pass
            
        elif rec.record_type == "firstledger_trade":
            # Direct mapping from FirstLedger trade format
            pass
            
    return fixtures

def generate_export_id(record_ids: List[str], fixture_type: str) -> str:
    raw = f"{fixture_type}:{sorted(record_ids)}"
    return hashlib.sha256(raw.encode()).hexdigest()

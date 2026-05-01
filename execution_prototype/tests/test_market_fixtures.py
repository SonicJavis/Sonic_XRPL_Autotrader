import pytest
from pathlib import Path
from decimal import Decimal
from execution_prototype.market_fixtures.normalizer import normalize_asset
from execution_prototype.market_fixtures.models import AssetKey, PriceSnapshot
from execution_prototype.market_fixtures.price_series import build_price_timeline
from execution_prototype.market_fixtures.mark_to_market import enrich_paper_positions

def test_asset_normalization():
    # XRP
    ak = normalize_asset(None, "XRP")
    assert ak.asset_type == "xrp"
    assert ak.normalized_currency == "XRP"
    assert ak.issuer is None
    
    # Issued Currency
    ak2 = normalize_asset("rhub8VRN5paDESTPBmDxQQeo3hYV2m4NVR", "USDC")
    assert ak2.asset_type == "issued_currency"
    assert ak2.issuer == "rhub8VRN5paDESTPBmDxQQeo3hYV2m4NVR"
    assert ak2.normalized_currency == "USDC"
    
    # Same ticker, different issuer
    ak3 = normalize_asset("rvYAfWj5gh67oV6fW32ZzP3Aw4Eubs59B", "USDC")
    assert ak2.asset_key_id != ak3.asset_key_id

def test_deterministic_ids():
    ak = normalize_asset("issuer", "USD")
    id1 = ak.asset_key_id
    ak_again = normalize_asset("issuer", "USD")
    assert id1 == ak_again.asset_key_id

def test_price_timeline_sorting():
    ak = normalize_asset("issuer", "USD")
    snapshots = [
        {"issuer": "issuer", "currency": "USD", "ledger_index": 100, "price_xrp": "1.0"},
        {"issuer": "issuer", "currency": "USD", "ledger_index": 50, "price_xrp": "0.5"},
    ]
    timeline = build_price_timeline(snapshots, ak)
    assert len(timeline) == 2
    assert timeline[0].ledger_index == 50
    assert timeline[1].ledger_index == 100

def test_mark_to_market_enrichment():
    positions = [
        {
            "position_id": "p1",
            "candidate_id": "c1",
            "issuer": "issuer",
            "currency_code": "USD",
            "entry_price": "1.0",
            "size_paper": "100",
            "entry_time": "2026-01-01T00:00:00Z"
        }
    ]
    prices = [
        {"issuer": "issuer", "currency": "USD", "ledger_index": 100, "price_xrp": "1.2", "snapshot_id": "s1"}
    ]
    
    results = enrich_paper_positions(positions, prices, [], "camp1")
    assert len(results) == 1
    res = results[0]
    assert res.outcome == "win"
    assert Decimal(res.unrealized_pnl_xrp) == Decimal("20.0") # (1.2 - 1.0) * 100
    assert Decimal(res.pnl_pct) == Decimal("20.0")

def test_missing_price_unknown_outcome():
    positions = [{"position_id": "p1", "issuer": "i", "currency_code": "C", "entry_price": "1.0"}]
    results = enrich_paper_positions(positions, [], [], "camp1")
    assert results[0].outcome == "unknown"
    assert results[0].unknown_reason is not None

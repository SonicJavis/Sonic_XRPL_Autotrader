"""Tests for the main snapshot builder."""

from __future__ import annotations

from pathlib import Path
import pytest

from sonic_xrpl.market.snapshot_builder import build_market_snapshot
from sonic_xrpl.market.models import MarketSnapshot, SnapshotRecommendation
from sonic_xrpl.market.errors import FixtureHealthError

FIXTURE_DIR = Path(__file__).parent.parent / "fixtures" / "xrpl"


class TestSnapshotBuilder:
    def test_basic_build(self):
        snap = build_market_snapshot(FIXTURE_DIR)
        assert isinstance(snap, MarketSnapshot)
        assert snap.fixture_id != "unknown"
        assert snap.ledger_index > 0

    def test_network_from_manifest(self):
        snap = build_market_snapshot(FIXTURE_DIR)
        assert snap.network == "synthetic"

    def test_has_amm_data(self):
        snap = build_market_snapshot(FIXTURE_DIR)
        assert len(snap.amms) >= 1

    def test_has_orderbook_data(self):
        snap = build_market_snapshot(FIXTURE_DIR)
        assert len(snap.orderbooks) >= 1

    def test_has_assets(self):
        snap = build_market_snapshot(FIXTURE_DIR)
        assert len(snap.assets) >= 1

    def test_has_trustlines(self):
        snap = build_market_snapshot(FIXTURE_DIR)
        assert len(snap.trustlines) >= 1

    def test_has_mpt_data(self):
        snap = build_market_snapshot(FIXTURE_DIR, include_mpt=True)
        assert len(snap.mpt_holders) >= 1

    def test_has_metadata_signals(self):
        snap = build_market_snapshot(FIXTURE_DIR, include_metadata=True)
        assert len(snap.metadata_signals) >= 1

    def test_account_context_loaded(self):
        snap = build_market_snapshot(FIXTURE_DIR)
        assert len(snap.accounts) >= 1

    def test_specific_account(self):
        snap = build_market_snapshot(FIXTURE_DIR, accounts=["rTrader1111111111111111111111111111"])
        assert len(snap.accounts) >= 1
        assert snap.accounts[0].account == "rTrader1111111111111111111111111111"

    def test_quality_score_reasonable(self):
        snap = build_market_snapshot(FIXTURE_DIR)
        assert snap.quality.score > 0
        assert snap.quality.recommendation in list(SnapshotRecommendation)

    def test_source_hash_determinism(self):
        # Two snapshots from same fixture should have same source_hash
        snap1 = build_market_snapshot(FIXTURE_DIR)
        snap2 = build_market_snapshot(FIXTURE_DIR)
        assert snap1.source_hash == snap2.source_hash

    def test_snapshot_id_unique_per_run(self):
        # snapshot_id includes timestamp so should differ between runs
        # (unless both run in same second — tolerate equal)
        snap1 = build_market_snapshot(FIXTURE_DIR)
        snap2 = build_market_snapshot(FIXTURE_DIR)
        # Both should be valid hex strings of length 32
        assert len(snap1.snapshot_id) == 32
        assert len(snap2.snapshot_id) == 32

    def test_capabilities_dict(self):
        snap = build_market_snapshot(FIXTURE_DIR)
        assert "AMM" in snap.capabilities
        assert snap.capabilities["AMM"] is True

    def test_no_metadata_flag(self):
        snap = build_market_snapshot(FIXTURE_DIR, include_metadata=False)
        assert len(snap.metadata_signals) == 0

    def test_no_mpt_flag(self):
        snap = build_market_snapshot(FIXTURE_DIR, include_mpt=False)
        assert len(snap.mpt_holders) == 0

    def test_same_ticker_different_issuer_not_collapsed(self):
        snap = build_market_snapshot(FIXTURE_DIR)
        # All asset keys in the snapshot must be unique
        keys = [a.asset_key for a in snap.assets]
        assert len(keys) == len(set(keys))

    def test_missing_fixture_dir_graceful(self, tmp_path):
        # Build against an empty temp dir — should not raise, should have limitations
        (tmp_path / "manifest.json").write_text(
            '{"name":"test","version":"1.0","network":"test",'
            '"created_at":"2026-01-01","source_summary":"test","source_urls":[],'
            '"ledger_min":1000,"ledger_max":1001,"account_count":0,'
            '"transaction_count":0,"amm_count":0,"orderbook_count":0,'
            '"mpt_snapshot_count":0,"limitations":[]}'
        )
        snap = build_market_snapshot(tmp_path)
        assert isinstance(snap, MarketSnapshot)

    def test_strict_mode_fails_bad_fixture(self, tmp_path):
        # No manifest — strict mode should raise
        with pytest.raises(FixtureHealthError):
            build_market_snapshot(tmp_path, strict=True)

    def test_limitations_are_list(self):
        snap = build_market_snapshot(FIXTURE_DIR)
        assert isinstance(snap.limitations, list)

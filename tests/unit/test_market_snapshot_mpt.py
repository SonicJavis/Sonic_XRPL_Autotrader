"""Tests for MPT snapshot builder."""

from __future__ import annotations

import pytest
from sonic_xrpl.market.mpt_snapshot import build_mpt_snapshot


_RAW_MPT = {
    "mpt_issuance_id": "0000000000000000000000000000000000000000000000000000000000000001",
    "holders": [
        {"account": "rTrader1111111111111111111111111111", "amount": "1000"},
    ],
}


class TestMPTSnapshotBuilder:
    def test_basic_build(self):
        snap = build_mpt_snapshot(_RAW_MPT)
        assert snap.mpt_id == "0000000000000000000000000000000000000000000000000000000000000001"
        assert snap.holder_count == 1
        assert len(snap.holders_sample) == 1

    def test_holder_sample_capped_at_10(self):
        raw = {
            "mpt_issuance_id": "test123",
            "holders": [{"account": f"r{i}", "amount": "100"} for i in range(20)],
        }
        snap = build_mpt_snapshot(raw)
        assert len(snap.holders_sample) == 10
        assert snap.holder_count == 20

    def test_capability_requirements(self):
        snap = build_mpt_snapshot(_RAW_MPT)
        assert "MPTokensV1" in snap.capability_requirements

    def test_empty_holders_adds_limitation(self):
        raw = {"mpt_issuance_id": "test", "holders": []}
        snap = build_mpt_snapshot(raw)
        assert snap.holder_count == 0
        assert any("holder" in lim for lim in snap.limitations)

    def test_missing_mpt_id_adds_limitation(self):
        raw = {"holders": [{"account": "rT", "amount": "1"}]}
        snap = build_mpt_snapshot(raw)
        assert any("mpt_issuance_id" in lim for lim in snap.limitations)
        assert snap.mpt_id == "unknown"

    def test_explicit_mpt_id_overrides(self):
        snap = build_mpt_snapshot({"holders": []}, mpt_id="custom_id")
        assert snap.mpt_id == "custom_id"

    def test_frozen(self):
        snap = build_mpt_snapshot(_RAW_MPT)
        with pytest.raises((TypeError, AttributeError)):
            snap.mpt_id = "new"  # type: ignore[misc]

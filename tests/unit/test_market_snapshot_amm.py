"""Tests for AMM snapshot builder."""

from __future__ import annotations

import pytest
from sonic_xrpl.market.amm_snapshot import build_amm_snapshot, _normalise_asset_key


_RAW_AMM = {
    "amm": {
        "amount": "1000000000",
        "amount2": {"currency": "USD", "issuer": "rIssuer1111111111111111111111111111", "value": "1000"},
        "lp_token": {"currency": "039C99CD", "issuer": "rAMMAccount", "value": "100"},
        "trading_fee": 500,
        "amm_account": "rAMMAccount",
    },
    "validated": True,
}


class TestAMMSnapshotBuilder:
    def test_basic_build(self):
        snap = build_amm_snapshot(_RAW_AMM, ledger_index=1000)
        assert snap.asset_a == "XRP"
        assert snap.asset_b == "USD:rIssuer1111111111111111111111111111"
        assert snap.trading_fee == 500
        assert snap.ledger_index == 1000

    def test_trading_fee_pct(self):
        snap = build_amm_snapshot(_RAW_AMM, ledger_index=1000)
        assert snap.trading_fee_pct == pytest.approx(0.005)

    def test_lp_token_present(self):
        snap = build_amm_snapshot(_RAW_AMM, ledger_index=1000)
        assert snap.lp_token is not None
        assert snap.lp_token.get("currency") == "039C99CD"

    def test_reserves(self):
        snap = build_amm_snapshot(_RAW_AMM, ledger_index=1000)
        assert snap.reserves["asset_a_key"] == "XRP"
        assert snap.reserves["asset_b_key"] == "USD:rIssuer1111111111111111111111111111"

    def test_capability_requirements_include_amm(self):
        snap = build_amm_snapshot(_RAW_AMM, ledger_index=1000)
        assert "AMM" in snap.capability_requirements

    def test_deterministic_amm_id(self):
        snap1 = build_amm_snapshot(_RAW_AMM, ledger_index=1000)
        snap2 = build_amm_snapshot(_RAW_AMM, ledger_index=1000)
        assert snap1.amm_id == snap2.amm_id

    def test_missing_amount_adds_limitation(self):
        raw = {"amm": {"trading_fee": 500, "amm_account": "rAMM"}}
        snap = build_amm_snapshot(raw, ledger_index=1000)
        assert any("amount" in lim for lim in snap.limitations)

    def test_clawback_issuer_surfaces_limitation(self):
        issuer = "rIssuer1111111111111111111111111111"
        snap = build_amm_snapshot(_RAW_AMM, ledger_index=1000, clawback_issuers={issuer})
        # AMMClawback is ENABLED — should flag it
        assert any("clawback" in lim.lower() or "AMMClawback" in lim for lim in snap.limitations)

    def test_asset_normalise_xrp_drops(self):
        assert _normalise_asset_key("1000000000") == "XRP"

    def test_asset_normalise_iou(self):
        raw = {"currency": "USD", "issuer": "rIssuer"}
        assert _normalise_asset_key(raw) == "USD:rIssuer"

    def test_top_level_raw_unwrapped(self):
        # Without nested "amm" key
        raw = {
            "amount": "500000000",
            "amount2": {"currency": "EUR", "issuer": "rEUR"},
            "trading_fee": 1000,
            "amm_account": "rAMM2",
        }
        snap = build_amm_snapshot(raw, ledger_index=999)
        assert snap.asset_a == "XRP"
        assert snap.asset_b == "EUR:rEUR"

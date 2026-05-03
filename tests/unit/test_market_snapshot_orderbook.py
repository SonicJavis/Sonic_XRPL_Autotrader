"""Tests for orderbook snapshot builder."""

from __future__ import annotations

import pytest
from sonic_xrpl.market.orderbook_snapshot import build_orderbook_snapshot


_RAW_OB = {
    "taker_gets": "XRP",
    "taker_pays": {"currency": "USD", "issuer": "rIssuer1111111111111111111111111111"},
    "offers": [
        {
            "account": "rTrader1",
            "quality": "0.000001",
            "taker_gets": "1000000",
            "taker_pays": {"currency": "USD", "issuer": "rIssuer1111111111111111111111111111", "value": "1"},
        }
    ],
}


class TestOrderbookSnapshotBuilder:
    def test_basic_build(self):
        snap = build_orderbook_snapshot(_RAW_OB, ledger_index=1000)
        assert snap.taker_gets == "XRP"
        assert snap.taker_pays == "USD:rIssuer1111111111111111111111111111"
        assert len(snap.offers) == 1

    def test_offer_entry(self):
        snap = build_orderbook_snapshot(_RAW_OB, ledger_index=1000)
        offer = snap.offers[0]
        assert offer.account == "rTrader1"
        assert offer.quality == "0.000001"

    def test_best_bid_set(self):
        snap = build_orderbook_snapshot(_RAW_OB, ledger_index=1000)
        assert snap.best_bid is not None

    def test_spread_bps_none_single_offer(self):
        snap = build_orderbook_snapshot(_RAW_OB, ledger_index=1000)
        # Only one offer — cannot compute spread
        assert snap.spread_bps is None

    def test_spread_bps_two_offers(self):
        raw = {
            "taker_gets": "XRP",
            "taker_pays": {"currency": "USD", "issuer": "rIssuer"},
            "offers": [
                {"account": "r1", "quality": "1.0", "taker_gets": "1000000", "taker_pays": {"currency": "USD", "issuer": "rIssuer", "value": "1"}},
                {"account": "r2", "quality": "1.01", "taker_gets": "1000000", "taker_pays": {"currency": "USD", "issuer": "rIssuer", "value": "1.01"}},
            ],
        }
        snap = build_orderbook_snapshot(raw, ledger_index=1000)
        assert snap.spread_bps is not None
        assert snap.spread_bps > 0

    def test_empty_offers_adds_limitation(self):
        raw = {
            "taker_gets": "XRP",
            "taker_pays": {"currency": "USD", "issuer": "rIssuer"},
            "offers": [],
        }
        snap = build_orderbook_snapshot(raw, ledger_index=1000)
        assert any("empty" in lim for lim in snap.limitations)

    def test_deterministic_orderbook_id(self):
        snap1 = build_orderbook_snapshot(_RAW_OB, ledger_index=1000)
        snap2 = build_orderbook_snapshot(_RAW_OB, ledger_index=1000)
        assert snap1.orderbook_id == snap2.orderbook_id

    def test_depth_summary(self):
        snap = build_orderbook_snapshot(_RAW_OB, ledger_index=1000)
        assert snap.depth_summary["offer_count"] == 1
        assert snap.depth_summary["has_data"] is True

    def test_taker_gets_normalised(self):
        snap = build_orderbook_snapshot(_RAW_OB, ledger_index=1000)
        assert snap.taker_gets == "XRP"

    def test_iou_taker_gets(self):
        raw = {
            "taker_gets": {"currency": "EUR", "issuer": "rEURIssuer"},
            "taker_pays": "XRP",
            "offers": [],
        }
        snap = build_orderbook_snapshot(raw, ledger_index=999)
        assert snap.taker_gets == "EUR:rEURIssuer"
        assert snap.taker_pays == "XRP"

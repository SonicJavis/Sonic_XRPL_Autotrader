"""Tests for market snapshot models."""

from __future__ import annotations

import pytest
from sonic_xrpl.market.models import (
    AssetSnapshot,
    AssetType,
    AMMSnapshot,
    OrderbookSnapshot,
    OfferEntry,
    AccountContext,
    TrustlineContext,
    MPTSnapshot,
    MetadataSignal,
    SnapshotQuality,
    SnapshotRecommendation,
    SnapshotManifest,
    MarketSnapshot,
)


def _make_asset(key="XRP", asset_type=AssetType.XRP) -> AssetSnapshot:
    return AssetSnapshot(
        asset_key=key,
        asset_type=asset_type,
        issuer=None,
        currency="XRP",
        mpt_id=None,
        capability_requirements=[],
        risk_flags=[],
        limitations=[],
    )


def _make_quality(score=90) -> SnapshotQuality:
    rec = SnapshotRecommendation.USABLE_FOR_SIMULATION if score >= 80 else SnapshotRecommendation.USABLE_FOR_RESEARCH
    return SnapshotQuality(
        score=score,
        coverage={},
        missing_sections=[],
        stale_sections=[],
        protocol_warnings=[],
        fixture_warnings=[],
        recommendation=rec,
    )


def _make_snapshot() -> MarketSnapshot:
    quality = _make_quality()
    return MarketSnapshot(
        snapshot_id="abc123",
        created_at="2026-05-03T00:00:00+00:00",
        fixture_id="fixture001",
        ledger_index=1000,
        network="synthetic",
        assets=[_make_asset()],
        amms=[],
        orderbooks=[],
        accounts=[],
        trustlines=[],
        mpt_holders=[],
        metadata_signals=[],
        capabilities={"AMM": True},
        quality=quality,
        limitations=[],
        source_hash="deadbeef" * 8,
    )


class TestAssetSnapshot:
    def test_xrp_asset(self):
        a = _make_asset("XRP", AssetType.XRP)
        assert a.asset_key == "XRP"
        assert a.asset_type == AssetType.XRP
        assert a.issuer is None

    def test_iou_asset(self):
        a = AssetSnapshot(
            asset_key="USD:rIssuer1111",
            asset_type=AssetType.IOU,
            issuer="rIssuer1111",
            currency="USD",
            mpt_id=None,
            capability_requirements=[],
            risk_flags=[],
            limitations=[],
        )
        assert a.asset_type == AssetType.IOU
        assert a.issuer == "rIssuer1111"
        assert a.currency == "USD"

    def test_frozen_immutable(self):
        a = _make_asset()
        with pytest.raises((TypeError, AttributeError)):
            a.asset_key = "new"  # type: ignore[misc]

    def test_same_ticker_different_issuer_distinct(self):
        a1 = AssetSnapshot("USD:rIssuer1", AssetType.IOU, "rIssuer1", "USD", None, [], [], [])
        a2 = AssetSnapshot("USD:rIssuer2", AssetType.IOU, "rIssuer2", "USD", None, [], [], [])
        assert a1.asset_key != a2.asset_key
        assert a1.issuer != a2.issuer


class TestAMMSnapshot:
    def test_trading_fee_pct(self):
        amm = AMMSnapshot(
            amm_id="id1",
            asset_a="XRP",
            asset_b="USD:rIssuer",
            trading_fee=500,
            lp_token=None,
            reserves={},
            ledger_index=1000,
            capability_requirements=["AMM"],
            limitations=[],
        )
        assert amm.trading_fee_pct == pytest.approx(0.005)

    def test_trading_fee_pct_none(self):
        amm = AMMSnapshot(
            amm_id="id1",
            asset_a="XRP",
            asset_b="USD:rIssuer",
            trading_fee=None,
            lp_token=None,
            reserves={},
            ledger_index=1000,
            capability_requirements=["AMM"],
            limitations=[],
        )
        assert amm.trading_fee_pct is None

    def test_frozen(self):
        amm = AMMSnapshot("id", "XRP", "USD:r", 500, None, {}, 1000, [], [])
        with pytest.raises((TypeError, AttributeError)):
            amm.amm_id = "new"  # type: ignore[misc]


class TestOrderbookSnapshot:
    def test_basic(self):
        ob = OrderbookSnapshot(
            orderbook_id="ob1",
            taker_gets="XRP",
            taker_pays="USD:rIssuer",
            offers=[],
            best_bid=None,
            best_ask=None,
            spread_bps=None,
            depth_summary={"offer_count": 0},
            ledger_index=1000,
            limitations=["empty orderbook"],
        )
        assert ob.orderbook_id == "ob1"
        assert ob.spread_bps is None


class TestSnapshotQuality:
    def test_recommendation_simulation(self):
        q = _make_quality(90)
        assert q.recommendation == SnapshotRecommendation.USABLE_FOR_SIMULATION

    def test_recommendation_research(self):
        q = _make_quality(60)
        assert q.recommendation == SnapshotRecommendation.USABLE_FOR_RESEARCH

    def test_frozen(self):
        q = _make_quality()
        with pytest.raises((TypeError, AttributeError)):
            q.score = 50  # type: ignore[misc]


class TestMarketSnapshot:
    def test_build(self):
        s = _make_snapshot()
        assert s.snapshot_id == "abc123"
        assert s.ledger_index == 1000
        assert len(s.assets) == 1

    def test_frozen(self):
        s = _make_snapshot()
        with pytest.raises((TypeError, AttributeError)):
            s.snapshot_id = "new"  # type: ignore[misc]

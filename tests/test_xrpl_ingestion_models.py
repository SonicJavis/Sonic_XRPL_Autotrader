from datetime import datetime, timezone
from math import inf, isfinite, nan

from app.live.xrpl_ingestion_models import XRPLBookOfferSnapshot, XRPLIngestionHealth, XRPLLedgerEvent


def test_ledger_event_sanitizes_malformed_values() -> None:
    event = XRPLLedgerEvent(ledger_index=nan, ledger_hash=123, close_time="bad-time", validated=True, raw={"seed": "x", "ok": 1})

    body = event.to_dict()

    assert body["ledger_index"] == 0
    assert body["ledger_hash"] == "123"
    assert body["close_time"] is None
    assert "seed" not in body["raw"]


def test_book_snapshot_outputs_are_utc_and_finite() -> None:
    snap = XRPLBookOfferSnapshot(
        token_id=-1,
        issuer="r",
        currency="USD",
        ledger_index=inf,
        best_bid=nan,
        best_ask=inf,
        bid_depth_xrp=-1,
        ask_depth_xrp=5,
        spread_pct=nan,
        observed_at=datetime(2026, 4, 28, 12, 0),
        raw={"secret": "x", "ok": True},
    )

    body = snap.to_dict()

    assert body["token_id"] == 0
    assert body["ledger_index"] == 0
    assert body["best_bid"] == 0.0
    assert body["best_ask"] == 0.0
    assert body["observed_at"].endswith("+00:00")
    assert "secret" not in body["raw"]


def test_ingestion_health_contract_flags_are_safe() -> None:
    health = XRPLIngestionHealth(
        connected=True,
        latest_ledger_index=10,
        latest_validated_ledger_index=9,
        last_snapshot_at=datetime(2026, 4, 28, 12, 0, tzinfo=timezone.utc),
        backoff_seconds=inf,
        reason="OK",
    ).to_dict()

    assert health["is_live"] is True
    assert health["is_shadow"] is True
    assert health["is_advisory"] is True
    assert health["is_executable"] is False
    assert isfinite(float(health["backoff_seconds"]))

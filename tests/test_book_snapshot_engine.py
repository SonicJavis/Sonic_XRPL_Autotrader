from datetime import datetime, timedelta, timezone

from app.live.book_snapshot_engine import BookSnapshotEngine, BookSnapshotRequest


class FakeBookOffersClient:
    def __init__(self, responses: list[dict[str, object]]) -> None:
        self.responses = list(responses)
        self.calls = 0

    def get_book_offers(self, taker_gets, taker_pays):
        index = min(self.calls, len(self.responses) - 1)
        self.calls += 1
        return self.responses[index]


def _engine(responses: list[dict[str, object]]) -> tuple[BookSnapshotEngine, FakeBookOffersClient]:
    client = FakeBookOffersClient(responses)
    engine = BookSnapshotEngine(client, fallback_interval_ms=2500, stale_after_ms=1800)
    return engine, client


def test_snapshot_engine_pulls_on_new_ledger_and_diffs_book() -> None:
    engine, client = _engine(
        [
            {
                "offers": [
                    {"side": "bid", "quality": 0.99, "taker_gets": 99.0, "taker_pays": 100.0},
                    {"side": "ask", "quality": 1.01, "taker_gets": 100.0, "taker_pays": 101.0},
                ]
            },
            {
                "offers": [
                    {"side": "bid", "quality": 0.98, "taker_gets": 98.0, "taker_pays": 100.0},
                    {"side": "ask", "quality": 1.03, "taker_gets": 100.0, "taker_pays": 103.0},
                    {"side": "ask", "quality": 1.04, "taker_gets": 100.0, "taker_pays": 104.0},
                ]
            },
        ]
    )
    now = datetime(2026, 4, 28, 12, 0, tzinfo=timezone.utc)
    request = BookSnapshotRequest(token_key="USD.rIssuer", taker_gets="XRP", taker_pays={"currency": "USD"})

    first = engine.pull_snapshot(request=request, ledger_index=100, now=now)
    second = engine.pull_snapshot(request=request, ledger_index=101, now=now + timedelta(seconds=1))

    assert client.calls == 2
    assert first.trigger == "bootstrap"
    assert second.trigger == "new_ledger"
    assert second.diff is not None
    assert second.diff.best_bid_changed is True
    assert second.diff.best_ask_changed is True
    assert second.diff.offer_count_delta == 1


def test_snapshot_engine_uses_interval_fallback_and_marks_snapshot_stale() -> None:
    engine, client = _engine(
        [
            {
                "offers": [
                    {"side": "bid", "quality": 0.99, "taker_gets": 99.0, "taker_pays": 100.0},
                    {"side": "ask", "quality": 1.01, "taker_gets": 100.0, "taker_pays": 101.0},
                ]
            },
            {
                "offers": [
                    {"side": "bid", "quality": 0.99, "taker_gets": 99.0, "taker_pays": 100.0},
                    {"side": "ask", "quality": 1.01, "taker_gets": 100.0, "taker_pays": 101.0},
                ]
            },
        ]
    )
    now = datetime(2026, 4, 28, 12, 0, tzinfo=timezone.utc)
    request = BookSnapshotRequest(token_key="USD.rIssuer", taker_gets="XRP", taker_pays={"currency": "USD"})

    engine.pull_snapshot(request=request, ledger_index=200, now=now)
    cached = engine.pull_snapshot(request=request, ledger_index=200, now=now + timedelta(milliseconds=1700))
    refreshed = engine.pull_snapshot(
        request=request,
        ledger_index=200,
        now=now + timedelta(milliseconds=2600),
        force_interval_fallback=True,
    )

    assert client.calls == 2
    assert cached.trigger == "cached"
    assert cached.snapshot_age_ms == 1700
    assert cached.possibly_stale is False
    assert refreshed.trigger == "interval_fallback"
    assert refreshed.snapshot_age_ms == 0
    assert refreshed.possibly_stale is False


def test_snapshot_engine_marks_invalid_snapshot_when_book_is_one_sided() -> None:
    engine, _ = _engine(
        [
            {
                "offers": [
                    {"side": "ask", "quality": 1.02, "taker_gets": 100.0, "taker_pays": 102.0},
                ]
            }
        ]
    )
    request = BookSnapshotRequest(token_key="USD.rIssuer", taker_gets="XRP", taker_pays={"currency": "USD"})

    snapshot = engine.pull_snapshot(
        request=request,
        ledger_index=300,
        now=datetime(2026, 4, 28, 12, 0, tzinfo=timezone.utc),
    )

    assert snapshot.valid is False
    assert "one_sided_book" in snapshot.invalid_reasons
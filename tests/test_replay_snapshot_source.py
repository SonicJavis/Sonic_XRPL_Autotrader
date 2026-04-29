import json

from app.live.replay_snapshot_source import ReplaySnapshotSource


def test_replay_source_deterministic_output(tmp_path) -> None:
    path = tmp_path / "replay.json"
    path.write_text(
        json.dumps(
            [
                {"token_id": 1, "issuer": "r", "currency": "USD", "ledger_index": 1, "snapshot_price": 1, "snapshot_derived_liquidity": 10, "observed_possible_fill": 5, "observed_at": "2026-04-29T12:00:00+00:00"},
                {"token_id": 1, "issuer": "r", "currency": "USD", "ledger_index": 2, "snapshot_price": 1, "snapshot_derived_liquidity": 10, "observed_possible_fill": 20, "observed_at": "2026-04-29T12:00:04+00:00"},
            ]
        ),
        encoding="utf-8",
    )

    first = ReplaySnapshotSource(path)
    second = ReplaySnapshotSource(path)

    assert first.next_snapshot() == second.next_snapshot()
    capped = first.next_snapshot()
    assert capped.observed_possible_fill == capped.snapshot_derived_liquidity


def test_replay_source_skips_malformed_and_preserves_order(tmp_path) -> None:
    path = tmp_path / "replay.json"
    path.write_text(
        json.dumps(
            [
                {"bad": True},
                {"token_id": 1, "issuer": "r", "currency": "USD", "ledger_index": 2, "snapshot_price": 1, "snapshot_derived_liquidity": 10, "observed_possible_fill": 5},
                {"token_id": 1, "issuer": "r", "currency": "USD", "ledger_index": 1, "snapshot_price": 1, "snapshot_derived_liquidity": 10, "observed_possible_fill": 5},
            ]
        ),
        encoding="utf-8",
    )

    source = ReplaySnapshotSource(path)

    assert source.next_snapshot().ledger_index == 2
    assert source.next_snapshot() is None


def test_replay_source_cycles_safely(tmp_path) -> None:
    path = tmp_path / "replay.json"
    path.write_text(
        json.dumps(
            [{"token_id": 1, "issuer": "r", "currency": "USD", "ledger_index": 1, "snapshot_price": 1, "snapshot_derived_liquidity": 10, "observed_possible_fill": 5}]
        ),
        encoding="utf-8",
    )
    source = ReplaySnapshotSource(path, cycle=True)

    assert source.next_snapshot().ledger_index == 1
    assert source.next_snapshot().ledger_index == 1

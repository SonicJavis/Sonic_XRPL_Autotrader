import json
from datetime import datetime, timezone

from app.calibration.xrpl_memory_model import (
    aggregate_by_issuer,
    aggregate_by_token,
    aggregate_global,
    build_memory_samples,
)
from app.db.models import ExecutionRecord, WatchedToken


def _execution(
    *,
    token_id: int,
    observed_possible_fill: float,
    snapshot_derived_liquidity: float,
    issuer: str = "rIssuer",
    currency: str = "USD",
    path_complexity: int = 1,
    route_instability: float = 0.1,
    competition_penalty: float = 0.0,
    ledger_gap: int = 1,
    execution_price: float = 1.0,
) -> ExecutionRecord:
    now = datetime(2026, 4, 28, 12, 0, tzinfo=timezone.utc)
    return ExecutionRecord(
        id=token_id,
        token_id=token_id,
        signal_id=1,
        snapshot_id=1,
        side="BUY",
        requested_size=100.0,
        filled_size=80.0,
        fill_status="PARTIAL",
        avg_fill_price=execution_price,
        snapshot_time=now,
        signal_time=now,
        execution_time=now,
        ledger_index_snapshot=100,
        ledger_index_signal=100,
        ledger_index_execution=100 + ledger_gap,
        ledger_index_inclusion=100 + ledger_gap,
        execution_details_json=json.dumps(
            {
                "shadow": True,
                "issuer": issuer,
                "currency": currency,
                "predicted_fill_probability": 0.8,
                "observed_possible_fill": observed_possible_fill,
                "snapshot_derived_liquidity": snapshot_derived_liquidity,
                "snapshot_price": 1.0,
                "execution_price": execution_price,
                "path_complexity": path_complexity,
                "route_instability": route_instability,
                "competition_penalty": competition_penalty,
                "slippage_estimate": 0.02,
            }
        ),
    )


def test_memory_aggregates_per_token() -> None:
    samples = build_memory_samples(
        [
            _execution(token_id=1, observed_possible_fill=20.0, snapshot_derived_liquidity=100.0),
            _execution(token_id=2, observed_possible_fill=80.0, snapshot_derived_liquidity=100.0),
        ]
    )

    by_token = aggregate_by_token(samples)

    assert [row.key for row in by_token] == ["1", "2"]
    assert by_token[0].sample_count == 1
    assert by_token[1].sample_count == 1


def test_memory_aggregates_per_issuer_with_token_metadata() -> None:
    token_a = WatchedToken(id=1, issuer="rA", currency="USD", is_xrp=False)
    token_b = WatchedToken(id=2, issuer="rA", currency="EUR", is_xrp=False)
    samples = build_memory_samples(
        [
            _execution(token_id=1, issuer="", currency="", observed_possible_fill=30.0, snapshot_derived_liquidity=100.0),
            _execution(token_id=2, issuer="", currency="", observed_possible_fill=40.0, snapshot_derived_liquidity=100.0),
        ],
        tokens_by_id={1: token_a, 2: token_b},
    )

    by_issuer = aggregate_by_issuer(samples)

    assert len(by_issuer) == 1
    assert by_issuer[0].key == "rA"
    assert by_issuer[0].sample_count == 2


def test_phantom_heavy_token_is_penalised() -> None:
    samples = build_memory_samples(
        [_execution(token_id=1, observed_possible_fill=5.0, snapshot_derived_liquidity=100.0)]
    )

    aggregate = aggregate_global(samples)

    assert aggregate.avg_phantom_penalty >= 0.9
    assert aggregate.avg_liquidity_decay == 0.05
    assert aggregate.liquidity_reliability < 0.1
    assert aggregate.advisory_risk_level in {"HIGH", "CRITICAL"}


def test_memory_outputs_are_deterministic() -> None:
    executions = [
        _execution(token_id=1, observed_possible_fill=20.0, snapshot_derived_liquidity=100.0),
        _execution(token_id=2, observed_possible_fill=80.0, snapshot_derived_liquidity=100.0),
    ]

    first = aggregate_global(build_memory_samples(executions))
    second = aggregate_global(build_memory_samples(executions))

    assert first == second

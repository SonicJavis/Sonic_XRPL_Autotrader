from contextlib import contextmanager
from datetime import datetime, timezone

from sqlmodel import Session, SQLModel, create_engine

from app.live.shadow_snapshot_source import ShadowSnapshotInput, StaticShadowSnapshotSource
from app.live.xrpl_shadow_loop import XRPLShadowLoop


def _loop() -> XRPLShadowLoop:
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)

    @contextmanager
    def session_factory():
        with Session(engine) as session:
            yield session

    return XRPLShadowLoop(session_factory=session_factory, snapshot_source=StaticShadowSnapshotSource([]))


def _snapshot(**kwargs) -> ShadowSnapshotInput:
    data = {
        "token_id": 1,
        "issuer": "rIssuer",
        "currency": "USD",
        "ledger_index": 100,
        "snapshot_price": 1.0,
        "execution_price_proxy": 1.0,
        "requested_size": 100.0,
        "snapshot_derived_liquidity": 100.0,
        "observed_possible_fill": 90.0,
        "path_complexity": 1,
        "route_instability": 0.1,
        "competition_penalty": 0.1,
        "slippage_estimate": 0.01,
        "observed_at": datetime(2026, 4, 29, tzinfo=timezone.utc),
        "snapshot_quality_score": 1.0,
        "ledger_latency_proxy": 0.0,
    }
    data.update(kwargs)
    return ShadowSnapshotInput(**data)


def test_wide_spread_and_imbalance_raise_route_and_competition_pressure() -> None:
    loop = _loop()
    clean = loop.build_shadow_decision(_snapshot())
    risky = loop.build_shadow_decision(_snapshot(slippage_estimate=0.12, route_instability=0.8, competition_penalty=0.5))

    assert risky.memory_adjusted_probability < clean.memory_adjusted_probability
    assert risky.memory_adjusted_effective_size < clean.memory_adjusted_effective_size


def test_phantom_latency_path_and_low_quality_reduce_probability() -> None:
    loop = _loop()
    clean = loop.build_shadow_decision(_snapshot())
    risky = loop.build_shadow_decision(
        _snapshot(
            snapshot_derived_liquidity=500.0,
            observed_possible_fill=20.0,
            path_complexity=4,
            ledger_latency_proxy=7000.0,
            snapshot_quality_score=0.35,
            slippage_estimate=0.15,
        )
    )

    assert risky.memory_adjusted_probability < clean.memory_adjusted_probability
    assert risky.drift_adjusted_ev < clean.drift_adjusted_ev

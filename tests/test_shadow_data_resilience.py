import json
from datetime import datetime, timezone
from math import inf, isnan, nan

from fastapi.testclient import TestClient
from sqlmodel import delete

from app.db.models import ShadowDecisionRecord
from app.api.routes_live_shadow import _row_to_dict
from app.live.shadow_snapshot_source import ShadowSnapshotInput, StaticShadowSnapshotSource
from app.main import create_app


def _clear(app) -> None:
    with app.state.container.session_factory() as session:
        session.exec(delete(ShadowDecisionRecord))
        session.commit()


def test_malformed_json_falls_back_to_safe_values() -> None:
    app = create_app()
    _clear(app)
    with app.state.container.session_factory() as session:
        session.add(
            ShadowDecisionRecord(
                token_id=1,
                observed_at=datetime(2026, 4, 28, 12, 0, tzinfo=timezone.utc),
                risk_flags_json="{bad-json",
                calibration_snapshot_json="[not-a-dict]",
                memory_adjusted_probability=0.4,
                memory_adjusted_effective_size=10.0,
                drift_adjusted_ev=0.1,
            )
        )
        session.commit()

    body = TestClient(app).get("/live/shadow/decisions").json()

    assert body["decisions"][0]["risk_flags"] == []
    assert body["decisions"][0]["calibration_snapshot"] == {}


def test_invalid_numeric_snapshot_inputs_never_crash_and_are_sanitized() -> None:
    source = StaticShadowSnapshotSource(
        [
            ShadowSnapshotInput(
                token_id=1,
                issuer="rBad",
                currency="USD",
                ledger_index=nan,
                snapshot_price=inf,
                execution_price_proxy=-inf,
                requested_size=-10.0,
                snapshot_derived_liquidity=nan,
                observed_possible_fill=inf,
                path_complexity=nan,
                route_instability=inf,
                competition_penalty=nan,
                slippage_estimate=-1.0,
                observed_at="not-a-date",
            )
        ]
    )

    tick = source.next_snapshot()

    assert tick is not None
    assert tick.ledger_index == 0
    assert tick.requested_size == 0.0
    assert tick.snapshot_derived_liquidity == 0.0
    assert tick.route_instability == 0.0
    assert tick.competition_penalty == 0.0
    assert not isnan(tick.observed_at.timestamp())


def test_api_float_fallbacks_for_nan_and_inf() -> None:
    row = _row_to_dict(
        ShadowDecisionRecord(
            id=1,
            token_id=1,
            observed_at=datetime(2026, 4, 28, 12, 0, tzinfo=timezone.utc),
            requested_size=nan,
            latency_path_probability=inf,
            memory_adjusted_probability=-inf,
            effective_size=nan,
            memory_adjusted_effective_size=inf,
            uncertainty_adjusted_value=nan,
            drift_adjusted_ev=-inf,
            risk_flags_json=json.dumps(["RISK"]),
            calibration_snapshot_json=json.dumps({"ok": True}),
        )
    )

    assert row["requested_size"] == 0.0
    assert row["latency_path_probability"] == 0.0
    assert row["memory_adjusted_probability"] == 0.0
    assert row["effective_size"] == 0.0

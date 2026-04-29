from datetime import datetime, timezone

from fastapi.testclient import TestClient
from sqlmodel import delete

from app.db.models import ShadowValidationRecord
from app.main import create_app


def test_shadow_validation_empty_state_safe_and_bounded_limits() -> None:
    app = create_app()
    with app.state.container.session_factory() as session:
        session.exec(delete(ShadowValidationRecord))
        session.commit()
    client = TestClient(app)

    summary = client.get("/validation/shadow/summary?limit=0").json()
    results = client.get("/validation/shadow/results?limit=999999").json()

    assert summary["sample_count"] == 0
    assert summary["limit"] == 1
    assert summary["is_shadow"] is True
    assert summary["is_advisory"] is True
    assert summary["is_executable"] is False
    assert summary["is_truth"] is False
    assert "xrpl_warning" in summary
    assert results["limit"] == 5000
    assert results["results"] == []


def test_shadow_validation_populated_summary_and_results() -> None:
    app = create_app()
    with app.state.container.session_factory() as session:
        session.exec(delete(ShadowValidationRecord))
        session.add(
            ShadowValidationRecord(
                decision_id=1,
                token_id=7,
                issuer="rIssuer",
                predicted_regime="STABLE_SHADOW",
                disagreement_score=0.4,
                brier_score=0.25,
                overconfidence_flag=True,
                attribution="liquidity_illusion",
                created_at=datetime(2026, 4, 29, tzinfo=timezone.utc),
            )
        )
        session.add(
            ShadowValidationRecord(
                decision_id=2,
                token_id=8,
                issuer="rIssuer2",
                predicted_regime="ROUTE_UNSTABLE",
                disagreement_score=0.2,
                brier_score=0.09,
                underconfidence_flag=True,
                attribution="path_instability",
                created_at=datetime(2026, 4, 29, tzinfo=timezone.utc),
            )
        )
        session.commit()
    client = TestClient(app)

    summary = client.get("/validation/shadow/summary").json()
    results = client.get("/validation/shadow/results").json()

    assert summary["sample_count"] == 2
    assert summary["avg_disagreement_score"] == 0.3
    assert summary["avg_brier_score"] == 0.17
    assert summary["overconfidence_rate"] == 0.5
    assert summary["underconfidence_rate"] == 0.5
    assert summary["attribution_breakdown"] == {"liquidity_illusion": 1, "path_instability": 1}
    assert results["count"] == 2
    assert results["results"][0]["is_truth"] is False

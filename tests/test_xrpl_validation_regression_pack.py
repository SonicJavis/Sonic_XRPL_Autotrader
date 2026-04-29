import json
from datetime import datetime, timezone
from math import isfinite
from pathlib import Path

from app.live.shadow_snapshot_source import ShadowSnapshotInput
from app.validation.xrpl_outcome_window_builder import build_outcome_windows
from app.validation.xrpl_validation_engine import compare_prediction_to_window
from app.validation.xrpl_validation_models import XRPLShadowPrediction


def test_regression_pack_windows_and_results_are_deterministic() -> None:
    snapshots = _load_fixture()
    first_windows = [window.to_dict() for window in build_outcome_windows(snapshots, window_size=3)]
    second_windows = [window.to_dict() for window in build_outcome_windows(list(reversed(snapshots)), window_size=3)]

    assert first_windows == second_windows
    first_results = [result.to_dict() for result in _validation_results(snapshots)]
    second_results = [result.to_dict() for result in _validation_results(list(reversed(snapshots)))]
    assert first_results == second_results
    assert all(_finite_json(row) for row in first_results)


def test_regression_pack_detection_and_attribution_stable() -> None:
    results = _validation_results(_load_fixture())
    attribution = {result.error_attribution for result in results}

    assert any(result.overconfidence_flag for result in results)
    assert any(result.underconfidence_flag for result in results)
    assert any(result.liquidity_disappearance > 0.0 for result in results)
    assert any(result.path_failure_rate > 0.0 for result in results)
    assert any(result.competition_miss_rate > 0.0 for result in results)
    assert attribution >= {"liquidity_illusion", "path_instability", "competition", "regime_shift"}


def test_regression_fixture_and_outputs_avoid_unsafe_language() -> None:
    text = Path("data/xrpl_validation_regression_snapshots.json").read_text(encoding="utf-8").lower()
    outputs = json.dumps([result.to_dict() for result in _validation_results(_load_fixture())], sort_keys=True).lower()
    for phrase in _UNSAFE_PHRASES:
        assert phrase not in text
        assert phrase not in outputs


def _validation_results(snapshots: list[ShadowSnapshotInput]):
    windows = {(window.token_id, window.issuer, window.start_ledger - 1): window for window in build_outcome_windows(snapshots, window_size=3)}
    cases = [
        _prediction(22, "rPhantom", 2000, probability=0.9, regime="COMPETITION_SPIKE", liquidity=400.0, competition=0.0),
        _prediction(11, "rNormal", 1000, probability=0.25, regime="ROUTE_UNSTABLE", liquidity=70.0, competition=1.0),
        _prediction(11, "rNormal", 1000, probability=0.6, regime="STABLE_SHADOW", liquidity=75.0),
        _prediction(11, "rNormal", 1000, probability=0.75, regime="DRIFT_RISK", liquidity=75.0),
        _prediction(44, "rUnder", 4000, probability=0.1, regime="STABLE_SHADOW", liquidity=90.0),
        _prediction(55, "rCompetition", 5000, probability=0.5, regime="COMPETITION_SPIKE", liquidity=50.0, competition=0.0),
    ]
    results = []
    for prediction in cases:
        window = windows[(prediction.token_id, prediction.issuer, prediction.ledger_index_start)]
        results.append(compare_prediction_to_window(prediction, window))
    return results


def _prediction(token_id: int, issuer: str, ledger: int, *, probability: float, regime: str, liquidity: float, competition: float = 0.5):
    return XRPLShadowPrediction(
        decision_id=ledger,
        token_id=token_id,
        issuer=issuer,
        ledger_index_start=ledger,
        predicted_probability=probability,
        predicted_effective_size=probability * 100.0,
        predicted_ev=probability * 10.0,
        predicted_path_complexity=1,
        predicted_route_instability=0.1,
        predicted_competition_penalty=competition,
        predicted_regime=regime,
        predicted_confidence=probability,
        created_at=datetime(2026, 4, 29, tzinfo=timezone.utc),
        requested_size=100.0,
        predicted_liquidity=liquidity,
        predicted_latency_ms=4000.0,
    )


def _load_fixture() -> list[ShadowSnapshotInput]:
    payload = json.loads(Path("data/xrpl_validation_regression_snapshots.json").read_text(encoding="utf-8"))
    return [
        ShadowSnapshotInput(
            token_id=int(row["token_id"]),
            issuer=str(row["issuer"]),
            currency=str(row["currency"]),
            ledger_index=int(row["ledger_index"]),
            snapshot_price=float(row["snapshot_price"]),
            execution_price_proxy=float(row["execution_price_proxy"]),
            requested_size=float(row["requested_size"]),
            snapshot_derived_liquidity=float(row["snapshot_derived_liquidity"]),
            observed_possible_fill=float(row["observed_possible_fill"]),
            path_complexity=int(row["path_complexity"]),
            route_instability=float(row["route_instability"]),
            competition_penalty=float(row["competition_penalty"]),
            slippage_estimate=float(row["slippage_estimate"]),
            observed_at=datetime.fromisoformat(str(row["observed_at"])),
            snapshot_quality_score=float(row.get("snapshot_quality_score", 1.0)),
            ledger_latency_proxy=float(row.get("ledger_latency_proxy", 0.0)),
        )
        for row in payload
    ]


def _finite_json(value) -> bool:
    if isinstance(value, dict):
        return all(_finite_json(item) for item in value.values())
    if isinstance(value, list):
        return all(_finite_json(item) for item in value)
    if isinstance(value, float):
        return isfinite(value)
    return True


_UNSAFE_PHRASES = (
    "true fill",
    "actual fill",
    "guaranteed fill",
    "guaranteed execution",
    "real execution",
    "executable truth",
    "proven executable",
    "confirmed fill",
)

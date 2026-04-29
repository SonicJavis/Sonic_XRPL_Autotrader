import json
from math import isfinite
from pathlib import Path

from scripts.xrpl_shadow_dry_run import run_dry_run


def test_validate_safe_with_regression_fixture(tmp_path) -> None:
    summary = run_dry_run(
        replay_path=Path("data/xrpl_validation_regression_snapshots.json"),
        ticks=20,
        database_url=f"sqlite:///{tmp_path / 'validation.db'}",
        validate=True,
    )

    assert _required_validation_keys() <= set(summary)
    assert summary["is_shadow"] is True
    assert summary["is_advisory"] is True
    assert summary["is_executable"] is False
    assert summary["is_truth"] is False
    assert _finite_json(summary)
    assert list(summary["attribution_breakdown"]) == sorted(summary["attribution_breakdown"])


def test_validate_with_no_windows_returns_safe_zeros(tmp_path) -> None:
    fixture = tmp_path / "single.json"
    fixture.write_text(
        json.dumps(
            [
                {
                    "token_id": 1,
                    "issuer": "rIssuer",
                    "currency": "USD",
                    "ledger_index": 1,
                    "snapshot_price": 1.0,
                    "execution_price_proxy": 1.0,
                    "requested_size": 100.0,
                    "snapshot_derived_liquidity": 100.0,
                    "observed_possible_fill": 50.0,
                    "path_complexity": 1,
                    "route_instability": 0.1,
                    "competition_penalty": 0.1,
                    "slippage_estimate": 0.01,
                    "observed_at": "2026-04-29T00:00:00+00:00",
                }
            ]
        ),
        encoding="utf-8",
    )

    summary = run_dry_run(replay_path=fixture, ticks=5, database_url=f"sqlite:///{tmp_path / 'empty.db'}", validate=True)

    assert summary["avg_disagreement_score"] == 0.0
    assert summary["avg_brier_score"] == 0.0
    assert summary["overconfidence_rate"] == 0.0
    assert summary["underconfidence_rate"] == 0.0
    assert summary["attribution_breakdown"] == {}


def test_dry_run_script_source_has_no_forbidden_operations() -> None:
    source = Path("scripts/xrpl_shadow_dry_run.py").read_text(encoding="utf-8")
    for term in ("submit", "sign", "wallet", "OfferCreate", "Payment", "autofill"):
        assert term not in source


def _required_validation_keys() -> set[str]:
    return {
        "avg_disagreement_score",
        "avg_brier_score",
        "overconfidence_rate",
        "underconfidence_rate",
        "attribution_breakdown",
        "is_shadow",
        "is_advisory",
        "is_executable",
        "is_truth",
    }


def _finite_json(value) -> bool:
    if isinstance(value, dict):
        return all(_finite_json(item) for item in value.values())
    if isinstance(value, list):
        return all(_finite_json(item) for item in value)
    if isinstance(value, float):
        return isfinite(value)
    return True

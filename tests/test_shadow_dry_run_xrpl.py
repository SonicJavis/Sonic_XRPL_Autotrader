from pathlib import Path

from scripts.xrpl_shadow_dry_run import run_dry_run


def test_replay_dry_run_returns_safe_summary(tmp_path) -> None:
    db = tmp_path / "dry_run.db"

    summary = run_dry_run(
        replay_path=Path("data/xrpl_replay_regression_snapshots.json"),
        ticks=10,
        database_url=f"sqlite:///{db}",
    )

    assert summary["ticks_processed"] == 10
    assert summary["decisions_stored"] > 0
    assert summary["skipped_snapshots"] >= 0
    assert summary["rejected_snapshots"] >= 0
    assert summary["avg_probability"] >= 0.0
    assert summary["avg_phantom_penalty"] >= 0.0
    assert summary["avg_competition_penalty"] >= 0.0
    assert summary["is_shadow"] is True
    assert summary["is_advisory"] is True
    assert summary["is_executable"] is False
    assert summary["is_truth"] is False


def test_replay_dry_run_validate_outputs_window_metrics(tmp_path) -> None:
    db = tmp_path / "dry_run_validate.db"

    summary = run_dry_run(
        replay_path=Path("data/xrpl_replay_regression_snapshots.json"),
        ticks=10,
        database_url=f"sqlite:///{db}",
        validate=True,
    )

    assert "avg_disagreement_score" in summary
    assert "avg_brier_score" in summary
    assert "overconfidence_rate" in summary
    assert "underconfidence_rate" in summary
    assert "attribution_breakdown" in summary
    assert summary["avg_disagreement_score"] >= 0.0

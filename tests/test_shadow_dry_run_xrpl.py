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

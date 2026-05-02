"""Phase 44: Walk-Forward Replay Report Writer.

Writes all outputs to reports/phase44/<timestamp>/. Never modifies source files.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from .models import (
    PaperStrategyLifecycleRecommendation,
    StrategyDegradationWarning,
    StrategyStabilityProfile,
    WalkForwardEvaluation,
    WalkForwardReplaySummary,
    WalkForwardWindow,
)

REPORT_SAFETY_NOTE = (
    "This report is paper-only. It does not contain signing logic,"
    " private keys, wallet references, or submission primitives."
)


def write_report(
    output_dir: Path,
    windows: List[WalkForwardWindow],
    evaluations: List[WalkForwardEvaluation],
    profiles: List[StrategyStabilityProfile],
    warnings: List[StrategyDegradationWarning],
    recommendations: List[PaperStrategyLifecycleRecommendation],
    summary: WalkForwardReplaySummary,
    dataset: Dict[str, Any],
    config: Dict[str, Any],
) -> Path:
    """Write all Phase 44 outputs. Returns the timestamped output path."""
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = output_dir / "reports" / "phase44" / ts
    out_path.mkdir(parents=True, exist_ok=True)

    _write_jsonl(out_path / "walk_forward_windows.jsonl", [w.to_dict() for w in windows])
    _write_jsonl(out_path / "walk_forward_evaluations.jsonl", [e.to_dict() for e in evaluations])
    _write_jsonl(out_path / "strategy_stability_profiles.jsonl", [p.to_dict() for p in profiles])
    _write_jsonl(out_path / "strategy_degradation_warnings.jsonl", [w.to_dict() for w in warnings])
    _write_jsonl(
        out_path / "paper_strategy_lifecycle_recommendations.jsonl",
        [r.to_dict() for r in recommendations],
    )

    summary_path = out_path / "walk_forward_replay_summary.json"
    summary_path.write_text(json.dumps(summary.to_dict(), indent=2), encoding="utf-8")

    md_path = out_path / "walk_forward_replay_report.md"
    md_path.write_text(
        _render_markdown(windows, evaluations, profiles, warnings, recommendations, summary, dataset, config),
        encoding="utf-8",
    )

    return out_path


def _write_jsonl(path: Path, records: List[Dict[str, Any]]) -> None:
    lines = [json.dumps(r) for r in records]
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def _render_markdown(
    windows: List[WalkForwardWindow],
    evaluations: List[WalkForwardEvaluation],
    profiles: List[StrategyStabilityProfile],
    warnings: List[StrategyDegradationWarning],
    recommendations: List[PaperStrategyLifecycleRecommendation],
    summary: WalkForwardReplaySummary,
    dataset: Dict[str, Any],
    config: Dict[str, Any],
) -> str:
    manifest = dataset.get("manifest", {})
    lines: List[str] = []

    lines.append("# Phase 44: Walk-Forward Backtest Replay Report")
    lines.append("")

    lines.append("## 1. Research Sources Checked")
    lines.append("- XRPL Known Amendments (rippled 3.1.2)")
    lines.append("- Clio 2.1.0 API docs")
    lines.append("- Phase 42 Backtest Dataset Builder output")
    lines.append("- Phase 43 Dataset-Driven Strategy Tournament output (optional)")
    lines.append("- Phase 41 Read-Only Data Adapter exports")
    lines.append("")
    lines.append(f"Safety note: {REPORT_SAFETY_NOTE}")
    lines.append("")

    lines.append("## 2. Walk-Forward Replay Summary")
    lines.append(f"- Dataset ID: {summary.dataset_id}")
    lines.append(f"- Dataset Quality Score: {summary.dataset_quality_score}/100")
    lines.append(f"- Strategies Evaluated: {summary.strategies_evaluated}")
    lines.append(f"- Walk-Forward Windows: {summary.walk_forward_windows}")
    lines.append(f"- Total Evaluations: {summary.total_evaluations}")
    lines.append(f"- Stable Strategies: {summary.stable_strategy_count}")
    lines.append(f"- Watch Strategies: {summary.watch_strategy_count}")
    lines.append(f"- Unstable Strategies: {summary.unstable_strategy_count}")
    lines.append(f"- Insufficient Data: {summary.insufficient_data_count}")
    lines.append(f"- Critical Warnings: {summary.critical_warning_count}")
    lines.append(f"- Live Trading Readiness: {summary.live_trading_readiness}")
    lines.append("")

    lines.append("## 3. Dataset Quality Context")
    lines.append(f"Quality Score: {summary.dataset_quality_score}/100")
    for lim in summary.limitations:
        lines.append(f"- {lim}")
    lines.append("")

    lines.append("## 4. Walk-Forward Windows")
    if not windows:
        lines.append("No walk-forward windows were built (insufficient Phase 42 data).")
    for w in windows:
        lines.append(
            f"- Window #{w.chronological_order}: eval_window={w.evaluation_window_id[:12]}..."
            f" train_count={w.training_record_count} eval_count={w.evaluation_record_count}"
        )
    lines.append("")

    lines.append("## 5. Strategy Stability Profiles")
    for p in profiles:
        lines.append(
            f"- **{p.strategy_id[:16]}...**: stability_score={p.stability_score},"
            f" band={p.stability_band}, windows={p.windows_evaluated},"
            f" mean_score={p.mean_evaluation_score}, volatility={p.score_volatility},"
            f" degradations={p.degradation_count}, confidence={p.confidence_band}"
        )
    lines.append("")

    lines.append("## 6. Score Trajectories")
    by_strategy: Dict[str, List[WalkForwardEvaluation]] = {}
    for ev in evaluations:
        by_strategy.setdefault(ev.strategy_id, []).append(ev)
    for sid, evals in by_strategy.items():
        sorted_evals = sorted(evals, key=lambda e: e.chronological_order)
        scores_str = ", ".join(str(e.evaluation_score) for e in sorted_evals)
        lines.append(f"- {sid[:16]}...: [{scores_str}]")
    lines.append("")

    lines.append("## 7. Degradation Warnings")
    if not warnings:
        lines.append("No degradation warnings detected.")
    for w in warnings:
        lines.append(
            f"- [{w.severity.upper()}] {w.warning_type} (strategy={w.strategy_id[:12]}...):"
            f" {'; '.join(w.evidence)}"
        )
    lines.append("")

    lines.append("## 8. Lifecycle Recommendations")
    for r in recommendations:
        lines.append(
            f"- **{r.strategy_id[:16]}...**: {r.lifecycle_status} — {r.reason}"
        )
        lines.append(f"  - Required human action: {r.required_human_action}")
    lines.append("")

    lines.append("## 9. Human Review Checklist")
    lines.append("- [ ] Verify dataset quality score >= 60")
    lines.append("- [ ] Confirm no future leakage in records")
    lines.append("- [ ] Review all critical degradation warnings")
    lines.append("- [ ] Approve or deny lifecycle status changes manually")
    lines.append("- [ ] Confirm live trading remains forbidden")
    lines.append("")

    lines.append("## 10. Protocol Context / Amendment Safety Notes")
    lines.append("- XRPL AMM (XLS-30d) amendment: supported in read-only mode")
    lines.append("- Xahau hooks: not supported; Xahau context triggers penalty and warning")
    lines.append("- Unsupported Batch context: triggers critical warning and stability cap")
    lines.append("- All data is read from static offline snapshots; no live node queries")
    lines.append("")

    lines.append("## 11. Limitations")
    lines.append("- All evaluations are paper-only; no real PnL is guaranteed")
    lines.append("- Signal quality depends on dataset completeness")
    lines.append("- Small samples (<5 records) produce unreliable scores")
    lines.append("- This report cannot predict future market behavior")
    lines.append("- Walk-forward windows require at least 2 Phase 42 backtest windows")
    lines.append("")

    lines.append("## 12. Why Live Trading Is Still Forbidden")
    lines.append("- No readiness gates have been fully passed")
    lines.append("- Human governance approval not granted")
    lines.append("- System is paper-only; 0/100 live trading readiness")
    lines.append(f"- {REPORT_SAFETY_NOTE}")
    lines.append("- No network calls are made; all data is offline and static")
    lines.append("")

    lines.append("## 13. Next Phase Recommendation")
    lines.append("- Collect more real XRPL historical data via Phase 41 adapters")
    lines.append("- Improve dataset quality to >= 70/100 before re-running replay")
    lines.append("- After multiple stable paper evaluations, consider Phase 45 planning")
    lines.append("- Do NOT advance to any live environment without explicit human approval")
    lines.append("")

    return "\n".join(lines)

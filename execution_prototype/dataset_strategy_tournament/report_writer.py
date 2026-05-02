from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .models import (
    DatasetStrategyDefinition,
    DatasetTournamentSummary,
    OverfittingWarning,
    StrategyGeneralizationScore,
    StrategyTournamentResult,
    StrategyWindowEvaluation,
)
from .recommendations import RecommendationEngine

REPORT_SAFETY_NOTE = "It does not contain signing logic, private keys, or submission primitives"


class ReportWriter:
    def write_all(
        self,
        output_dir: Path,
        strategy_defs: List[DatasetStrategyDefinition],
        window_evals: List[StrategyWindowEvaluation],
        gen_scores: List[StrategyGeneralizationScore],
        overfitting_warnings: List[OverfittingWarning],
        tournament_results: List[StrategyTournamentResult],
        summary: DatasetTournamentSummary,
    ) -> Path:
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        out_path = output_dir / ts
        out_path.mkdir(parents=True, exist_ok=True)

        self._write_jsonl(out_path / "dataset_strategy_definitions.jsonl", [d.to_dict() for d in strategy_defs])
        self._write_jsonl(out_path / "strategy_window_evaluations.jsonl", [e.to_dict() for e in window_evals])
        self._write_jsonl(out_path / "strategy_generalization_scores.jsonl", [g.to_dict() for g in gen_scores])
        self._write_jsonl(out_path / "overfitting_warnings.jsonl", [w.to_dict() for w in overfitting_warnings])
        self._write_jsonl(out_path / "dataset_strategy_tournament_results.jsonl", [r.to_dict() for r in tournament_results])

        summary_path = out_path / "dataset_strategy_tournament_summary.json"
        summary_path.write_text(json.dumps(summary.to_dict(), indent=2))

        rec_engine = RecommendationEngine()
        recommendations = rec_engine.generate_recommendations(
            tournament_results, overfitting_warnings, summary
        )

        md_path = out_path / "dataset_strategy_tournament_report.md"
        md_path.write_text(self._render_markdown(
            strategy_defs, window_evals, gen_scores, overfitting_warnings,
            tournament_results, summary, recommendations
        ))

        return out_path

    def _write_jsonl(self, path: Path, records: List[Dict[str, Any]]) -> None:
        lines = [json.dumps(r) for r in records]
        path.write_text("\n".join(lines) + ("\n" if lines else ""))

    def _render_markdown(
        self,
        strategy_defs: List[DatasetStrategyDefinition],
        window_evals: List[StrategyWindowEvaluation],
        gen_scores: List[StrategyGeneralizationScore],
        overfitting_warnings: List[OverfittingWarning],
        tournament_results: List[StrategyTournamentResult],
        summary: DatasetTournamentSummary,
        recommendations: List[str],
    ) -> str:
        lines: List[str] = []
        lines.append("# Phase 43: Dataset Strategy Tournament Report")
        lines.append("")

        lines.append("## 1. Research Sources Checked")
        lines.append("- XRPL Known Amendments (rippled 3.1.2)")
        lines.append("- Clio 2.1.0 API docs")
        lines.append("- Phase 42 Backtest Dataset Builder output")
        lines.append("- Phase 40 Market Fixture Engine snapshots")
        lines.append("- Phase 41 Read-Only Data Adapter exports")
        lines.append("- Phase 37 Strategy Performance reports (optional)")
        lines.append("")
        lines.append(f"Safety note: {REPORT_SAFETY_NOTE}")
        lines.append("")

        lines.append("## 2. Dataset Tournament Summary")
        lines.append(f"- Dataset ID: {summary.dataset_id}")
        lines.append(f"- Dataset Quality Score: {summary.dataset_quality_score}/100")
        lines.append(f"- Strategies Evaluated: {summary.strategies_evaluated}")
        lines.append(f"- Windows Evaluated: {summary.windows_evaluated}")
        lines.append(f"- Best Strategy: {summary.best_strategy_id or 'N/A'}")
        lines.append(f"- Worst Strategy: {summary.worst_strategy_id or 'N/A'}")
        lines.append(f"- Critical Warnings: {summary.critical_warning_count}")
        lines.append(f"- Live Trading Readiness: {summary.live_trading_readiness}")
        lines.append("")

        lines.append("## 3. Dataset Quality Context")
        lines.append(f"Quality Score: {summary.dataset_quality_score}/100")
        for lim in summary.limitations:
            lines.append(f"- {lim}")
        lines.append("")

        lines.append("## 4. Strategies Evaluated")
        for sd in strategy_defs:
            lines.append(f"- **{sd.strategy_name}** (family: {sd.strategy_family}, v{sd.strategy_version})")
            lines.append(f"  - {sd.description}")
        lines.append("")

        lines.append("## 5. Split-by-Split Performance")
        eval_by_strat: Dict[str, List[StrategyWindowEvaluation]] = {}
        for ev in window_evals:
            eval_by_strat.setdefault(ev.strategy_id, []).append(ev)
        for strat_id, evals in eval_by_strat.items():
            lines.append(f"### Strategy: {strat_id[:16]}...")
            for ev in evals:
                lines.append(
                    f"- {ev.window_type}: records={ev.records_evaluated}, "
                    f"signals={ev.signals_generated}, "
                    f"wins={ev.win_count}, losses={ev.loss_count}, "
                    f"quality_score={ev.quality_weighted_score}"
                )
            lines.append("")

        lines.append("## 6. Generalization Scores")
        for gs in gen_scores:
            lines.append(f"- strategy={gs.strategy_id[:16]}...: train={gs.train_score}, val={gs.validation_score}, test={gs.test_score}, holdout={gs.holdout_score}, confidence={gs.confidence_band}")
        lines.append("")

        lines.append("## 7. Robustness Scores")
        for gs in gen_scores:
            lines.append(f"- strategy={gs.strategy_id[:16]}...: robustness={gs.robustness_score}, overfitting={gs.overfitting_score}")
        lines.append("")

        lines.append("## 8. Overfitting Warnings")
        if not overfitting_warnings:
            lines.append("No warnings detected.")
        for w in overfitting_warnings:
            lines.append(f"- [{w.severity.upper()}] {w.warning_type}: {'; '.join(w.evidence)}")
        lines.append("")

        lines.append("## 9. Promotion / Rejection Recommendations")
        for rec in recommendations:
            lines.append(f"- {rec}")
        lines.append("")

        lines.append("## 10. Human Review Checklist")
        lines.append("- [ ] Verify dataset quality score >= 60")
        lines.append("- [ ] Confirm no future leakage in records")
        lines.append("- [ ] Review all critical warnings")
        lines.append("- [ ] Approve any paper promotions manually")
        lines.append("- [ ] Confirm live trading remains forbidden")
        lines.append("")

        lines.append("## 11. Protocol Context / Amendment Safety Notes")
        lines.append("- XRPL AMM (XLS-30d) amendment: supported in read-only mode")
        lines.append("- Xahau hooks: not supported; Xahau context triggers penalty")
        lines.append("- Unsupported batch context: triggers penalty")
        lines.append("- All data is read from static offline snapshots; no live node queries")
        lines.append("")

        lines.append("## 12. Limitations")
        lines.append("- All evaluations are paper-only; no real PnL is guaranteed")
        lines.append("- Signal quality depends on dataset completeness")
        lines.append("- Small samples (<10 signals) produce unreliable scores")
        lines.append("- This report cannot predict future market behavior")
        lines.append("")

        lines.append("## 13. Why Live Trading Is Still Forbidden")
        lines.append("- No readiness gates have been fully passed")
        lines.append("- Human governance approval not granted")
        lines.append("- System is paper-only; 0/100 live trading readiness")
        lines.append(f"- {REPORT_SAFETY_NOTE}")
        lines.append("- No network calls are made; all data is offline and static")
        lines.append("")

        lines.append("## 14. Next Phase Recommendation")
        lines.append("- Collect more real XRPL historical data via Phase 41 adapters")
        lines.append("- Improve dataset quality to >= 70/100 before re-running tournament")
        lines.append("- After multiple paper promotions, consider Phase 44: Extended Paper Validation")
        lines.append("- Do NOT advance to any live environment without explicit human approval")
        lines.append("")

        return "\n".join(lines)

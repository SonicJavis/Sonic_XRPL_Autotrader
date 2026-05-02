from __future__ import annotations
from typing import List

from .models import DatasetTournamentSummary, OverfittingWarning, StrategyTournamentResult

PAPER_ONLY_DISCLAIMER = (
    "All promotions are paper-only. No live execution is permitted. "
    "READ-ONLY. NO WALLET. NO SIGNING. NO SUBMISSION."
)
LIVE_TRADING_PROHIBITION = (
    "Live trading remains at 0/100 readiness. "
    "No automated live action is permitted under any circumstance."
)


class RecommendationEngine:
    def generate_recommendations(
        self,
        results: List[StrategyTournamentResult],
        warnings: List[OverfittingWarning],
        summary: DatasetTournamentSummary,
    ) -> List[str]:
        recs: List[str] = [PAPER_ONLY_DISCLAIMER, LIVE_TRADING_PROHIBITION]

        for result in results:
            if result.promotion_status == "promote_to_more_paper_tests":
                recs.append(
                    f"PROMOTE (paper): strategy_id={result.strategy_id[:8]}... "
                    f"rank={result.rank}, overall_score={result.overall_score}. "
                    f"Reason: {result.promotion_reason}"
                )
            elif result.promotion_status == "reject_for_now":
                recs.append(
                    f"REJECT: strategy_id={result.strategy_id[:8]}... "
                    f"rank={result.rank}, overall_score={result.overall_score}. "
                    f"Reason: {result.promotion_reason}"
                )
            elif result.promotion_status == "keep_under_review":
                recs.append(
                    f"REVIEW: strategy_id={result.strategy_id[:8]}... "
                    f"rank={result.rank}, overall_score={result.overall_score}. "
                    f"Reason: {result.promotion_reason}"
                )
            else:
                recs.append(
                    f"INSUFFICIENT DATA: strategy_id={result.strategy_id[:8]}... "
                    f"rank={result.rank}. Collect more records."
                )

        critical_warnings = [w for w in warnings if w.severity == "critical"]
        if critical_warnings:
            recs.append(
                f"CRITICAL: {len(critical_warnings)} critical overfitting warning(s) detected. "
                "Human review mandatory before any further testing."
            )

        if summary.dataset_quality_score < 60:
            recs.append(
                f"Dataset quality ({summary.dataset_quality_score}/100) is below threshold. "
                "Improve data collection pipeline before re-running tournament."
            )

        recs.append(
            f"Live trading readiness: {summary.live_trading_readiness}. "
            "This will not change until all readiness gates are passed and human approval is granted."
        )

        return recs

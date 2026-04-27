from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from sqlmodel import Session, select

from app.config import Settings
from app.db.models import AlphaSignal, MarketSnapshot, PaperTradeOutcome


class PerformanceEngine:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def summary(self, session: Session, limit: int = 200) -> dict[str, float | int]:
        outcomes = session.exec(select(PaperTradeOutcome).order_by(PaperTradeOutcome.id.desc()).limit(limit)).all()
        if not outcomes:
            return {
                "trades": 0,
                "win_rate": 0.0,
                "avg_pnl": 0.0,
                "avg_slippage_error": 0.0,
                "fill_rate": 0.0,
                "reject_accuracy": 0.0,
            }

        pnl_rows = [float(row.pnl_xrp or 0.0) for row in outcomes if row.pnl_xrp is not None]
        wins = sum(1 for p in pnl_rows if p > 0)
        slippage_errors = [abs(float(row.actual_slippage_pct) - float(row.expected_slippage_pct)) for row in outcomes]
        fill_rate = sum(1 for row in outcomes if row.fill_success) / max(1, len(outcomes))

        return {
            "trades": len(outcomes),
            "win_rate": wins / max(1, len(pnl_rows)),
            "avg_pnl": sum(pnl_rows) / max(1, len(pnl_rows)),
            "avg_slippage_error": sum(slippage_errors) / max(1, len(slippage_errors)),
            "fill_rate": fill_rate,
            "reject_accuracy": self._reject_accuracy(session),
        }

    def trades(self, session: Session, limit: int = 200) -> list[dict[str, object]]:
        rows = session.exec(select(PaperTradeOutcome).order_by(PaperTradeOutcome.id.desc()).limit(limit)).all()
        return [row.model_dump() for row in rows]

    def alpha_breakdown(self, session: Session, limit: int = 300) -> dict[str, object]:
        outcomes = session.exec(select(PaperTradeOutcome).order_by(PaperTradeOutcome.id.desc()).limit(limit)).all()
        if not outcomes:
            return {"components": {}, "manipulation_flags": {}}

        by_signal = {row.signal_id: row for row in outcomes}
        alpha_rows = session.exec(select(AlphaSignal).where(AlphaSignal.decision == "APPROVE")).all()

        components: dict[str, dict[str, float]] = {}
        flags: dict[str, dict[str, float]] = {}

        for alpha in alpha_rows:
            if alpha.id is None or alpha.id not in by_signal:
                continue
            outcome = by_signal[alpha.id]
            pnl = float(outcome.pnl_xrp or 0.0)

            comp_scores = self._safe_json(alpha.component_scores_json)
            for name, raw_value in comp_scores.items():
                score = float(raw_value)
                bucket = components.setdefault(
                    name,
                    {
                        "high_count": 0.0,
                        "high_pnl_sum": 0.0,
                        "low_count": 0.0,
                        "low_pnl_sum": 0.0,
                    },
                )
                if score >= 0.6:
                    bucket["high_count"] += 1
                    bucket["high_pnl_sum"] += pnl
                else:
                    bucket["low_count"] += 1
                    bucket["low_pnl_sum"] += pnl

            manip_flags = self._safe_json(alpha.manipulation_flags_json)
            for name, raw_value in manip_flags.items():
                seen = bool(raw_value)
                bucket = flags.setdefault(name, {"flagged": 0.0, "flagged_negative": 0.0, "clear": 0.0, "clear_positive": 0.0})
                if seen:
                    bucket["flagged"] += 1
                    if pnl <= 0:
                        bucket["flagged_negative"] += 1
                else:
                    bucket["clear"] += 1
                    if pnl > 0:
                        bucket["clear_positive"] += 1

        component_summary: dict[str, dict[str, float]] = {}
        for name, bucket in components.items():
            component_summary[name] = {
                "samples": bucket["high_count"] + bucket["low_count"],
                "avg_pnl_high": bucket["high_pnl_sum"] / max(1.0, bucket["high_count"]),
                "avg_pnl_low": bucket["low_pnl_sum"] / max(1.0, bucket["low_count"]),
            }

        flag_summary: dict[str, dict[str, float]] = {}
        for name, bucket in flags.items():
            flag_summary[name] = {
                "samples": bucket["flagged"] + bucket["clear"],
                "flagged_negative_rate": bucket["flagged_negative"] / max(1.0, bucket["flagged"]),
                "clear_positive_rate": bucket["clear_positive"] / max(1.0, bucket["clear"]),
            }

        return {
            "components": component_summary,
            "manipulation_flags": flag_summary,
        }

    def _reject_accuracy(self, session: Session) -> float:
        rejected = session.exec(select(AlphaSignal).where(AlphaSignal.decision == "REJECT")).all()
        if not rejected:
            return 0.0

        horizon = timedelta(minutes=self.settings.PERF_MONITOR_MINUTES)
        correct = 0

        for row in rejected:
            if row.snapshot_id is None:
                continue
            snap = session.get(MarketSnapshot, row.snapshot_id)
            if snap is None or snap.price_xrp is None or snap.token_id is None:
                continue

            cutoff = snap.created_at + horizon
            future = session.exec(
                select(MarketSnapshot)
                .where(MarketSnapshot.token_id == snap.token_id)
                .where(MarketSnapshot.created_at > snap.created_at)
                .where(MarketSnapshot.created_at <= cutoff)
                .order_by(MarketSnapshot.created_at.desc())
            ).first()
            if future is None or future.price_xrp is None:
                continue

            move_pct = ((future.price_xrp - snap.price_xrp) / snap.price_xrp) * 100.0
            if move_pct <= 0:
                correct += 1

        return correct / max(1, len(rejected))

    @staticmethod
    def _safe_json(raw: str) -> dict[str, object]:
        try:
            value = json.loads(raw)
            if isinstance(value, dict):
                return value
            return {}
        except json.JSONDecodeError:
            return {}

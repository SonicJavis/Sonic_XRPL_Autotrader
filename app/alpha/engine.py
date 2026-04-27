from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from statistics import mean, pstdev

from app.config import Settings
from app.db.models import MarketSnapshot


@dataclass(slots=True)
class AlphaEvaluation:
    pair: str
    score: float
    decision: str
    reasons: list[str]
    spread: float | None
    depth_xrp: float
    imbalance: float
    slippage_estimate: float
    fill_probability: float
    stability_score: float
    timestamp: str
    component_scores: dict[str, float]
    manipulation_flags: dict[str, bool]


class AlphaEngine:
    """Strict, reject-biased deterministic scoring engine."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    @staticmethod
    def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
        return max(low, min(high, value))

    def compute_depth_metrics(self, bids: list[dict[str, float]], asks: list[dict[str, float]]) -> dict[str, float | bool]:
        depth_n = self.settings.ALPHA_DEPTH_LEVELS
        top_bids = bids[:depth_n]
        top_asks = asks[:depth_n]

        bid_liq = sum(level.get("xrp_value", 0.0) for level in top_bids)
        ask_liq = sum(level.get("xrp_value", 0.0) for level in top_asks)
        total_liq = bid_liq + ask_liq

        # WAP uses XRP value as weight for token units.
        bid_tokens = sum(level.get("token_amount", 0.0) for level in top_bids)
        ask_tokens = sum(level.get("token_amount", 0.0) for level in top_asks)
        bid_wap = (bid_liq / bid_tokens) if bid_tokens > 0 else 0.0
        ask_wap = (ask_liq / ask_tokens) if ask_tokens > 0 else 0.0

        imbalance = 0.0
        if total_liq > 0:
            imbalance = (bid_liq - ask_liq) / total_liq

        concentrated = False
        if total_liq > 0:
            first_level = (top_bids[0].get("xrp_value", 0.0) if top_bids else 0.0) + (
                top_asks[0].get("xrp_value", 0.0) if top_asks else 0.0
            )
            concentrated = (first_level / total_liq) > 0.75

        collapses_fast = False
        if top_asks:
            top2_ask_liq = sum(level.get("xrp_value", 0.0) for level in top_asks[:2])
            collapses_fast = top2_ask_liq < (self.settings.MAX_TRADE_XRP * 2)

        return {
            "bid_liquidity_xrp": bid_liq,
            "ask_liquidity_xrp": ask_liq,
            "total_liquidity_xrp": total_liq,
            "bid_wap": bid_wap,
            "ask_wap": ask_wap,
            "imbalance": imbalance,
            "liquidity_concentrated": concentrated,
            "book_collapses_fast": collapses_fast,
        }

    def compute_stability_metrics(self, history: list[MarketSnapshot]) -> dict[str, float | bool]:
        if len(history) < self.settings.ALPHA_STABILITY_WINDOW:
            return {
                "spread_stability": 0.0,
                "liquidity_consistency": 0.0,
                "mid_price_stability": 0.0,
                "imbalance_flip_rate": 1.0,
                "stable_enough": False,
            }

        spreads = [s.spread_pct for s in history if s.spread_pct is not None]
        liqs = [s.liquidity_xrp for s in history]
        mids = [s.price_xrp for s in history if s.price_xrp is not None]

        spread_cv = (pstdev(spreads) / mean(spreads)) if len(spreads) >= 2 and mean(spreads) > 0 else 1.0
        liq_cv = (pstdev(liqs) / mean(liqs)) if len(liqs) >= 2 and mean(liqs) > 0 else 1.0
        mid_cv = (pstdev(mids) / mean(mids)) if len(mids) >= 2 and mean(mids) > 0 else 1.0

        spread_stability = self._clamp(1.0 - spread_cv)
        liq_stability = self._clamp(1.0 - liq_cv)
        mid_stability = self._clamp(1.0 - mid_cv)

        flip_count = 0
        prev_sign = None
        for snap in history:
            sign = 0
            if snap.liquidity_xrp > 0:
                sign = 1 if (snap.liquidity_bid_xrp - snap.liquidity_ask_xrp) >= 0 else -1
            if prev_sign is not None and sign != 0 and sign != prev_sign:
                flip_count += 1
            if sign != 0:
                prev_sign = sign

        flip_rate = flip_count / max(1, len(history) - 1)
        stable_enough = (
            spread_stability >= 0.45
            and liq_stability >= 0.45
            and mid_stability >= 0.40
            and flip_rate <= self.settings.ALPHA_MAX_IMBALANCE_FLIP_RATE
        )

        return {
            "spread_stability": spread_stability,
            "liquidity_consistency": liq_stability,
            "mid_price_stability": mid_stability,
            "imbalance_flip_rate": flip_rate,
            "stable_enough": stable_enough,
        }

    def simulate_fill(self, asks: list[dict[str, float]], target_xrp: float) -> dict[str, float | bool]:
        if target_xrp <= 0:
            return {"expected_fill_price": 0.0, "fill_probability": 0.0, "slippage_pct": 100.0, "fill_possible": False}

        remaining = target_xrp
        acquired_tokens = 0.0
        spent_xrp = 0.0

        for level in asks[: self.settings.ALPHA_DEPTH_LEVELS]:
            level_xrp = level.get("xrp_value", 0.0)
            level_tokens = level.get("token_amount", 0.0)
            if level_xrp <= 0 or level_tokens <= 0:
                continue
            take = min(level_xrp, remaining)
            token_take = (take / level_xrp) * level_tokens
            spent_xrp += take
            acquired_tokens += token_take
            remaining -= take
            if remaining <= 0:
                break

        fill_ratio = (target_xrp - remaining) / target_xrp
        fill_possible = remaining <= 0
        fill_probability = self._clamp(fill_ratio)

        if acquired_tokens <= 0:
            return {
                "expected_fill_price": 0.0,
                "fill_probability": fill_probability,
                "slippage_pct": 100.0,
                "fill_possible": False,
            }

        expected_fill_price = spent_xrp / acquired_tokens
        best_ask = asks[0].get("price", 0.0) if asks else 0.0
        if best_ask <= 0:
            slippage = 100.0
        else:
            slippage = ((expected_fill_price - best_ask) / best_ask) * 100.0

        return {
            "expected_fill_price": expected_fill_price,
            "fill_probability": fill_probability,
            "slippage_pct": slippage,
            "fill_possible": fill_possible,
        }

    def evaluate(
        self,
        *,
        pair: str,
        spread_pct: float | None,
        bids: list[dict[str, float]],
        asks: list[dict[str, float]],
        history: list[MarketSnapshot],
        target_size_xrp: float,
        issuer: str,
    ) -> AlphaEvaluation:
        reasons: list[str] = []

        depth = self.compute_depth_metrics(bids, asks)
        stability = self.compute_stability_metrics(history)
        fill = self.simulate_fill(asks, target_size_xrp)

        spread_quality = 0.0
        if spread_pct is not None and spread_pct >= 0:
            spread_quality = self._clamp(1.0 - (spread_pct / max(self.settings.MAX_SPREAD_PCT, 1e-6)))

        depth_score = self._clamp(depth["total_liquidity_xrp"] / max(self.settings.MIN_LIQUIDITY_XRP * 2, 1.0))
        imbalance_score = self._clamp(1.0 - abs(float(depth["imbalance"])))
        stability_score = float(
            mean(
                [
                    float(stability["spread_stability"]),
                    float(stability["liquidity_consistency"]),
                    float(stability["mid_price_stability"]),
                ]
            )
        )
        fill_feasibility_score = self._clamp(float(fill["fill_probability"]))
        slippage_penalty = self._clamp(float(fill["slippage_pct"]) / max(self.settings.MAX_SLIPPAGE_PCT, 1e-6))

        component_scores = {
            "spread_quality_score": spread_quality,
            "depth_score": depth_score,
            "imbalance_score": imbalance_score,
            "stability_score": stability_score,
            "fill_feasibility_score": fill_feasibility_score,
            "slippage_penalty": slippage_penalty,
        }

        manipulation_flags = {
            "liquidity_concentrated": bool(depth["liquidity_concentrated"]),
            "book_collapses_fast": bool(depth["book_collapses_fast"]),
            "imbalance_flips_fast": float(stability["imbalance_flip_rate"]) > self.settings.ALPHA_MAX_IMBALANCE_FLIP_RATE,
            "synthetic_depth": bool(depth["liquidity_concentrated"]) and float(depth["total_liquidity_xrp"]) > self.settings.MIN_LIQUIDITY_XRP,
            "suspicious_issuer": issuer == "" or issuer.lower().startswith("r000"),
        }

        if spread_pct is None:
            reasons.append("reject: spread unavailable")
        if spread_pct is not None and spread_pct > self.settings.MAX_SPREAD_PCT:
            reasons.append("reject: spread above threshold")
        if len(bids) < 2 or len(asks) < 2:
            reasons.append("reject: insufficient two-sided depth")
        if float(depth["total_liquidity_xrp"]) < self.settings.MIN_LIQUIDITY_XRP:
            reasons.append("reject: insufficient cumulative liquidity")
        if not bool(stability["stable_enough"]):
            reasons.append("reject: stability window not satisfied")
        if not bool(fill["fill_possible"]):
            reasons.append("reject: fill not fully feasible")
        if float(fill["slippage_pct"]) > self.settings.MAX_SLIPPAGE_PCT:
            reasons.append("reject: slippage above threshold")
        if float(fill["fill_probability"]) < self.settings.ALPHA_MIN_FILL_PROBABILITY:
            reasons.append("reject: fill probability too low")
        if any(manipulation_flags.values()):
            reasons.append("reject: manipulation heuristic triggered")

        weighted_score = (
            spread_quality * 0.20
            + depth_score * 0.20
            + imbalance_score * 0.10
            + stability_score * 0.20
            + fill_feasibility_score * 0.20
            + (1.0 - slippage_penalty) * 0.10
        )
        score = self._clamp(weighted_score)

        if score < self.settings.ALPHA_MIN_SCORE:
            reasons.append("reject: score below minimum")

        decision = "REJECT" if reasons else "APPROVE"

        return AlphaEvaluation(
            pair=pair,
            score=score,
            decision=decision,
            reasons=reasons if reasons else ["approve: high-confidence executable conditions"],
            spread=spread_pct,
            depth_xrp=float(depth["total_liquidity_xrp"]),
            imbalance=float(depth["imbalance"]),
            slippage_estimate=float(fill["slippage_pct"]),
            fill_probability=float(fill["fill_probability"]),
            stability_score=stability_score,
            timestamp=datetime.now(tz=timezone.utc).isoformat(),
            component_scores=component_scores,
            manipulation_flags=manipulation_flags,
        )

    def in_cooldown(self, recent_failures: list[datetime]) -> bool:
        if len(recent_failures) < self.settings.ALPHA_COOLDOWN_FAILURES:
            return False
        now = datetime.now(tz=timezone.utc)
        latest_window = recent_failures[-self.settings.ALPHA_COOLDOWN_FAILURES :]
        threshold = now - timedelta(minutes=self.settings.ALPHA_COOLDOWN_MINUTES)
        return all(ts >= threshold for ts in latest_window)

from __future__ import annotations

from statistics import mean

from app.config import Settings
from app.db.models import MarketSnapshot


def _top_share(levels: list[dict[str, float]]) -> float:
    if not levels:
        return 0.0
    top = max(0.0, float(levels[0].get("xrp_value", 0.0)))
    total = sum(max(0.0, float(level.get("xrp_value", 0.0))) for level in levels)
    if total <= 0:
        return 0.0
    return top / total


def analyze_liquidity_decay(
    *,
    settings: Settings,
    history: list[MarketSnapshot],
    bids: list[dict[str, float]],
    asks: list[dict[str, float]],
    spread_pct: float | None,
) -> dict[str, float | bool]:
    depth_now = sum(max(0.0, float(level.get("xrp_value", 0.0))) for level in bids[: settings.ALPHA_DEPTH_LEVELS])
    depth_now += sum(max(0.0, float(level.get("xrp_value", 0.0))) for level in asks[: settings.ALPHA_DEPTH_LEVELS])

    hist_depth = [max(0.0, float(s.liquidity_xrp or 0.0)) for s in history if float(s.liquidity_xrp or 0.0) > 0]
    recent_avg = mean(hist_depth) if hist_depth else depth_now

    if recent_avg <= 0:
        decay_pct = 0.0
    else:
        decay_pct = max(0.0, ((recent_avg - depth_now) / recent_avg) * 100.0)

    collapse_flag = decay_pct >= 50.0

    ask_top_share = _top_share(asks)
    bid_top_share = _top_share(bids)
    ask_backing = sum(max(0.0, float(level.get("xrp_value", 0.0))) for level in asks[1: settings.ALPHA_DEPTH_LEVELS])
    bid_backing = sum(max(0.0, float(level.get("xrp_value", 0.0))) for level in bids[1: settings.ALPHA_DEPTH_LEVELS])
    spoof_flag = (
        (ask_top_share >= 0.80 and ask_backing < (settings.MAX_TRADE_XRP * 3.0))
        or (bid_top_share >= 0.80 and bid_backing < (settings.MAX_TRADE_XRP * 3.0))
    )

    fake_spread_flag = bool(
        spread_pct is not None
        and spread_pct <= 0.20
        and depth_now < max(settings.MIN_LIQUIDITY_XRP, settings.MAX_TRADE_XRP * 2.0)
    )

    return {
        "decay_pct": round(decay_pct, 4),
        "collapse_flag": collapse_flag,
        "spoof_flag": spoof_flag,
        "fake_spread_flag": fake_spread_flag,
    }

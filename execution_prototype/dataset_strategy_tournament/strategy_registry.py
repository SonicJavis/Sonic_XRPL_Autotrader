from __future__ import annotations
import hashlib
from typing import Any, Dict, List, Optional, Tuple

from .models import DatasetStrategyDefinition

PROHIBITED_LIVE = "READ-ONLY. NO WALLET. NO SIGNING. NO SUBMISSION."


def _strategy_id(name: str, version: str) -> str:
    raw = f"strategy|{name}|{version}"
    return hashlib.sha256(raw.encode()).hexdigest()


AMM_SEEDED_LAUNCH_WATCH = DatasetStrategyDefinition(
    strategy_id=_strategy_id("amm_seeded_launch_watch", "v1"),
    strategy_name="amm_seeded_launch_watch",
    strategy_version="v1",
    strategy_family="amm_seeded",
    description="Watches AMM seeding events for early liquidity opportunity detection. Paper-only.",
    required_features=[
        "amm_seeded_event",
        "amm_asset_pair",
        "amm_initial_liquidity",
        "ledger_index",
        "timestamp",
    ],
    prohibited_live_action=PROHIBITED_LIVE,
)

TRUSTLINE_SPIKE_WATCH = DatasetStrategyDefinition(
    strategy_id=_strategy_id("trustline_spike_watch", "v1"),
    strategy_name="trustline_spike_watch",
    strategy_version="v1",
    strategy_family="trustline_spike",
    description="Watches trustline growth spikes as potential interest signals. Paper-only.",
    required_features=[
        "trustline_count",
        "trustline_delta",
        "asset_key_id",
        "ledger_index",
        "timestamp",
    ],
    prohibited_live_action=PROHIBITED_LIVE,
)

OFFER_NOISE_FILTER = DatasetStrategyDefinition(
    strategy_id=_strategy_id("offer_noise_filter", "v1"),
    strategy_name="offer_noise_filter",
    strategy_version="v1",
    strategy_family="offer_noise_filter",
    description="Filters noisy offer-only signals to reduce false positives. Paper-only.",
    required_features=[
        "offer_count",
        "offer_volume",
        "bid_ask_spread",
        "asset_key_id",
        "ledger_index",
    ],
    prohibited_live_action=PROHIBITED_LIVE,
)

METADATA_QUALITY_GUARD = DatasetStrategyDefinition(
    strategy_id=_strategy_id("metadata_quality_guard", "v1"),
    strategy_name="metadata_quality_guard",
    strategy_version="v1",
    strategy_family="metadata_quality",
    description="Requires full metadata backing before emitting a paper accept. Paper-only.",
    required_features=[
        "has_metadata",
        "metadata_completeness_score",
        "issuer_domain",
        "asset_key_id",
        "ledger_index",
    ],
    prohibited_live_action=PROHIBITED_LIVE,
)

LIQUIDITY_GUARD = DatasetStrategyDefinition(
    strategy_id=_strategy_id("liquidity_guard", "v1"),
    strategy_name="liquidity_guard",
    strategy_version="v1",
    strategy_family="liquidity_guard",
    description="Requires sufficient liquidity snapshots before emitting a paper accept. Paper-only.",
    required_features=[
        "liquidity_score",
        "best_bid",
        "best_ask",
        "depth_score",
        "asset_key_id",
        "ledger_index",
    ],
    prohibited_live_action=PROHIBITED_LIVE,
)

BASELINE_HOLDOUT_CONTROL = DatasetStrategyDefinition(
    strategy_id=_strategy_id("baseline_holdout_control", "v1"),
    strategy_name="baseline_holdout_control",
    strategy_version="v1",
    strategy_family="baseline",
    description="Simple baseline control for comparison across all window types. Paper-only.",
    required_features=[
        "asset_key_id",
        "ledger_index",
        "timestamp",
    ],
    prohibited_live_action=PROHIBITED_LIVE,
)

STRATEGY_REGISTRY: Dict[str, DatasetStrategyDefinition] = {
    AMM_SEEDED_LAUNCH_WATCH.strategy_name: AMM_SEEDED_LAUNCH_WATCH,
    TRUSTLINE_SPIKE_WATCH.strategy_name: TRUSTLINE_SPIKE_WATCH,
    OFFER_NOISE_FILTER.strategy_name: OFFER_NOISE_FILTER,
    METADATA_QUALITY_GUARD.strategy_name: METADATA_QUALITY_GUARD,
    LIQUIDITY_GUARD.strategy_name: LIQUIDITY_GUARD,
    BASELINE_HOLDOUT_CONTROL.strategy_name: BASELINE_HOLDOUT_CONTROL,
}

Signal = Tuple[str, str, List[str]]  # (accept|reject|unknown, reason, evidence)


def _eval_amm_seeded_launch_watch(features: Dict[str, Any]) -> Signal:
    ev: List[str] = []
    if not features.get("amm_seeded_event"):
        return ("reject", "no_amm_seeded_event", ["amm_seeded_event missing or false"])
    liquidity = features.get("amm_initial_liquidity")
    if liquidity is None:
        ev.append("amm_initial_liquidity missing")
        return ("unknown", "missing_liquidity_info", ev)
    try:
        liq_val = float(str(liquidity))
    except (ValueError, TypeError):
        ev.append(f"amm_initial_liquidity not numeric: {liquidity}")
        return ("unknown", "invalid_liquidity_value", ev)
    if liq_val > 0:
        ev.append(f"amm_initial_liquidity={liq_val}")
        return ("accept", "amm_seeded_with_liquidity", ev)
    ev.append(f"amm_initial_liquidity={liq_val} (zero)")
    return ("reject", "amm_seeded_zero_liquidity", ev)


def _eval_trustline_spike_watch(features: Dict[str, Any]) -> Signal:
    ev: List[str] = []
    delta = features.get("trustline_delta")
    count = features.get("trustline_count")
    if delta is None or count is None:
        ev.append("trustline_delta or trustline_count missing")
        return ("unknown", "missing_trustline_info", ev)
    try:
        delta_val = float(str(delta))
        count_val = float(str(count))
    except (ValueError, TypeError):
        ev.append("trustline_delta or trustline_count not numeric")
        return ("unknown", "invalid_trustline_value", ev)
    if delta_val > 10 and count_val > 5:
        ev.append(f"trustline_delta={delta_val}, trustline_count={count_val}")
        return ("accept", "trustline_spike_detected", ev)
    if delta_val <= 0:
        ev.append(f"trustline_delta={delta_val} (no growth)")
        return ("reject", "no_trustline_growth", ev)
    ev.append(f"trustline_delta={delta_val}, trustline_count={count_val} (insufficient spike)")
    return ("reject", "trustline_spike_below_threshold", ev)


def _eval_offer_noise_filter(features: Dict[str, Any]) -> Signal:
    ev: List[str] = []
    spread = features.get("bid_ask_spread")
    volume = features.get("offer_volume")
    count = features.get("offer_count")
    if spread is None or volume is None or count is None:
        ev.append("bid_ask_spread, offer_volume, or offer_count missing")
        return ("unknown", "missing_offer_info", ev)
    try:
        spread_val = float(str(spread))
        volume_val = float(str(volume))
        count_val = float(str(count))
    except (ValueError, TypeError):
        ev.append("offer features not numeric")
        return ("unknown", "invalid_offer_values", ev)
    if spread_val > 0.15 or volume_val < 100 or count_val < 3:
        ev.append(f"spread={spread_val}, volume={volume_val}, count={count_val}")
        return ("reject", "high_noise_signal_filtered", ev)
    ev.append(f"spread={spread_val}, volume={volume_val}, count={count_val}")
    return ("accept", "low_noise_offer_accepted", ev)


def _eval_metadata_quality_guard(features: Dict[str, Any]) -> Signal:
    ev: List[str] = []
    has_meta = features.get("has_metadata")
    score = features.get("metadata_completeness_score")
    if has_meta is None:
        ev.append("has_metadata missing")
        return ("unknown", "missing_metadata_flag", ev)
    if not has_meta:
        ev.append("has_metadata=False")
        return ("reject", "no_metadata_backing", ev)
    if score is None:
        ev.append("metadata_completeness_score missing")
        return ("unknown", "missing_completeness_score", ev)
    try:
        score_val = float(str(score))
    except (ValueError, TypeError):
        ev.append(f"metadata_completeness_score not numeric: {score}")
        return ("unknown", "invalid_completeness_score", ev)
    if score_val >= 0.7:
        ev.append(f"metadata_completeness_score={score_val}")
        return ("accept", "full_metadata_backing", ev)
    ev.append(f"metadata_completeness_score={score_val} below 0.7")
    return ("reject", "insufficient_metadata_quality", ev)


def _eval_liquidity_guard(features: Dict[str, Any]) -> Signal:
    ev: List[str] = []
    liq_score = features.get("liquidity_score")
    best_bid = features.get("best_bid")
    best_ask = features.get("best_ask")
    if liq_score is None or best_bid is None or best_ask is None:
        ev.append("liquidity_score, best_bid, or best_ask missing")
        return ("unknown", "missing_liquidity_data", ev)
    try:
        liq_val = float(str(liq_score))
        bid_val = float(str(best_bid))
        ask_val = float(str(best_ask))
    except (ValueError, TypeError):
        ev.append("liquidity features not numeric")
        return ("unknown", "invalid_liquidity_values", ev)
    if liq_val < 0.5 or bid_val <= 0 or ask_val <= 0:
        ev.append(f"liquidity_score={liq_val}, best_bid={bid_val}, best_ask={ask_val}")
        return ("reject", "insufficient_liquidity", ev)
    ev.append(f"liquidity_score={liq_val}, best_bid={bid_val}, best_ask={ask_val}")
    return ("accept", "adequate_liquidity", ev)


def _eval_baseline_holdout_control(features: Dict[str, Any]) -> Signal:
    ev: List[str] = []
    if features.get("asset_key_id") and features.get("ledger_index"):
        ev.append(f"asset_key_id={features.get('asset_key_id')}, ledger_index={features.get('ledger_index')}")
        return ("accept", "baseline_accept", ev)
    ev.append("asset_key_id or ledger_index missing")
    return ("unknown", "baseline_missing_fields", ev)


STRATEGY_EVALUATORS = {
    "amm_seeded_launch_watch": _eval_amm_seeded_launch_watch,
    "trustline_spike_watch": _eval_trustline_spike_watch,
    "offer_noise_filter": _eval_offer_noise_filter,
    "metadata_quality_guard": _eval_metadata_quality_guard,
    "liquidity_guard": _eval_liquidity_guard,
    "baseline_holdout_control": _eval_baseline_holdout_control,
}

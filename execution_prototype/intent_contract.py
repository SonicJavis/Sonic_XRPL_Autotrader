from __future__ import annotations

import json
from dataclasses import dataclass
from math import isfinite
from pathlib import Path
from typing import Mapping


ALLOWED_ACTIONS = {"buy", "sell"}
STALE_DECISIONS = {"stale", "invalid"}


@dataclass(frozen=True, slots=True)
class ExecutionIntent:
    intent_id: str
    action: str
    token: str
    issuer: str
    size: float
    execution_feasibility: dict[str, object]
    liquidity_source_model: dict[str, object]
    liquidity_decay: dict[str, object]

    def to_dict(self) -> dict[str, object]:
        return {
            "action": self.action,
            "execution_feasibility": _sorted_mapping(self.execution_feasibility),
            "intent_id": self.intent_id,
            "issuer": self.issuer,
            "liquidity_decay": _sorted_mapping(self.liquidity_decay),
            "liquidity_source_model": _sorted_mapping(self.liquidity_source_model),
            "size": round(self.size, 6),
            "token": self.token,
        }


def load_intent_file(path: str | Path) -> ExecutionIntent:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, Mapping):
        raise ValueError("intent JSON must be an object")
    return parse_intent(raw)


def parse_intent(raw: Mapping[str, object]) -> ExecutionIntent:
    missing = [
        key
        for key in (
            "intent_id",
            "action",
            "token",
            "issuer",
            "size",
            "execution_feasibility",
            "liquidity_source_model",
            "liquidity_decay",
        )
        if key not in raw
    ]
    if missing:
        raise ValueError(f"missing intent fields: {','.join(sorted(missing))}")
    action = str(raw["action"]).lower()
    if action not in ALLOWED_ACTIONS:
        raise ValueError("intent action must be buy or sell")
    size = _positive(raw["size"])
    if size <= 0.0:
        raise ValueError("intent size must be positive")
    feasibility = _mapping(raw["execution_feasibility"], "execution_feasibility")
    liquidity = _mapping(raw["liquidity_source_model"], "liquidity_source_model")
    decay = _mapping(raw["liquidity_decay"], "liquidity_decay")
    return ExecutionIntent(
        intent_id=str(raw["intent_id"]),
        action=action,
        token=str(raw["token"]),
        issuer=str(raw["issuer"]),
        size=size,
        execution_feasibility=feasibility,
        liquidity_source_model=liquidity,
        liquidity_decay=decay,
    )


def validate_safety_gates(intent: ExecutionIntent) -> list[str]:
    failures: list[str] = []
    if str(intent.execution_feasibility.get("decision", "avoid")).lower() == "avoid":
        failures.append("execution_feasibility_avoid")
    if str(intent.liquidity_source_model.get("decision", "avoid")).lower() == "avoid":
        failures.append("liquidity_source_avoid")
    if str(intent.liquidity_decay.get("decision", "invalid")).lower() in STALE_DECISIONS:
        failures.append("liquidity_decay_stale_or_invalid")
    if not bool(intent.execution_feasibility.get("is_executable", False)) is False:
        failures.append("unexpected_executable_flag")
    return sorted(failures)


def ensure_safety_gates(intent: ExecutionIntent) -> None:
    failures = validate_safety_gates(intent)
    if failures:
        raise ValueError(f"intent blocked by safety gates: {','.join(failures)}")


def risk_summary(intent: ExecutionIntent) -> dict[str, object]:
    return {
        "intent_id": intent.intent_id,
        "action": intent.action,
        "token": intent.token,
        "issuer": intent.issuer,
        "size": round(intent.size, 6),
        "expected_fill_ratio": _unit(intent.execution_feasibility.get("expected_fill_ratio", 0.0)),
        "expected_slippage": _unit(intent.execution_feasibility.get("expected_slippage", 0.0)),
        "liquidity_source": str(intent.liquidity_source_model.get("liquidity_source", "unknown")),
        "decay_decision": str(intent.liquidity_decay.get("decision", "invalid")),
        "warnings": [
            "XRPL execution outcome is not guaranteed",
            "Liquidity can change between validated ledgers",
            "Path-based transactions can fail at validation time",
        ],
        "blocked_reasons": validate_safety_gates(intent),
    }


def _mapping(raw: object, field_name: str) -> dict[str, object]:
    if not isinstance(raw, Mapping):
        raise ValueError(f"{field_name} must be an object")
    return dict(raw)


def _positive(raw: object) -> float:
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return 0.0
    return value if isfinite(value) and value > 0.0 else 0.0


def _unit(raw: object) -> float:
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return 0.0
    if not isfinite(value):
        return 0.0
    return round(max(0.0, min(1.0, value)), 6)


def _sorted_mapping(raw: Mapping[str, object]) -> dict[str, object]:
    clean: dict[str, object] = {}
    for key, value in sorted(raw.items()):
        if isinstance(value, Mapping):
            clean[str(key)] = _sorted_mapping(value)
        elif isinstance(value, float):
            clean[str(key)] = round(value if isfinite(value) else 0.0, 6)
        elif isinstance(value, list):
            clean[str(key)] = list(value)
        else:
            clean[str(key)] = value
    return clean

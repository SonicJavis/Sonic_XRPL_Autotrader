from __future__ import annotations

import json
from pathlib import Path

from sonic_xrpl.firstledger_intelligence import build_intelligence_results, load_firstledger_intelligence_inputs
from sonic_xrpl.paper_sniper_simulation.models import PaperSniperBatch, PaperSniperScenario


def _to_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes"}
    return bool(value)


def _to_float(value):
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_int(value, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def load_paper_sniper_batch(path: str | Path) -> PaperSniperBatch:
    fixture_path = Path(path)
    payload = json.loads(fixture_path.read_text(encoding="utf-8"))
    intelligence_fixture = str(payload.get("intelligence_fixture") or "").strip()
    if not intelligence_fixture:
        raise ValueError("paper-sniper simulation fixture requires intelligence_fixture")

    intelligence_inputs = load_firstledger_intelligence_inputs(intelligence_fixture)
    intelligence_results = tuple(build_intelligence_results(intelligence_inputs))

    rows = payload.get("simulations", [])
    if not isinstance(rows, list):
        raise ValueError("paper-sniper simulation fixture field simulations must be a list")

    scenarios: list[PaperSniperScenario] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        notes = row.get("notes", [])
        if not isinstance(notes, list):
            notes = []
        scenarios.append(
            PaperSniperScenario(
                candidate_id=str(row.get("candidate_id") or ""),
                allow_watch_entry=_to_bool(row.get("allow_watch_entry", False)),
                allow_missing_holder_simulation=_to_bool(row.get("allow_missing_holder_simulation", False)),
                stale_policy=str(row.get("stale_policy") or "reduce_confidence"),
                entry_price_xrp=_to_float(row.get("entry_price_xrp")),
                exit_price_xrp=_to_float(row.get("exit_price_xrp")),
                slippage_bps_assumption=_to_int(row.get("slippage_bps_assumption"), 50),
                latency_seconds_assumption=_to_int(row.get("latency_seconds_assumption"), 4),
                ledger_window_seconds_assumption=_to_int(row.get("ledger_window_seconds_assumption"), 10),
                liquidity_available_pct_assumption=_to_float(row.get("liquidity_available_pct_assumption")),
                outcome_window=str(row.get("outcome_window") or "5m"),
                notes=tuple(str(item) for item in notes),
            )
        )

    if not scenarios:
        scenarios = [
            PaperSniperScenario(
                candidate_id=item.candidate_id,
            )
            for item in intelligence_results
        ]

    return PaperSniperBatch(
        intelligence_fixture=intelligence_fixture,
        intelligence_results=intelligence_results,
        scenarios=tuple(sorted(scenarios, key=lambda row: row.candidate_id)),
    )

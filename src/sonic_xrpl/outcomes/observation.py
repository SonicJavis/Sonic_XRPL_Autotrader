from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable, Mapping

from sonic_xrpl.outcomes.errors import OutcomeFixtureError
from sonic_xrpl.outcomes.models import PaperOutcomeObservation
from sonic_xrpl.signals.evidence import stable_id


def _as_float_or_none(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise OutcomeFixtureError(f"Invalid numeric outcome value: {value!r}") from exc


def _as_int_or_none(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise OutcomeFixtureError(f"Invalid integer outcome value: {value!r}") from exc


def _as_limitations(value: Any) -> tuple[str, ...]:
    if value in (None, ""):
        return tuple()
    if not isinstance(value, list):
        raise OutcomeFixtureError("Outcome limitations must be a list")
    return tuple(str(item) for item in value)


def _rows_from_payload(payload: Any) -> Iterable[Mapping[str, Any]]:
    rows = payload.get("observations", []) if isinstance(payload, dict) else payload
    if not isinstance(rows, list):
        raise OutcomeFixtureError("Outcome fixture must be a list or contain an observations list")
    for row in rows:
        if not isinstance(row, Mapping):
            raise OutcomeFixtureError("Outcome observation rows must be objects")
        yield row


def load_outcome_observations(path: str | Path) -> list[PaperOutcomeObservation]:
    """Load deterministic paper outcome observations from a local fixture."""
    source_path = Path(path)
    try:
        payload = json.loads(source_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise OutcomeFixtureError(f"Outcome fixture is not valid JSON: {source_path}") from exc

    observations: list[PaperOutcomeObservation] = []
    for row in _rows_from_payload(payload):
        candidate_id = str(row.get("candidate_id") or "").strip()
        if not candidate_id:
            raise OutcomeFixtureError("Outcome observation is missing candidate_id")

        signal_id = str(row.get("signal_id") or "").strip()
        window = str(row.get("window") or "unknown_window").strip()
        observed_at = str(row.get("observed_at") or "").strip()
        observation_id = str(
            row.get("observation_id")
            or stable_id("obs", candidate_id, signal_id, window, observed_at)
        )

        observations.append(
            PaperOutcomeObservation(
                observation_id=observation_id,
                candidate_id=candidate_id,
                signal_id=signal_id,
                window=window,
                observed_at=observed_at,
                entry_price_xrp=_as_float_or_none(row.get("entry_price_xrp")),
                exit_price_xrp=_as_float_or_none(row.get("exit_price_xrp")),
                baseline_exit_price_xrp=_as_float_or_none(row.get("baseline_exit_price_xrp")),
                liquidity_score=_as_int_or_none(row.get("liquidity_score")),
                evidence_quality=str(row.get("evidence_quality") or "fixture"),
                source_fixture=str(source_path),
                limitations=_as_limitations(row.get("limitations")),
                paper_only=True,
                live_execution_allowed=False,
            )
        )

    observations.sort(key=lambda item: (item.candidate_id, item.signal_id, item.window, item.observation_id))
    return observations

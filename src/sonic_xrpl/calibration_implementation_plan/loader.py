from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from sonic_xrpl.calibration_implementation_plan.errors import ImplementationInputError


def _load_json(path: str | Path) -> Any:
    source = Path(path)
    try:
        return json.loads(source.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ImplementationInputError(f"Input file not found: {source}") from exc
    except json.JSONDecodeError as exc:
        raise ImplementationInputError(f"Input file is not valid JSON: {source}") from exc


def load_approval_ledger(path: str | Path) -> dict[str, Any]:
    payload = _load_json(path)
    if not isinstance(payload, Mapping):
        raise ImplementationInputError("Approval ledger must be a JSON object.")
    if "ledger_id" not in payload:
        raise ImplementationInputError("Approval ledger missing required field: ledger_id")
    if "records" not in payload or not isinstance(payload["records"], list):
        raise ImplementationInputError("Approval ledger missing required list: records")
    return dict(payload)


def load_change_requests(path: str | Path) -> list[dict[str, Any]]:
    payload = _load_json(path)
    if not isinstance(payload, list):
        raise ImplementationInputError("Change requests input must be a JSON list.")
    requests: list[dict[str, Any]] = []
    for item in payload:
        if isinstance(item, Mapping):
            requests.append(dict(item))
    return requests

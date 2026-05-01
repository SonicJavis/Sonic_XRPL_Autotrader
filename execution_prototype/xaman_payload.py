from __future__ import annotations

import json
from hashlib import sha256
from urllib.parse import quote


def build_xaman_payload(unsigned_tx: dict[str, object], *, user_token: str | None = None) -> dict[str, object]:
    tx = _sorted(unsigned_tx)
    payload = {
        "txjson": tx,
        "options": {
            "submit": False,
            "multisign": False,
        },
        "custom_meta": {
            "identifier": payload_identifier(tx),
            "instruction": "Review manually in Xaman. This tool never handles account credentials.",
        },
    }
    if user_token:
        payload["user_token"] = user_token
    return _sorted(payload)


def build_deep_link(payload: dict[str, object]) -> str:
    encoded = quote(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    return f"xaman://xapp/sign/{encoded}"


def build_qr_rendering_payload(deep_link: str) -> dict[str, object]:
    return {
        "format": "qr_source_text",
        "qr_data": str(deep_link),
        "instructions": [
            "Scan with Xaman to sign.",
            "Review transaction before approving.",
        ],
        "is_executable": False,
    }


def payload_identifier(unsigned_tx: dict[str, object]) -> str:
    encoded = json.dumps(unsigned_tx, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return f"xaman_{sha256(encoded).hexdigest()[:24]}"


def _sorted(raw: object) -> object:
    if isinstance(raw, dict):
        return {key: _sorted(raw[key]) for key in sorted(raw)}
    if isinstance(raw, list):
        return [_sorted(item) for item in raw]
    return raw

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Mapping

from execution_prototype.audit import append_lifecycle_audit_record
from execution_prototype.intent_contract import ExecutionIntent, ensure_safety_gates, load_intent_file
from execution_prototype.xaman_payload import build_xaman_payload
from execution_prototype.xrpl_tx_builder import build_unsigned_transaction


DEFAULT_SESSION_LOG = Path(__file__).with_name("payload_sessions.jsonl")
LIFECYCLE_EVENTS = {
    "SESSION_CREATED",
    "SESSION_SIGNED",
    "SESSION_SUBMITTED",
    "SESSION_RESULT_RECORDED",
    "SESSION_VALIDATED",
    "SESSION_FAILED",
}
STATUS_ORDER = ("created", "signed", "submitted", "validated", "failed", "unknown")
VALID_TRANSITIONS = {
    "created": {"signed", "unknown"},
    "signed": {"submitted", "failed", "unknown"},
    "submitted": {"validated", "failed", "unknown"},
    "unknown": {"signed", "submitted", "validated", "failed"},
}


@dataclass(frozen=True, slots=True)
class PayloadSession:
    session_id: str
    intent_id: str
    tx_type: str
    unsigned_tx: dict[str, object]
    xaman_payload: dict[str, object]
    xrpl_state: dict[str, object]
    status: str
    tx_hash: str | None
    created_at: str
    updated_at: str

    def to_dict(self) -> dict[str, object]:
        body = {
            "created_at": self.created_at,
            "intent_id": self.intent_id,
            "session_id": self.session_id,
            "status": self.status,
            "tx_hash": self.tx_hash,
            "tx_type": self.tx_type,
            "unsigned_tx": _sorted(self.unsigned_tx),
            "updated_at": self.updated_at,
            "xaman_payload": _sorted(self.xaman_payload),
            "xrpl_state": _sorted(self.xrpl_state),
        }
        return _sorted(body)


def create_session_from_intent_file(
    intent_path: str | Path,
    *,
    account: str = "rMANUAL_ACCOUNT_PLACEHOLDER",
    session_log: str | Path = DEFAULT_SESSION_LOG,
    audit_log: str | Path | None = None,
) -> PayloadSession:
    intent = load_intent_file(intent_path)
    return create_session(intent, account=account, session_log=session_log, audit_log=audit_log)


def create_session(
    intent: ExecutionIntent,
    *,
    account: str = "rMANUAL_ACCOUNT_PLACEHOLDER",
    session_log: str | Path = DEFAULT_SESSION_LOG,
    audit_log: str | Path | None = None,
) -> PayloadSession:
    ensure_safety_gates(intent)
    unsigned_tx = build_unsigned_transaction(intent, account=account)
    xaman_payload = build_xaman_payload(unsigned_tx)
    session_id = stable_session_id(intent=intent, unsigned_tx=unsigned_tx)
    now = _now()
    session = PayloadSession(
        session_id=session_id,
        intent_id=intent.intent_id,
        tx_type=str(unsigned_tx.get("TransactionType", "unknown")),
        unsigned_tx=unsigned_tx,
        xaman_payload=xaman_payload,
        xrpl_state={
            "engine_result": None,
            "engine_result_message": None,
            "ledger_index": None,
            "submitted": False,
            "validated": False,
        },
        status="created",
        tx_hash=None,
        created_at=now,
        updated_at=now,
    )
    append_session_event(session, "SESSION_CREATED", session_log=session_log, audit_log=audit_log)
    return session


def stable_session_id(*, intent: ExecutionIntent, unsigned_tx: Mapping[str, object]) -> str:
    payload_basis = {
        "intent": intent.to_dict(),
        "unsigned_tx": _sorted(dict(unsigned_tx)),
    }
    encoded = json.dumps(payload_basis, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return f"session_{sha256(encoded).hexdigest()[:24]}"


def load_session(session_id: str, *, session_log: str | Path = DEFAULT_SESSION_LOG) -> PayloadSession:
    events = _read_session_events(session_log)
    state: PayloadSession | None = None
    for event in events:
        if event.get("session_id") != session_id:
            continue
        snapshot = event.get("session")
        if isinstance(snapshot, Mapping):
            state = _session_from_mapping(snapshot)
    if state is None:
        raise ValueError("payload session not found")
    return state


def mark_signed(
    session_id: str,
    *,
    session_log: str | Path = DEFAULT_SESSION_LOG,
    audit_log: str | Path | None = None,
) -> PayloadSession:
    session = load_session(session_id, session_log=session_log)
    updated = _transition(session, "signed")
    append_session_event(updated, "SESSION_SIGNED", session_log=session_log, audit_log=audit_log)
    return updated


def record_submission(
    session_id: str,
    tx_hash: str,
    *,
    session_log: str | Path = DEFAULT_SESSION_LOG,
    audit_log: str | Path | None = None,
) -> PayloadSession:
    if not str(tx_hash).strip():
        raise ValueError("tx_hash is required and user-provided")
    session = load_session(session_id, session_log=session_log)
    state = dict(session.xrpl_state)
    state["submitted"] = True
    updated = _replace(session, status="submitted", tx_hash=str(tx_hash), xrpl_state=state)
    _validate_transition(session.status, updated.status)
    append_session_event(updated, "SESSION_SUBMITTED", session_log=session_log, audit_log=audit_log)
    return updated


def record_result(
    session_id: str,
    engine_result: str,
    *,
    engine_result_message: str | None = None,
    session_log: str | Path = DEFAULT_SESSION_LOG,
    audit_log: str | Path | None = None,
) -> PayloadSession:
    if not str(engine_result).strip():
        raise ValueError("engine_result is required")
    session = load_session(session_id, session_log=session_log)
    state = dict(session.xrpl_state)
    state["engine_result"] = str(engine_result)
    state["engine_result_message"] = str(engine_result_message) if engine_result_message else None
    status = "submitted" if session.status in {"created", "signed", "submitted"} else session.status
    updated = _replace(session, status=status, xrpl_state=state)
    append_session_event(updated, "SESSION_RESULT_RECORDED", session_log=session_log, audit_log=audit_log)
    return updated


def mark_validated(
    session_id: str,
    *,
    ledger_index: int,
    session_log: str | Path = DEFAULT_SESSION_LOG,
    audit_log: str | Path | None = None,
) -> PayloadSession:
    if int(ledger_index) <= 0:
        raise ValueError("validated ledger_index must be positive and user-provided")
    session = load_session(session_id, session_log=session_log)
    state = dict(session.xrpl_state)
    state["ledger_index"] = int(ledger_index)
    state["validated"] = True
    updated = _replace(session, status="validated", xrpl_state=state)
    _validate_transition(session.status, updated.status)
    append_session_event(updated, "SESSION_VALIDATED", session_log=session_log, audit_log=audit_log)
    return updated


def mark_failed(
    session_id: str,
    *,
    engine_result: str,
    session_log: str | Path = DEFAULT_SESSION_LOG,
    audit_log: str | Path | None = None,
) -> PayloadSession:
    if not str(engine_result).strip():
        raise ValueError("engine_result is required for failed state")
    session = load_session(session_id, session_log=session_log)
    state = dict(session.xrpl_state)
    state["engine_result"] = str(engine_result)
    state["validated"] = False
    updated = _replace(session, status="failed", xrpl_state=state)
    _validate_transition(session.status, updated.status)
    append_session_event(updated, "SESSION_FAILED", session_log=session_log, audit_log=audit_log)
    return updated


def append_session_event(
    session: PayloadSession,
    event_type: str,
    *,
    session_log: str | Path = DEFAULT_SESSION_LOG,
    audit_log: str | Path | None = None,
) -> dict[str, object]:
    if event_type not in LIFECYCLE_EVENTS:
        raise ValueError("unsupported lifecycle event type")
    event = {
        "engine_result": session.xrpl_state.get("engine_result"),
        "event_type": event_type,
        "intent_id": session.intent_id,
        "session": session.to_dict(),
        "session_id": session.session_id,
        "timestamp": _now(),
        "tx_hash": session.tx_hash,
    }
    target = Path(session_log)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(_sorted(event), sort_keys=True, separators=(",", ":")) + "\n")
    append_lifecycle_audit_record(
        event_type=event_type,
        session_id=session.session_id,
        intent_id=session.intent_id,
        tx_hash=session.tx_hash,
        engine_result=str(session.xrpl_state.get("engine_result") or "") or None,
        path=audit_log or Path(__file__).with_name("lifecycle_audit_log.jsonl"),
    )
    return event


def _transition(session: PayloadSession, status: str) -> PayloadSession:
    _validate_transition(session.status, status)
    return _replace(session, status=status)


def _validate_transition(current: str, target: str) -> None:
    if current == target:
        raise ValueError("duplicate lifecycle transition rejected")
    if current in {"validated", "failed"}:
        raise ValueError("terminal payload session cannot transition")
    if target not in VALID_TRANSITIONS.get(current, set()):
        raise ValueError(f"invalid lifecycle transition: {current}->{target}")


def _replace(session: PayloadSession, **changes: object) -> PayloadSession:
    body = session.to_dict()
    body.update(changes)
    body["updated_at"] = _now()
    return _session_from_mapping(body)


def _session_from_mapping(raw: Mapping[str, object]) -> PayloadSession:
    status = str(raw.get("status", "unknown"))
    if status not in STATUS_ORDER:
        status = "unknown"
    xrpl_state = raw.get("xrpl_state", {})
    if not isinstance(xrpl_state, Mapping):
        xrpl_state = {}
    return PayloadSession(
        session_id=str(raw["session_id"]),
        intent_id=str(raw["intent_id"]),
        tx_type=str(raw["tx_type"]),
        unsigned_tx=dict(raw.get("unsigned_tx", {})),
        xaman_payload=dict(raw.get("xaman_payload", {})),
        xrpl_state=dict(xrpl_state),
        status=status,
        tx_hash=(str(raw["tx_hash"]) if raw.get("tx_hash") else None),
        created_at=str(raw.get("created_at", "")),
        updated_at=str(raw.get("updated_at", "")),
    )


def _read_session_events(path: str | Path) -> list[dict[str, object]]:
    target = Path(path)
    if not target.exists():
        return []
    rows: list[dict[str, object]] = []
    for line in target.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        raw = json.loads(line)
        if isinstance(raw, dict):
            rows.append(raw)
    return rows


def _now() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def _sorted(raw: object) -> object:
    if isinstance(raw, Mapping):
        return {str(key): _sorted(value) for key, value in sorted(raw.items())}
    if isinstance(raw, list):
        return [_sorted(item) for item in raw]
    return raw

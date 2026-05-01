from __future__ import annotations

from typing import Callable, Mapping

from execution_prototype.audit import append_audit_record
from execution_prototype.intent_contract import ExecutionIntent, ensure_safety_gates, risk_summary


CONFIRMATION_PHRASE = "CONFIRM_EXECUTION"


def require_manual_confirmation(value: str) -> None:
    if value != CONFIRMATION_PHRASE:
        raise ValueError("manual confirmation phrase mismatch")


def submit_manual(
    *,
    intent: ExecutionIntent,
    unsigned_tx: Mapping[str, object],
    confirmation: str,
    signed_blob: str | None = None,
    submitter: Callable[[str], Mapping[str, object]] | None = None,
    audit_path=None,
) -> dict[str, object]:
    ensure_safety_gates(intent)
    require_manual_confirmation(confirmation)
    summary = risk_summary(intent)
    if signed_blob is None or submitter is None:
        append_audit_record(
            intent_id=intent.intent_id,
            tx_type=str(unsigned_tx.get("TransactionType", "unknown")),
            tx_payload=unsigned_tx,
            user_confirmed=True,
            submitted=False,
            path=audit_path or _default_audit_path(),
        )
        return {
            "submitted": False,
            "reason": "signed_blob_or_submitter_missing",
            "risk_summary": summary,
            "is_executable": False,
        }
    response = dict(submitter(signed_blob))
    tx_hash = str(response.get("tx_hash", response.get("hash", "")) or "")
    append_audit_record(
        intent_id=intent.intent_id,
        tx_type=str(unsigned_tx.get("TransactionType", "unknown")),
        tx_payload=unsigned_tx,
        user_confirmed=True,
        submitted=True,
        tx_hash=tx_hash or None,
        path=audit_path or _default_audit_path(),
    )
    return {
        "submitted": True,
        "tx_hash": tx_hash,
        "risk_summary": summary,
        "is_executable": False,
    }


def _default_audit_path():
    from execution_prototype.audit import DEFAULT_AUDIT_PATH

    return DEFAULT_AUDIT_PATH

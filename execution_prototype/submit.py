from __future__ import annotations

from typing import Callable, Mapping

from execution_prototype.audit import append_audit_record
from execution_prototype.intent_contract import ExecutionIntent, ensure_safety_gates, risk_summary
from execution_prototype.wizard import RiskAcknowledgement, audit_context, require_risk_acknowledgement


CONFIRMATION_PHRASE = "CONFIRM_EXECUTION"


def require_manual_confirmation(value: str) -> None:
    if value != CONFIRMATION_PHRASE:
        raise ValueError("manual confirmation phrase mismatch")


def submit_manual(
    *,
    intent: ExecutionIntent,
    unsigned_tx: Mapping[str, object],
    confirmation: str,
    trade_type_understood: bool = False,
    partial_fill_accepted: bool = False,
    price_impact_understood: bool = False,
    signed_blob: str | None = None,
    submitter: Callable[[str], Mapping[str, object]] | None = None,
    audit_path=None,
) -> dict[str, object]:
    ensure_safety_gates(intent)
    require_risk_acknowledgement(
        RiskAcknowledgement(
            confirmation=confirmation,
            trade_type_understood=trade_type_understood,
            partial_fill_accepted=partial_fill_accepted,
            price_impact_understood=price_impact_understood,
        )
    )
    summary = risk_summary(intent)
    context = audit_context(intent)
    if signed_blob is None or submitter is None:
        append_audit_record(
            intent_id=intent.intent_id,
            tx_type=str(unsigned_tx.get("TransactionType", "unknown")),
            tx_payload=unsigned_tx,
            user_confirmed=True,
            submitted=False,
            **context,
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
        **context,
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

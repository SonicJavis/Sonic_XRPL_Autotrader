from __future__ import annotations

from collections import Counter
from pathlib import Path

from sonic_xrpl.calibration_approval.approval_policy import SAFETY_SUMMARY, evaluate_review
from sonic_xrpl.calibration_approval.models import ApprovalLedger, DETERMINISTIC_CREATED_AT
from sonic_xrpl.calibration_approval.review_record import load_review_payload, review_items, reviewer_from_payload
from sonic_xrpl.calibration_proposal import build_calibration_proposal_pack
from sonic_xrpl.signals.evidence import stable_id


def build_approval_ledger(proposal_fixture: str | Path, review_fixture: str | Path) -> ApprovalLedger:
    pack = build_calibration_proposal_pack(proposal_fixture)
    review_payload = load_review_payload(review_fixture)
    reviewer = reviewer_from_payload(review_payload, str(review_fixture))
    records = []
    change_request_items = []
    for item in review_items(review_payload):
        record, change_request = evaluate_review(pack, reviewer, item)
        records.append(record)
        if change_request is not None:
            change_request_items.append(change_request)
    decision_counts = dict(sorted(Counter(record.decision for record in records).items()))
    request_counts = dict(sorted(Counter(item.status for item in change_request_items).items()))
    limitation_summary = tuple(dict.fromkeys(
        limitation
        for record in records
        for limitation in record.limitation_summary
    ))
    ledger_id = stable_id(
        "cal",
        pack.pack_id,
        tuple(record.approval_record_id for record in records),
        tuple(item.change_request_id for item in change_request_items),
        reviewer.reviewer_id,
        reviewer.reviewed_at,
    )
    return ApprovalLedger(
        ledger_id=ledger_id,
        records=tuple(records),
        change_requests=tuple(change_request_items),
        counts_by_decision=decision_counts,
        counts_by_change_request_status=request_counts,
        blocked_count=decision_counts.get("BLOCKED", 0),
        approved_count=decision_counts.get("APPROVED_FOR_CHANGE_REQUEST", 0),
        invalid_count=decision_counts.get("INVALID_REVIEW", 0),
        generated_at=DETERMINISTIC_CREATED_AT,
        safety_summary=SAFETY_SUMMARY,
        limitation_summary=limitation_summary,
    )

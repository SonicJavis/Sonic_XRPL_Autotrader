from __future__ import annotations

from sonic_xrpl.calibration_approval.models import CalibrationApprovalRecord, CalibrationChangeRequest
from sonic_xrpl.signals.evidence import stable_id


def build_change_request(record: CalibrationApprovalRecord) -> CalibrationChangeRequest:
    before = float(record.proposal_before_value)
    after = float(record.proposal_after_value)
    delta = round(float(record.proposal_delta), 2)
    request_id = stable_id(
        "ccr",
        record.approval_record_id,
        record.proposal_pack_id,
        record.proposal_id,
        before,
        after,
        delta,
    )
    return CalibrationChangeRequest(
        change_request_id=request_id,
        approval_record_id=record.approval_record_id,
        proposal_pack_id=record.proposal_pack_id,
        proposal_id=record.proposal_id,
        requested_change=f"{record.proposal_signal_class}: {before} -> {after}",
        before_value=before,
        after_value=after,
        delta=delta,
        rationale=record.decision_reason,
        required_follow_up=(
            "Open a separate implementation phase if humans accept this request.",
            "Keep runtime configuration unchanged until that future phase is reviewed.",
            "Rerun safety, audit, dependency, and full test validation before any implementation.",
        ),
        status="REQUESTED",
        change_request_only=True,
        apply_allowed=False,
        live_execution_allowed=False,
        runtime_mutation_allowed=False,
        paper_only=True,
        offline_only=True,
    )

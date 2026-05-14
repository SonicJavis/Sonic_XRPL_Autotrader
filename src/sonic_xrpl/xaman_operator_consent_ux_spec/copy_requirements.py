from __future__ import annotations

REQUIRED_COPY_KEYS: tuple[str, ...] = (
    "no_live_execution_disclosure",
    "no_wallet_material_disclosure",
    "payload_not_created_disclosure",
    "signing_submission_unavailable_disclosure",
    "risk_disclosure",
    "source_provenance_section",
    "paper_simulation_assumption_section",
    "stale_missing_evidence_disclosure",
    "operator_acknowledgement",
    "confirmation_phrase_requirement",
)

PROHIBITED_COPY_MARKERS: tuple[str, ...] = (
    "auto_approval",
    "one_click_execution",
    "approved_to_execute",
    "ready_to_sign",
    "ready_to_submit",
    "live_approved",
)

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


DETERMINISTIC_CREATED_AT = "1970-01-01T00:00:00+00:00"
PASS = "PASS"
REVIEW = "REVIEW"
FAIL = "FAIL"


@dataclass(frozen=True)
class RuntimeProfile:
    profile_id: str
    profile_name: str
    created_at: str
    source: str
    source_refs: tuple[str, ...]
    paper_only: bool
    dry_run: bool
    live_execution_allowed: bool
    execution_enabled: bool
    signing_allowed: bool
    submission_allowed: bool
    wallet_material_allowed: bool
    dashboard_mutation_allowed: bool
    calibration_mutation_allowed: bool
    human_review_required: bool
    network_read_policy: str
    runtime_write_policy: str
    safety_statement: str
    limitations: tuple[str, ...]
    warnings: tuple[str, ...]
    allows_network_reads: bool
    allows_runtime_writes: bool
    allows_execution: bool
    allows_signing: bool
    allows_submission: bool
    allows_wallet_material: bool
    allows_dashboard_mutation: bool
    allows_calibration_mutation: bool
    requires_human_review: bool
    env_snapshot: dict[str, str]


@dataclass(frozen=True)
class ConformanceCheck:
    check_id: str
    status: str
    message: str
    evidence: tuple[str, ...]


@dataclass(frozen=True)
class RuntimeProfileConformance:
    conformance_id: str
    created_at: str
    profile_name: str
    status: str
    checks: tuple[ConformanceCheck, ...]
    drift_findings: tuple[str, ...]
    blockers: tuple[str, ...]
    warnings: tuple[str, ...]
    source_refs: tuple[str, ...]
    paper_only: bool
    live_execution_allowed: bool
    runtime_mutation_allowed: bool


def jsonable(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return {
            key: jsonable(getattr(value, key))
            for key in value.__dataclass_fields__
        }
    if isinstance(value, dict):
        return {str(key): jsonable(item) for key, item in sorted(value.items())}
    if isinstance(value, tuple):
        return [jsonable(item) for item in value]
    if isinstance(value, list):
        return [jsonable(item) for item in value]
    return value

from __future__ import annotations

from sonic_xrpl.calibration_implementation_plan.models import ImplementationRollbackPlan
from sonic_xrpl.signals.evidence import stable_id


def build_rollback_plan() -> ImplementationRollbackPlan:
    affected = (
        "src/sonic_xrpl/calibration_implementation_plan/",
        "src/sonic_xrpl/cli/main.py",
        "tests/fixtures/calibration_implementation_plan/",
        "tests/unit/test_phase56_implementation_plan_models.py",
        "tests/unit/test_phase56_implementation_plan_loader.py",
        "tests/unit/test_phase56_implementation_planner.py",
        "tests/unit/test_phase56_dry_run_patch.py",
        "tests/unit/test_phase56_validation_and_rollback_plan.py",
        "tests/unit/test_phase56_report_writer.py",
        "tests/smoke/test_phase56_implementation_plan_cli.py",
        "tests/safety/test_phase56_implementation_plan_safety.py",
        "docs/PHASE56_APPROVED_CALIBRATION_IMPLEMENTATION_PLAN.md",
        "docs/research/PHASE56_APPROVED_CALIBRATION_IMPLEMENTATION_PLAN_RESEARCH.md",
    )
    return ImplementationRollbackPlan(
        rollback_id=stable_id("rbp", "phase56", *affected),
        rollback_steps=(
            "Revert the Phase 56 merge commit.",
            "Re-run safety_grep, audit_validator, dependency_audit, and targeted Phase 56 tests.",
            "Verify reports/phase56 artifacts are removed or regenerated from known-safe inputs.",
            "Confirm runtime calibration settings remain unchanged.",
        ),
        affected_files=affected,
        requires_manual_review=True,
    )

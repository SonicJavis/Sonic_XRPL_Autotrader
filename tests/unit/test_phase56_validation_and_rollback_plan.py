from sonic_xrpl.calibration_implementation_plan.rollback_plan import build_rollback_plan
from sonic_xrpl.calibration_implementation_plan.validation_plan import build_validation_plan


def test_validation_plan_has_required_sections():
    plan = build_validation_plan()
    assert len(plan.required_commands) >= 5
    assert "paper_only=True" in plan.safety_checks
    assert "docs/PHASE56_APPROVED_CALIBRATION_IMPLEMENTATION_PLAN.md" in plan.docs_checks


def test_rollback_plan_is_manual_review_only():
    rollback = build_rollback_plan()
    assert rollback.rollback_id.startswith("rbp_")
    assert rollback.requires_manual_review is True
    assert len(rollback.rollback_steps) >= 3

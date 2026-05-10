from sonic_xrpl.calibration_implementation_plan.models import (
    CalibrationImplementationItem,
    CalibrationImplementationPlan,
    DryRunPatchPreview,
    ImplementationRollbackPlan,
    ImplementationValidationPlan,
)


def test_phase56_model_defaults_are_safe():
    item = CalibrationImplementationItem(
        implementation_item_id="cpi_1",
        change_request_id="ccr_1",
        proposal_id="cp_1",
        target_namespace="paper_calibration",
        target_parameter="watch_threshold",
        current_value=0.5,
        proposed_value=0.48,
        exact_delta=-0.02,
        implementation_status="DRY_RUN_PLANNED",
        target_file_hint="config",
        target_config_key_hint="paper_calibration.watch_threshold",
        dry_run_diff="DRY RUN ONLY",
        validation_commands=(),
        rollback_note="rollback",
        safety_flags={},
        limitations=(),
    )
    patch = DryRunPatchPreview(
        patch_id="drp_1",
        target_file_hint="config",
        target_config_key_hint="paper_calibration.watch_threshold",
        before_value=0.5,
        after_value=0.48,
        diff_text="DRY RUN ONLY",
    )
    validation = ImplementationValidationPlan((), (), (), (), ())
    rollback = ImplementationRollbackPlan("rbp_1", (), ())
    plan = CalibrationImplementationPlan(
        plan_id="cip_1",
        created_at="1970-01-01T00:00:00+00:00",
        phase="56",
        source_ledger_id="ledger",
        source_change_request_count=1,
        implementation_items=(item,),
        blocked_items=(),
        dry_run_patches=(patch,),
        validation_plan=validation,
        rollback_plan=rollback,
        safety_summary="safe",
        limitations=(),
    )
    assert plan.paper_only is True
    assert plan.offline_only is True
    assert plan.dry_run_only is True
    assert plan.auto_apply_allowed is False
    assert plan.live_execution_allowed is False
    assert plan.runtime_mutation_allowed is False
    assert plan.requires_human_implementation is True

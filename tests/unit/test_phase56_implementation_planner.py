from sonic_xrpl.calibration_implementation_plan.planner import build_calibration_implementation_plan


APPROVAL = "reports/phase55/latest_calibration_approval_ledger.json"


def test_approved_change_request_generates_implementation_item():
    plan = build_calibration_implementation_plan(
        APPROVAL,
        "tests/fixtures/calibration_implementation_plan/approved_change_requests.json",
    )
    assert len(plan.implementation_items) == 1
    assert len(plan.blocked_items) == 0
    item = plan.implementation_items[0]
    assert item.target_parameter == "watch_threshold"
    assert "DRY RUN ONLY" in item.dry_run_diff


def test_mixed_requests_generate_blocked_and_planned_items():
    plan = build_calibration_implementation_plan(
        APPROVAL,
        "tests/fixtures/calibration_implementation_plan/mixed_change_requests.json",
    )
    assert len(plan.implementation_items) == 1
    assert len(plan.blocked_items) == 1
    assert plan.blocked_items[0].reason == "unsupported_target_parameter"


def test_invalid_numeric_request_is_blocked():
    plan = build_calibration_implementation_plan(
        APPROVAL,
        "tests/fixtures/calibration_implementation_plan/invalid_numeric_change_request.json",
    )
    assert len(plan.implementation_items) == 0
    assert plan.blocked_items[0].reason == "invalid_numeric_values"


def test_missing_ids_request_is_blocked():
    plan = build_calibration_implementation_plan(
        APPROVAL,
        "tests/fixtures/calibration_implementation_plan/missing_change_request_ids.json",
    )
    assert len(plan.implementation_items) == 0
    assert plan.blocked_items[0].reason == "missing_required_ids"


def test_empty_requests_produce_empty_safe_plan():
    plan = build_calibration_implementation_plan(
        APPROVAL,
        "tests/fixtures/calibration_implementation_plan/empty_change_requests.json",
    )
    assert plan.implementation_items == ()
    assert plan.blocked_items == ()
    assert plan.dry_run_patches == ()

"""V2 Documentation checker — verifies required docs exist."""

from __future__ import annotations

from pathlib import Path

REQUIRED_DOCS = [
    "docs/PROJECT_BLUEPRINT.md",
    "docs/V2_ARCHITECTURE.md",
    "docs/PHASE_LEDGER.md",
    "docs/SYSTEM_STATE.md",
    "docs/LIVE_TRADING_READINESS_GATES.md",
    "docs/AUDIT_VALIDATOR.md",
    "docs/AGENT_OPERATING_RULES.md",
    "docs/SAFETY_MODEL.md",
    "docs/ROADMAP.md",
    "ARCHITECTURE.md",
    "README.md",
    "docs/research/XRPL_RESEARCH_BASELINE.md",
    "docs/audit/pre_v2_repository_audit.md",
    "docs/audit/latest_audit_report.md",
    "docs/audit/latest_audit_report.json",
    "docs/PHASE46_PROVIDER_FIXTURES.md",
    "docs/research/PHASE46_PROVIDER_FIXTURE_RESEARCH.md",
    "docs/PHASE48_DEPENDENCY_AUDIT.md",
    "docs/research/PHASE48_DEPENDENCY_AUDIT_RESEARCH.md",
    "docs/PHASE49_FIRSTLEDGER_SIGNAL_CONTRACTS.md",
    "docs/research/PHASE49_FIRSTLEDGER_SIGNAL_RESEARCH.md",
    "docs/PHASE50_SIGNAL_REVIEW_WORKFLOW.md",
    "docs/research/PHASE50_SIGNAL_REVIEW_RESEARCH.md",
    "docs/PHASE51_PAPER_OUTCOME_ATTRIBUTION.md",
    "docs/research/PHASE51_PAPER_OUTCOME_ATTRIBUTION_RESEARCH.md",
    "docs/PHASE52_OUTCOME_REPLAY_CORPUS.md",
    "docs/research/PHASE52_PAPER_OBSERVATION_CORPUS_RESEARCH.md",
    "docs/PHASE53_CALIBRATION_READINESS_REVIEW.md",
    "docs/research/PHASE53_CALIBRATION_READINESS_RESEARCH.md",
    "docs/PHASE54_HUMAN_REVIEWED_CALIBRATION_PROPOSAL_PACK.md",
    "docs/research/PHASE54_CALIBRATION_PROPOSAL_PACK_RESEARCH.md",
    "docs/PHASE55_HUMAN_REVIEW_APPROVAL_LEDGER.md",
    "docs/research/PHASE55_HUMAN_REVIEW_APPROVAL_LEDGER_RESEARCH.md",
    "docs/PHASE56_APPROVED_CALIBRATION_IMPLEMENTATION_PLAN.md",
    "docs/research/PHASE56_APPROVED_CALIBRATION_IMPLEMENTATION_PLAN_RESEARCH.md",
    "docs/PHASE57_RUNTIME_PROFILE_CONSOLIDATION.md",
    "docs/research/PHASE57_RUNTIME_PROFILE_CONSOLIDATION_RESEARCH.md",
    "docs/PHASE58A_SAFETY_REVIEW_TRIAGE.md",
    "docs/LIVE_READINESS_POLICY.md",
    "docs/CANONICAL_RUNTIME_OWNERSHIP_POLICY.md",
    "docs/XAMAN_FUTURE_INTEGRATION_POLICY.md",
    "docs/FIRSTLEDGER_FUTURE_INGESTION_POLICY.md",
    "docs/POLICY_INDEX.md",
]

REQUIRED_V2_MODULES = [
    "src/sonic_xrpl/__init__.py",
    "src/sonic_xrpl/core/modes.py",
    "src/sonic_xrpl/core/errors.py",
    "src/sonic_xrpl/execution/live_guard.py",
    "src/sonic_xrpl/protocol/amendments.py",
    "src/sonic_xrpl/protocol/capability_matrix.py",
    "src/sonic_xrpl/reconciliation/legacy_phase30_adapter.py",
    "src/sonic_xrpl/signals/models.py",
    "src/sonic_xrpl/signals/classifier.py",
    "src/sonic_xrpl/review/models.py",
    "src/sonic_xrpl/outcomes/models.py",
    "src/sonic_xrpl/outcomes/attribution.py",
    "src/sonic_xrpl/outcomes/feedback.py",
    "src/sonic_xrpl/outcome_corpus/models.py",
    "src/sonic_xrpl/outcome_corpus/builder.py",
    "src/sonic_xrpl/outcome_corpus/quality.py",
    "src/sonic_xrpl/outcome_corpus/report_writer.py",
    "src/sonic_xrpl/calibration_review/models.py",
    "src/sonic_xrpl/calibration_review/readiness.py",
    "src/sonic_xrpl/calibration_review/recommendations.py",
    "src/sonic_xrpl/calibration_review/report_writer.py",
    "src/sonic_xrpl/calibration_proposal/models.py",
    "src/sonic_xrpl/calibration_proposal/proposal_builder.py",
    "src/sonic_xrpl/calibration_proposal/report_writer.py",
    "src/sonic_xrpl/calibration_approval/models.py",
    "src/sonic_xrpl/calibration_approval/approval_policy.py",
    "src/sonic_xrpl/calibration_approval/change_request.py",
    "src/sonic_xrpl/calibration_approval/ledger.py",
    "src/sonic_xrpl/calibration_approval/report_writer.py",
    "src/sonic_xrpl/calibration_implementation_plan/models.py",
    "src/sonic_xrpl/calibration_implementation_plan/loader.py",
    "src/sonic_xrpl/calibration_implementation_plan/planner.py",
    "src/sonic_xrpl/calibration_implementation_plan/dry_run_patch.py",
    "src/sonic_xrpl/calibration_implementation_plan/report_writer.py",
    "src/sonic_xrpl/runtime_profile/models.py",
    "src/sonic_xrpl/runtime_profile/profiles.py",
    "src/sonic_xrpl/runtime_profile/conformance.py",
    "src/sonic_xrpl/runtime_profile/report_writer.py",
]

REQUIRED_TEST_FILES = [
    "tests/unit/test_modes.py",
    "tests/unit/test_live_guard.py",
    "tests/unit/test_capability_matrix.py",
    "tests/safety/test_safety_scan.py",
    "tests/safety/test_dependency_audit.py",
    "tests/smoke/test_imports.py",
    "tests/unit/test_firstledger_signal_classifier.py",
    "tests/smoke/test_firstledger_signal_cli.py",
    "tests/safety/test_firstledger_signal_safety.py",
    "tests/unit/test_phase50_review_models.py",
    "tests/unit/test_phase50_review_policy.py",
    "tests/unit/test_phase51_outcome_attribution.py",
    "tests/smoke/test_phase51_outcome_cli.py",
    "tests/unit/test_phase52_outcome_corpus_models.py",
    "tests/unit/test_phase52_outcome_corpus_builder.py",
    "tests/unit/test_phase52_outcome_corpus_quality.py",
    "tests/smoke/test_phase52_outcome_corpus_cli.py",
    "tests/safety/test_phase52_outcome_corpus_safety.py",
    "tests/unit/test_phase53_calibration_models.py",
    "tests/unit/test_phase53_calibration_readiness.py",
    "tests/unit/test_phase53_calibration_recommendations.py",
    "tests/unit/test_phase53_calibration_report_writer.py",
    "tests/smoke/test_phase53_calibration_cli.py",
    "tests/safety/test_phase53_calibration_safety.py",
    "tests/unit/test_phase54_calibration_proposal_models.py",
    "tests/unit/test_phase54_calibration_proposal_builder.py",
    "tests/unit/test_phase54_calibration_proposal_diff.py",
    "tests/unit/test_phase54_calibration_proposal_report_writer.py",
    "tests/smoke/test_phase54_calibration_proposal_cli.py",
    "tests/safety/test_phase54_calibration_proposal_safety.py",
    "tests/unit/test_phase55_approval_models.py",
    "tests/unit/test_phase55_approval_policy.py",
    "tests/unit/test_phase55_change_request.py",
    "tests/unit/test_phase55_approval_ledger.py",
    "tests/unit/test_phase55_approval_report_writer.py",
    "tests/smoke/test_phase55_approval_cli.py",
    "tests/safety/test_phase55_approval_safety.py",
    "tests/unit/test_phase56_implementation_plan_models.py",
    "tests/unit/test_phase56_implementation_plan_loader.py",
    "tests/unit/test_phase56_implementation_planner.py",
    "tests/unit/test_phase56_dry_run_patch.py",
    "tests/unit/test_phase56_validation_and_rollback_plan.py",
    "tests/unit/test_phase56_report_writer.py",
    "tests/smoke/test_phase56_implementation_plan_cli.py",
    "tests/safety/test_phase56_implementation_plan_safety.py",
    "tests/unit/test_phase57_runtime_profile_models.py",
    "tests/unit/test_phase57_runtime_profile_conformance.py",
    "tests/unit/test_phase57_runtime_profile_report_writer.py",
    "tests/smoke/test_phase57_runtime_profile_cli.py",
    "tests/safety/test_phase57_runtime_profile_safety.py",
    "tests/safety/test_guard_critical_changes.py",
    "tests/safety/test_phase58b_policy_docs.py",
]


def check_docs_exist(repo_root: Path) -> list[tuple[str, bool, str]]:
    """Check all required documentation files exist.

    Returns list of (path, exists, message) tuples.
    """
    results = []
    for doc_path in REQUIRED_DOCS:
        full = repo_root / doc_path
        exists = full.exists()
        results.append((
            doc_path,
            exists,
            "OK" if exists else f"MISSING: {doc_path}",
        ))
    return results


def check_modules_exist(repo_root: Path) -> list[tuple[str, bool, str]]:
    """Check all required V2 modules exist."""
    results = []
    for mod_path in REQUIRED_V2_MODULES:
        full = repo_root / mod_path
        exists = full.exists()
        results.append((
            mod_path,
            exists,
            "OK" if exists else f"MISSING: {mod_path}",
        ))
    return results


def check_tests_exist(repo_root: Path) -> list[tuple[str, bool, str]]:
    """Check required test files exist."""
    results = []
    for test_path in REQUIRED_TEST_FILES:
        full = repo_root / test_path
        exists = full.exists()
        results.append((
            test_path,
            exists,
            "OK" if exists else f"MISSING: {test_path}",
        ))
    return results

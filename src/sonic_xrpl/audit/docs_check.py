"""V2 Documentation checker — verifies required docs exist."""

from __future__ import annotations

from pathlib import Path

REQUIRED_DOCS = [
    "docs/PROJECT_BLUEPRINT.md",
    "docs/V2_ARCHITECTURE.md",
    "docs/PHASE_LEDGER.md",
    "docs/AGENT_OPERATING_RULES.md",
    "docs/SAFETY_MODEL.md",
    "docs/ROADMAP.md",
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

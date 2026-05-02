"""Safety scan tests — verifies the V2 safety scanner works correctly."""

from __future__ import annotations

from pathlib import Path
import pytest

from sonic_xrpl.audit.safety_scan import (
    SafetyClassification,
    SafetyFinding,
    classify_finding,
    run_safety_scan,
    get_blocked_findings,
    get_review_findings,
)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def test_safety_scan_runs_without_error():
    """run_safety_scan() completes without raising exceptions."""
    findings = run_safety_scan(REPO_ROOT)
    assert isinstance(findings, list)


def test_safety_scan_returns_findings():
    """Safety scan finds something in the repo (it has docs/tests mentioning these terms)."""
    findings = run_safety_scan(REPO_ROOT)
    assert len(findings) > 0


def test_no_blocked_findings_in_v2_src():
    """V2 source code should have no BLOCKED findings."""
    findings = run_safety_scan(REPO_ROOT)
    blocked = get_blocked_findings(findings)
    # Filter to only V2 src findings
    v2_blocked = [
        f for f in blocked
        if f.file_path.startswith("src/sonic_xrpl/")
    ]
    assert v2_blocked == [], f"Blocked findings in V2 src: {v2_blocked}"


def test_doc_file_classified_as_documentation():
    """Patterns in .md files are ALLOWED_DOCUMENTATION."""
    finding = classify_finding(
        file_path="docs/SAFETY_MODEL.md",
        line_no=1,
        line_content="This discusses private_key handling",
        pattern=r"\bprivate_key\b",
        all_lines=["This discusses private_key handling"],
    )
    assert finding.classification == SafetyClassification.ALLOWED_DOCUMENTATION


def test_test_file_classified_as_test_fixture():
    """Patterns in test files are ALLOWED_TEST_FIXTURE."""
    finding = classify_finding(
        file_path="tests/unit/test_live_guard.py",
        line_no=1,
        line_content="    # test that wallet construction is blocked",
        pattern=r"\bwallet\b",
        all_lines=["    # test that wallet construction is blocked"],
    )
    assert finding.classification in (
        SafetyClassification.ALLOWED_TEST_FIXTURE,
        SafetyClassification.ALLOWED_DOCUMENTATION,
    )


def test_live_guard_file_classified_as_interface():
    """live_guard.py patterns are ALLOWED_INTERFACE_ONLY."""
    finding = classify_finding(
        file_path="src/sonic_xrpl/execution/live_guard.py",
        line_no=10,
        line_content="def block_signing() -> None:",
        pattern=r"\bsign\b",
        all_lines=["def block_signing() -> None:"],
    )
    assert finding.classification == SafetyClassification.ALLOWED_INTERFACE_ONLY

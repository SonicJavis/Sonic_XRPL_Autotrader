"""Phase 58A guard-critical file change detector.

Detects changes to safety-critical files and paths so they always receive
explicit review attention.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

CRITICAL_PREFIXES = (
    ".github/workflows/",
    "src/sonic_xrpl/audit/",
    "src/sonic_xrpl/execution/",
    "app/execution/",
)

CRITICAL_FILES = {
    "scripts/safety_grep.py",
    "scripts/audit_validator.py",
    "scripts/dependency_audit.py",
    "scripts/guard_critical_changes.py",
    "docs/SAFETY_MODEL.md",
    "docs/AGENT_OPERATING_RULES.md",
    "docs/CANONICAL_PATH_DECISION.md",
    "docs/ROADMAP.md",
    "docs/PHASE_LEDGER.md",
    "docs/PHASE58A_SAFETY_REVIEW_TRIAGE.md",
    "docs/LIVE_READINESS_POLICY.md",
    "docs/CANONICAL_RUNTIME_OWNERSHIP_POLICY.md",
    "docs/XAMAN_FUTURE_INTEGRATION_POLICY.md",
    "docs/FIRSTLEDGER_FUTURE_INGESTION_POLICY.md",
    "docs/POLICY_INDEX.md",
    "docs/MIGRATION_SAFE_CONTROL_CHECKS.md",
    "docs/MIGRATION_READINESS_MATRIX.md",
    "scripts/migration_safe_check.py",
    "docs/PHASE60_PAPER_SNIPER_SIMULATION_HARNESS.md",
    "docs/PHASE61_XAMAN_MANUAL_APPROVAL_DESIGN_SPEC.md",
    "docs/PHASE62_XAMAN_TESTNET_PAYLOAD_SCHEMA_REVIEW.md",
    "docs/PHASE63_XAMAN_CALLBACK_REPLAY_VERIFICATION_SPEC.md",
    "docs/PHASE64_XAMAN_AUDIT_IDEMPOTENCY_STORE_SPEC.md",
    "docs/PHASE65_XAMAN_APPROVAL_STATE_MACHINE_SPEC.md",
    "docs/PHASE66_XAMAN_OPERATOR_CONSENT_UX_SPEC.md",
    "docs/PHASE67_XAMAN_CONSENT_EVIDENCE_PACK_SPEC.md",
}


def _run_git_diff(base_ref: str, head_ref: str) -> list[str]:
    cmd = ["git", "diff", "--name-only", f"{base_ref}...{head_ref}"]
    result = subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        cmd = ["git", "diff", "--name-only", f"{base_ref}..{head_ref}"]
        result = subprocess.run(
            cmd,
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
    if result.returncode != 0:
        refs_result = subprocess.run(
            ["git", "show-ref", "--heads", "--remotes"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        available_refs = refs_result.stdout.strip() or "(no refs returned by git show-ref)"
        suggested_fix = (
            "Fetch the base ref in CI and pass explicit refs. "
            f"Example: git fetch origin <base>:refs/remotes/origin/<base>; "
            f"python scripts/guard_critical_changes.py --base origin/<base> --head {head_ref}"
        )
        raise RuntimeError(
            "Unable to compute changed files. "
            f"base={base_ref} head={head_ref} stderr={result.stderr.strip()} "
            f"available_refs={available_refs} suggested_fix={suggested_fix}"
        )
    return [line.strip().replace("\\", "/") for line in result.stdout.splitlines() if line.strip()]


def is_guard_critical(path: str) -> bool:
    if path in CRITICAL_FILES:
        return True
    return any(path.startswith(prefix) for prefix in CRITICAL_PREFIXES)


def find_guard_critical_changes(changed_files: list[str]) -> list[str]:
    return sorted([path for path in changed_files if is_guard_critical(path)])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Detect guard-critical file changes.")
    parser.add_argument("--base-ref", "--base", dest="base_ref", default="origin/main", help="Base git ref for diff.")
    parser.add_argument("--head-ref", "--head", dest="head_ref", default="HEAD", help="Head git ref for diff.")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero if guard-critical files changed.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        changed = _run_git_diff(args.base_ref, args.head_ref)
    except RuntimeError as exc:
        print(f"ERROR: {exc}")
        return 2

    critical = find_guard_critical_changes(changed)
    if not critical:
        print("PASS: no guard-critical files changed.")
        return 0

    print("REVIEW: guard-critical files changed:")
    for path in critical:
        print(f"- {path}")

    if args.strict:
        print("FAIL: strict mode enabled; guard-critical changes require explicit security review.")
        return 1
    print("PASS: non-strict mode; review required.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

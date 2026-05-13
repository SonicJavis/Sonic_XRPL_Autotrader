"""Phase 58C migration-safe control check script.

Deterministically verifies that migration-safety invariants are satisfied:
- Required policy docs exist.
- Required migration matrix exists.
- Key safety phrases are present in policy docs.
- app/ and src/sonic_xrpl/ entry points remain present.
- Live guard and execution guard files are present.
- Prohibited live-authorization phrases are absent from policy docs.

No network access. No external dependencies. Does not modify files.
Exits 0 on pass, 1 on any invariant violation.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# Required files
# ---------------------------------------------------------------------------

REQUIRED_DOCS = [
    "docs/MIGRATION_SAFE_CONTROL_CHECKS.md",
    "docs/MIGRATION_READINESS_MATRIX.md",
    "docs/LIVE_READINESS_POLICY.md",
    "docs/CANONICAL_RUNTIME_OWNERSHIP_POLICY.md",
    "docs/POLICY_INDEX.md",
    "docs/SAFETY_MODEL.md",
]

REQUIRED_RUNTIME_FILES = [
    "app/main.py",
    "src/sonic_xrpl/cli/main.py",
    "src/sonic_xrpl/execution/live_guard.py",
    "app/execution/execution_guard.py",
]

OPTIONAL_PROTOTYPE_FILES = [
    "execution_prototype/README.md",
]

# ---------------------------------------------------------------------------
# Required key phrases (lowercase) per doc path
# ---------------------------------------------------------------------------

REQUIRED_PHRASES: dict[str, list[str]] = {
    "docs/MIGRATION_SAFE_CONTROL_CHECKS.md": [
        "does not perform runtime migration",
        "does not change runtime ownership",
        "does not authorize live trading",
        "app/` remains the current runnable legacy api/paper runtime",
        "src/sonic_xrpl/` remains the canonical future runtime target",
        "execution_prototype/` remains historical/reference-only",
        "explicit future phase approval",
        "parity gates",
        "safety gates",
        "rollback gates",
        "docs gates",
        "audit gates",
        "runtime cutover is separate from migration readiness",
        "live enablement is separate from runtime migration",
        "still no live execution",
    ],
    "docs/MIGRATION_READINESS_MATRIX.md": [
        "no runtime cutover is performed here",
        "live execution is not authorized here",
        "blocked/not-started",
        "not-cutover",
        "app/",
        "src/sonic_xrpl/",
        "execution_prototype/",
    ],
    "docs/LIVE_READINESS_POLICY.md": [
        "live trading remains blocked",
        "does not authorize live trading",
    ],
    "docs/CANONICAL_RUNTIME_OWNERSHIP_POLICY.md": [
        "`src/sonic_xrpl/` is the canonical future runtime target",
        "`app/` is the current runnable legacy api/paper runtime surface",
        "`execution_prototype/` is historical/reference-only",
    ],
    "docs/POLICY_INDEX.md": [
        "live readiness policy",
        "canonical runtime ownership policy",
    ],
}

# ---------------------------------------------------------------------------
# Prohibited live-authorization phrases (lowercase) — must be ABSENT
# ---------------------------------------------------------------------------

PROHIBITED_PHRASES = (
    "live execution is authorized",
    "live trading is authorized",
    "phase 58c authorizes live",
    "phase 58c enables live",
    "migration is complete",
    "cutover is complete",
    "runtime cutover is authorized",
)

# ---------------------------------------------------------------------------
# Check functions
# ---------------------------------------------------------------------------


def check_required_docs(results: list[tuple[str, bool, str]]) -> None:
    for rel in REQUIRED_DOCS:
        path = REPO_ROOT / rel
        if path.exists():
            results.append((rel, True, "PASS: required doc present"))
        else:
            results.append((rel, False, f"FAIL: required doc missing: {rel}"))


def check_required_runtime_files(results: list[tuple[str, bool, str]]) -> None:
    for rel in REQUIRED_RUNTIME_FILES:
        path = REPO_ROOT / rel
        if path.exists():
            results.append((rel, True, "PASS: required runtime file present"))
        else:
            results.append((rel, False, f"FAIL: required runtime file missing: {rel}"))


def check_optional_prototype_files(results: list[tuple[str, bool, str]]) -> None:
    for rel in OPTIONAL_PROTOTYPE_FILES:
        path = REPO_ROOT / rel
        if path.exists():
            results.append((rel, True, "PASS: prototype file present"))
        else:
            results.append((rel, True, f"INFO: optional prototype file not found (acceptable): {rel}"))


def check_required_phrases(results: list[tuple[str, bool, str]]) -> None:
    for rel, phrases in REQUIRED_PHRASES.items():
        path = REPO_ROOT / rel
        if not path.exists():
            results.append((rel, False, f"FAIL: doc missing, cannot check phrases: {rel}"))
            continue
        text = path.read_text(encoding="utf-8").lower()
        for phrase in phrases:
            if phrase in text:
                results.append((f"{rel}:phrase:{phrase[:40]}", True, f"PASS: phrase present in {rel}"))
            else:
                results.append((
                    f"{rel}:phrase:{phrase[:40]}",
                    False,
                    f"FAIL: required phrase missing in {rel}: {phrase!r}",
                ))


def check_prohibited_phrases(results: list[tuple[str, bool, str]]) -> None:
    docs_to_scan = list(REQUIRED_PHRASES.keys())
    for rel in docs_to_scan:
        path = REPO_ROOT / rel
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8").lower()
        for phrase in PROHIBITED_PHRASES:
            if phrase in text:
                results.append((
                    f"{rel}:prohibited:{phrase[:40]}",
                    False,
                    f"FAIL: prohibited live-authorization phrase found in {rel}: {phrase!r}",
                ))
            else:
                results.append((
                    f"{rel}:prohibited:{phrase[:40]}",
                    True,
                    f"PASS: prohibited phrase absent in {rel}",
                ))


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------


def emit_report(results: list[tuple[str, bool, str]]) -> bool:
    """Print a readable report. Returns True if all checks passed."""
    all_passed = True
    failures: list[str] = []
    passes: list[str] = []
    infos: list[str] = []

    for _key, passed, message in results:
        if message.startswith("INFO:"):
            infos.append(message)
        elif passed:
            passes.append(message)
        else:
            all_passed = False
            failures.append(message)

    print("=" * 72)
    print("Migration-Safe Control Check Report")
    print("=" * 72)

    for msg in passes:
        print(msg)
    for msg in infos:
        print(msg)

    if failures:
        print()
        print("--- FAILURES ---")
        for msg in failures:
            print(msg)
        print()
        print(f"RESULT: FAIL — {len(failures)} invariant(s) violated.")
    else:
        print()
        print(f"RESULT: PASS — all {len(passes)} migration-safety invariants satisfied.")

    print("=" * 72)
    print("Still no live execution.")
    print("=" * 72)
    return all_passed


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def run_checks() -> list[tuple[str, bool, str]]:
    results: list[tuple[str, bool, str]] = []
    check_required_docs(results)
    check_required_runtime_files(results)
    check_optional_prototype_files(results)
    check_required_phrases(results)
    check_prohibited_phrases(results)
    return results


def main() -> int:
    results = run_checks()
    passed = emit_report(results)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())

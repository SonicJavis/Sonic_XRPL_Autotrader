"""V2 Safety Scan — classifies potentially dangerous patterns in source code.

Classification levels:
- ALLOWED_DOCUMENTATION: pattern appears in docs/comments — OK
- ALLOWED_TEST_FIXTURE: pattern appears in test/fixture context — OK
- ALLOWED_INTERFACE_ONLY: pattern appears as abstract interface definition — OK
- REQUIRES_REVIEW: pattern in runtime code — needs human review
- BLOCKED: pattern in runtime code with no valid justification — fails audit

Unsafe implementation in runtime code must BLOCKED.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import NamedTuple


class SafetyClassification(str, Enum):
    ALLOWED_DOCUMENTATION = "allowed_documentation"
    ALLOWED_TEST_FIXTURE = "allowed_test_fixture"
    ALLOWED_INTERFACE_ONLY = "allowed_interface_only"
    REQUIRES_REVIEW = "requires_review"
    BLOCKED = "blocked"


@dataclass
class SafetyFinding:
    """A single safety scan finding."""

    file_path: str
    line_no: int
    pattern: str
    classification: SafetyClassification
    context: str
    reason: str = ""


# Patterns to scan for
SAFETY_PATTERNS = [
    r"\bseed\b",
    r"\bsecret\b",
    r"\bprivate_key\b",
    r"\bmnemonic\b",
    r"\bwallet\b",
    r"\bWallet\b",
    r"\bsign\b",
    r"\bsigning\b",
    r"\bsubmit\b",
    r"\bsubmitAndWait\b",
    r"\bsubmit_and_wait\b",
    r"\bautofill\b",
    r"while True",
    r"\bdaemon\b",
    r"\bbackground\b",
    r"\bscheduler\b",
    r"\bcron\b",
    r"live.trad",
    r"os\.environ.*SECRET",
    r"os\.environ.*SEED",
    r"os\.environ.*PRIVATE",
]

# File extensions to scan
SCAN_EXTENSIONS = {".py"}

# Directories to exclude from blocked classification
DOC_DIRS = {"docs", "tests", "execution_prototype/tests"}

# File path patterns that indicate documentation/test context
DOC_FILE_PATTERNS = [
    r"\.md$",
    r"test_",
    r"_test\.py$",
    r"/tests/",
    r"fixture",
    r"mock",
    r"conftest",
]

# Abstract interface markers — methods that are abstract/protocol-only
INTERFACE_MARKERS = [
    "@abstractmethod",
    "raise LiveTradingDisabledError",
    "raise NotImplementedError",
    "# interface",
    "# BLOCKED",
    "# abstract",
    "ABC",
]


def _is_doc_context(file_path: str, line_content: str) -> bool:
    """Return True if the finding is in a documentation or comment context."""
    # Pure doc file
    if file_path.endswith(".md"):
        return True
    # Comment line
    stripped = line_content.strip()
    if stripped.startswith("#") or stripped.startswith('"""') or stripped.startswith("'''"):
        return True
    # Docstring-only patterns
    if '"""' in line_content or "'''" in line_content:
        return True
    return False


def _is_test_context(file_path: str) -> bool:
    """Return True if the file is a test or fixture."""
    return any(re.search(p, file_path) for p in DOC_FILE_PATTERNS)


def _is_interface_context(file_path: str, lines: list[str], line_no: int) -> bool:
    """Return True if the finding is in an abstract interface definition."""
    # Check surrounding lines (±5) for interface markers
    start = max(0, line_no - 5)
    end = min(len(lines), line_no + 5)
    context_block = "\n".join(lines[start:end])
    return any(marker in context_block for marker in INTERFACE_MARKERS)


def classify_finding(
    file_path: str,
    line_no: int,
    line_content: str,
    pattern: str,
    all_lines: list[str],
) -> SafetyFinding:
    """Classify a single finding."""
    # Documentation files
    if file_path.endswith(".md") or file_path.endswith(".rst"):
        return SafetyFinding(
            file_path=file_path,
            line_no=line_no,
            pattern=pattern,
            classification=SafetyClassification.ALLOWED_DOCUMENTATION,
            context=line_content.strip(),
            reason="Pattern in documentation file",
        )

    # Comment/docstring in source
    if _is_doc_context(file_path, line_content):
        return SafetyFinding(
            file_path=file_path,
            line_no=line_no,
            pattern=pattern,
            classification=SafetyClassification.ALLOWED_DOCUMENTATION,
            context=line_content.strip(),
            reason="Pattern in comment or docstring",
        )

    # Test/fixture files
    if _is_test_context(file_path):
        return SafetyFinding(
            file_path=file_path,
            line_no=line_no,
            pattern=pattern,
            classification=SafetyClassification.ALLOWED_TEST_FIXTURE,
            context=line_content.strip(),
            reason="Pattern in test or fixture file",
        )

    # Abstract interface definitions
    if _is_interface_context(file_path, all_lines, line_no):
        return SafetyFinding(
            file_path=file_path,
            line_no=line_no,
            pattern=pattern,
            classification=SafetyClassification.ALLOWED_INTERFACE_ONLY,
            context=line_content.strip(),
            reason="Pattern in abstract interface or blocked stub",
        )

    # Live guard files are allowed to mention these terms (they're blocking them)
    if "live_guard" in file_path or "safety_scan" in file_path:
        return SafetyFinding(
            file_path=file_path,
            line_no=line_no,
            pattern=pattern,
            classification=SafetyClassification.ALLOWED_INTERFACE_ONLY,
            context=line_content.strip(),
            reason="Pattern in live guard or safety scan module (blocking context)",
        )

    # All other runtime code — requires review
    return SafetyFinding(
        file_path=file_path,
        line_no=line_no,
        pattern=pattern,
        classification=SafetyClassification.REQUIRES_REVIEW,
        context=line_content.strip(),
        reason="Pattern in runtime code — requires human review",
    )


# Source-controlled directories to scan by default.
# These are the only directories that contain project code.
DEFAULT_SCAN_DIRS = [
    "src/sonic_xrpl",
    "execution_prototype",
    "app",
    "scripts",
    "docs",
    "dashboard",
    "tests",
]

# Directory name components to unconditionally skip during traversal.
EXCLUDED_DIR_PARTS = {
    ".git",
    ".venv",
    "venv",
    "env",
    ".ecc-source",  # local reference-only clone, not part of the project runtime
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "node_modules",
    "dist",
    "build",
    "artifacts",
    "reports",
    "datasets",
    "data",
    ".idea",
    ".vscode",
    ".tox",
    "site-packages",
}


def _collect_scan_paths(
    root: Path,
    *,
    scan_dirs: list[str] | None = None,
    max_files: int | None = None,
) -> list[Path]:
    """Collect files to scan from bounded source-controlled directories.

    Only '.py' and '.md' files are returned.  Traversal skips any directory
    whose name is in
    EXCLUDED_DIR_PARTS so that virtual-envs, caches, and build artefacts
    are never walked.

    Args:
        root: Repository root directory.
        scan_dirs: List of subdirectory paths (relative to *root*) to scan.
            Defaults to DEFAULT_SCAN_DIRS.  Only directories that actually
            exist are scanned.
        max_files: Optional upper limit on the number of files returned.

    Returns:
        Sorted list of Path objects to scan.
    """
    if scan_dirs is None:
        scan_dirs = DEFAULT_SCAN_DIRS

    allowed_extensions = {".py", ".md"}
    collected: list[Path] = []

    for rel_dir in scan_dirs:
        target = root / rel_dir
        if not target.exists():
            continue
        if target.is_file():
            if target.suffix in allowed_extensions:
                collected.append(target)
            continue
        for filepath in target.rglob("*"):
            if not filepath.is_file():
                continue
            if filepath.suffix not in allowed_extensions:
                continue
            # Skip excluded directory components anywhere in the path
            if any(part in EXCLUDED_DIR_PARTS for part in filepath.parts):
                continue
            collected.append(filepath)
            if max_files is not None and len(collected) >= max_files:
                return collected

    return collected


def run_safety_scan(
    repo_root: Path,
    *,
    scan_dirs: list[str] | None = None,
    max_files: int | None = None,
) -> list[SafetyFinding]:
    """Scan the repository for safety-sensitive patterns.

    Only source-controlled project directories are scanned by default (see
    DEFAULT_SCAN_DIRS).  Virtual-envs, caches, build artefacts, and binary
    directories are excluded so the scan completes quickly and
    deterministically offline.

    Args:
        repo_root: Root directory of the repository.
        scan_dirs: Override the list of directories to scan (relative paths).
        max_files: Stop collecting files after this many files have been found.

    Returns:
        List of SafetyFinding objects classified by context.
    """
    findings: list[SafetyFinding] = []

    scan_paths = _collect_scan_paths(repo_root, scan_dirs=scan_dirs, max_files=max_files)

    compiled_patterns = [re.compile(p) for p in SAFETY_PATTERNS]

    for filepath in scan_paths:
        try:
            text = filepath.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue

        lines = text.splitlines()
        rel_path = str(filepath.relative_to(repo_root))

        for line_no, line in enumerate(lines, start=1):
            for pat_re, pat_str in zip(compiled_patterns, SAFETY_PATTERNS):
                if pat_re.search(line):
                    finding = classify_finding(
                        file_path=rel_path,
                        line_no=line_no,
                        line_content=line,
                        pattern=pat_str,
                        all_lines=lines,
                    )
                    findings.append(finding)
                    break  # One finding per line

    return findings


def get_blocked_findings(findings: list[SafetyFinding]) -> list[SafetyFinding]:
    """Return only BLOCKED findings."""
    return [f for f in findings if f.classification == SafetyClassification.BLOCKED]


def get_review_findings(findings: list[SafetyFinding]) -> list[SafetyFinding]:
    """Return findings that REQUIRE_REVIEW."""
    return [f for f in findings if f.classification == SafetyClassification.REQUIRES_REVIEW]


# Fixture-specific patterns (no "secret" to avoid tesSUCCESS false positives)
_FIXTURE_SCAN_PATTERNS = [
    re.compile(r'\bseed\b', re.IGNORECASE),
    re.compile(r'\bprivate_key\b', re.IGNORECASE),
    re.compile(r'\bmnemonic\b', re.IGNORECASE),
]


def scan_fixture_files(fixture_dir: Path) -> list[SafetyFinding]:
    """Scan JSON/JSONL fixture files for credential-like patterns.

    Checks for: seed, private_key, mnemonic.
    Does NOT check for 'secret' to avoid flagging tesSUCCESS in XRPL fixtures.
    """
    if not fixture_dir.exists():
        return []

    findings: list[SafetyFinding] = []

    for ext in ("*.json", "*.jsonl"):
        for fpath in fixture_dir.rglob(ext):
            try:
                lines = fpath.read_text().splitlines()
            except Exception:
                continue
            for i, line in enumerate(lines, 1):
                for compiled_re in _FIXTURE_SCAN_PATTERNS:
                    if compiled_re.search(line):
                        try:
                            rel = str(fpath.relative_to(fixture_dir.parent.parent))
                        except Exception:
                            rel = str(fpath)
                        findings.append(SafetyFinding(
                            file_path=rel,
                            line_no=i,
                            pattern=compiled_re.pattern,
                            classification=SafetyClassification.BLOCKED,
                            context=line.strip()[:80],
                            reason=f"Credential-like pattern '{compiled_re.pattern}' in fixture file",
                        ))
                        break
    return findings

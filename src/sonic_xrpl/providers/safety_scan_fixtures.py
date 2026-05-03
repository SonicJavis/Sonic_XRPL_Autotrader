"""Safety scan for fixture files — separate from main safety_scan to avoid circular imports."""
from __future__ import annotations

import re
from pathlib import Path
from sonic_xrpl.audit.safety_scan import SafetyFinding, SafetyClassification

_SECRET_FIXTURE_PATTERNS = [
    r'\bseed\b',
    r'\bprivate_key\b',
    r'\bmnemonic\b',
]


def scan_fixture_files(fixture_dir: Path) -> list[SafetyFinding]:
    """Scan JSON/JSONL fixture files for secret patterns.

    Patterns checked: seed, private_key, mnemonic (NOT secret to avoid tesSUCCESS false positives).
    """
    if not fixture_dir.exists():
        return []

    findings = []
    compiled = [(pat, re.compile(pat, re.IGNORECASE)) for pat in _SECRET_FIXTURE_PATTERNS]

    for ext in ("*.json", "*.jsonl"):
        for fpath in fixture_dir.rglob(ext):
            try:
                lines = fpath.read_text().splitlines()
            except Exception:
                continue
            for i, line in enumerate(lines, 1):
                for pat, compiled_re in compiled:
                    if compiled_re.search(line):
                        try:
                            rel = str(fpath.relative_to(fixture_dir.parent.parent))
                        except Exception:
                            rel = str(fpath)
                        findings.append(SafetyFinding(
                            file_path=rel,
                            line_no=i,
                            pattern=pat,
                            classification=SafetyClassification.BLOCKED,
                            context=line.strip()[:80],
                            reason=f"Potential secret pattern '{pat}' found in fixture file",
                        ))
                        break
    return findings

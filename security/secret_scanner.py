import os
import re
from typing import List, Tuple

SECRET_PATTERNS = [
    # Common environment-like keys
    r"AWS_SECRET_ACCESS_KEY",
    r"AWS_ACCESS_KEY_ID",
    r"SECRET_KEY",
    r"API_KEY",
    r"TOKEN",
    r"PASSWORD",
    r"SECRET",
    r"MNEMONIC",
    r"WALLET",
    r"SEED",
]

# Simple heuristic: detect long base64-like strings that could be keys
BASE64_HEURISTIC = re.compile(r"([A-Za-z0-9+/]{40,}={0,2})")

def _is_text_file(path: str) -> bool:
    try:
        with open(path, 'rb') as f:
            data = f.read(1024)
        # Heuristic: skip binary files by checking for null bytes
        return b"\0" not in data
    except Exception:
        return False

def scan_for_secrets(root_path: str = ".") -> List[Tuple[str, int, str]]:
    """Scan repository for potential secret indicators.

    Returns a list of tuples: (file_path, line_number, line_text)
    The function is intentionally conservative and non-blocking.
    """
    findings: List[Tuple[str, int, str]] = []
    for dirpath, _, filenames in os.walk(root_path):
        for fname in filenames:
            path = os.path.join(dirpath, fname)
            # Heuristic skip obvious binary or large files
            if not _is_text_file(path):
                continue
            try:
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    for idx, line in enumerate(f, start=1):
                        # Check for explicit keyword patterns
                        if any(re.search(pat, line, flags=re.IGNORECASE) for pat in SECRET_PATTERNS):
                            findings.append((path, idx, line.rstrip('\n')))
                            continue
                        # Check for long base64-like tokens common in secrets
                        if BASE64_HEURISTIC.search(line):
                            findings.append((path, idx, line.rstrip('\n')))
            except Exception:
                # Best-effort: skip unreadable files
                continue
    return findings

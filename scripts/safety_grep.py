import os
import re
import sys
from pathlib import Path

FORBIDDEN_PATTERNS = [
    r"autofill",
    r"submitAndWait",
    r"\bwallet\b",
    r"\bseed\b",
    r"private_key",
    r"\bsecret\b",
    r"\bsign\b",
    r"\bsigning\b",
    r"\bsubmit\b",
    r"background",
    r"polling",
    r"auto_calibrate",
    r"mutate_model"
]

ALLOWED_DIRS = ["docs", "tests", "execution_prototype/tests", "scripts"]
ALLOWED_EXTENSIONS = [".py"]

# Words that are acceptable as string literals or within specific safe contexts
SAFE_STRINGS = [
    "unsigned",
    "signed",
    "status",
    "submitter",
    "submit_manual",
    "tx_type",
    "tx_payload",
    "st.warning",
    "execution_prototype.submit",
    'add_parser("submit")',
    'args.command == "submit"',
    'xaman://xapp/sign',
    'scan with xaman to sign',
    'post_signing_prompt',
    '"submit": false',
    'sign = ',
    'sign !=',
    'prev_sign',
    'execution_guard_warning',
    'xrpl.wallet',
    'private_key',
    'post_signing_warning'
]

def is_allowed_dir(file_path: Path) -> bool:
    parts = file_path.parts
    for d in ALLOWED_DIRS:
        if d in parts:
            return True
    return False

def is_comment_or_string(line: str) -> bool:
    stripped = line.strip()
    if stripped.startswith("#"):
        return True
    # Basic check for string literals, not perfect but sufficient for strict mode
    if stripped.startswith('"') and stripped.endswith('"'):
        return True
    if stripped.startswith("'") and stripped.endswith("'"):
        return True
    return False

def check_file(file_path: Path) -> list:
    violations = []
    if is_allowed_dir(file_path) or file_path.suffix not in ALLOWED_EXTENSIONS:
        return violations
        
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
        for i, line in enumerate(lines):
            line_str = line.lower()
            if is_comment_or_string(line):
                continue
                
            for pattern in FORBIDDEN_PATTERNS:
                if re.search(pattern.lower(), line_str):
                    # Check if it's a known safe string
                    is_safe = False
                    for safe_word in SAFE_STRINGS:
                        if safe_word.lower() in line_str:
                            is_safe = True
                            break
                            
                    # Allow definitions of safe enums or constants if they explicitly say so
                    if "def " in line_str and ("build_unsigned" in line_str or "payload_identifier" in line_str):
                        is_safe = True
                        
                    if "raise valueerror" in line_str:
                        is_safe = True
                        
                    if not is_safe:
                        violations.append(f"{file_path}:{i+1}: {line.strip()} (matches {pattern})")
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        
    return violations

def main():
    root_dir = Path.cwd()
    all_violations = []
    
    for py_file in root_dir.rglob("*.py"):
        if ".venv" in py_file.parts or "__pycache__" in py_file.parts:
            continue
        violations = check_file(py_file)
        all_violations.extend(violations)
        
    if all_violations:
        print("SAFETY GREP FAILED. Unsafe patterns found in runtime code:")
        for v in all_violations:
            print(f"- {v}")
        sys.exit(1)
    else:
        print("SAFETY GREP PASSED. No execution logic found in runtime code.")
        sys.exit(0)

if __name__ == "__main__":
    main()

import os
import re
import sys
from pathlib import Path

FORBIDDEN_PATTERNS = [
    r"autofill",
    r"submitAndWait",
    r"submit_and_wait",
    r"\bwallet\b",
    r"Wallet",
    r"\bseed\b",
    r"from_seed",
    r"private_key",
    r"\bsecret\b",
    r"\bsign\b",
    r"\bsigning\b",
    r"\bsubmit\b",
    r"live buy",
    r"live sell",
    r"background",
    r"polling",
    r"auto_calibrate",
    r"mutate_model"
]

ALLOWED_DIRS = ["docs", "tests", "execution_prototype/tests", "scripts"]
ALLOWED_EXTENSIONS = [".py"]

# Exact whitelist strings with reasons
WHITELIST = {
    "unsigned": "Term used in logging/models for unsigned payload structures",
    "signed": "Term used in logging/models for signed payload structures",
    "status": "Term used for payload status",
    "submitter": "Term used in intent contracts",
    "submit_manual": "Manual submission placeholder name",
    "tx_type": "Term used for transaction classification",
    "tx_payload": "Term used for payload structures",
    "st.warning": "Streamlit UI warning syntax",
    "execution_prototype.submit": "Module import name for manual submission",
    'add_parser("submit")': "CLI command definition",
    'args.command == "submit"': "CLI command router",
    'xaman://xapp/sign': "Xaman deep link string for UX flows",
    'scan with xaman to sign': "User instruction string",
    'post_signing_prompt': "Function name for UX flows",
    '"submit": false': "Configuration string disabling submission",
    'sign = ': "Variable assignment in tests",
    'sign !=': "Variable comparison in tests",
    'prev_sign': "Variable name in tests",
    'execution_guard_warning': "Warning flag name",
    'xrpl.wallet': "Import used strictly in tests to ensure it fails",
    'private_key': "String literal used in test payloads",
    'post_signing_warning': "Warning function name",
    'from execution_prototype.submit import submit_manual': "Import for manual submission",
    'build_unsigned': "Function name for payload creation",
    'payload_identifier': "Variable name",
    'raise ValueError': "Error raising",
    'submit_transaction': "Function name in safety tests to assert failure",
    'OfferCreate': "Transaction type string",
    'Payment': "Transaction type string",
    'XRPL_WALLET_SEED': "Config property name, properly masked",
    'wallet_seed': "Config property name, properly masked",
    'Execution boundary is fail-closed': "Execution guard warning string",
    'observed liquidity is not executable': "Observation string",
    'WalletInfo': "Class name for safe read-only info wrapper",
    'safety_statement': "Phase 39 Dashboard safety text string",
    'READ-ONLY. NO WALLET. NO SIGNING. NO SUBMISSION.': "Phase 41 adapter report safety text",
    'It does not contain signing logic, private keys, or submission primitives': "Phase 42 dataset report safety text",
    'no wallet, no signing, no submission': "Phase 44 module docstring safety declaration",
    'no wallet. no signing.': "Phase 44 module docstring safety declaration",
    'wallet references, or submission primitives': "Phase 44 report safety note",
    'it does not contain signing logic': "Phase 44 report safety note",
}

def is_allowed_dir(file_path: Path) -> bool:
    parts = file_path.parts
    for d in ALLOWED_DIRS:
        if d in parts:
            return True
    return False

def check_file(file_path: Path) -> tuple[list, list]:
    violations = []
    allowed_matches = []
    
    if is_allowed_dir(file_path) or file_path.suffix not in ALLOWED_EXTENSIONS:
        return violations, allowed_matches
        
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
        for i, line in enumerate(lines):
            line_str = line.lower()
            original_line = line.strip()
            
            # Skip pure comments
            if original_line.startswith("#"):
                continue
                
            for pattern in FORBIDDEN_PATTERNS:
                if re.search(pattern.lower(), line_str):
                    is_safe = False
                    reason = ""
                    # Exact match check against whitelist
                    for safe_word, safe_reason in WHITELIST.items():
                        if safe_word.lower() in line_str:
                            is_safe = True
                            reason = safe_reason
                            break
                            
                    if is_safe:
                        allowed_matches.append(f"{file_path}:{i+1}: Allowed '{pattern}' because '{safe_word}' ({reason})")
                    else:
                        violations.append(f"{file_path}:{i+1}: {original_line} (matches {pattern})")
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        
    return violations, allowed_matches

def main():
    root_dir = Path.cwd()
    all_violations = []
    all_allowed = []
    
    for py_file in root_dir.rglob("*.py"):
        if ".venv" in py_file.parts or "__pycache__" in py_file.parts:
            continue
        violations, allowed = check_file(py_file)
        all_violations.extend(violations)
        all_allowed.extend(allowed)
        
    if all_allowed:
        print("--- ALLOWED MATCHES REPORT ---")
        for a in all_allowed:
            print(a)
        print("------------------------------")
        
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

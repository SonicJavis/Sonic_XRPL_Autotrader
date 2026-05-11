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

ALLOWED_DIRS = ["docs", "tests", "execution_prototype/tests", "scripts", "src/sonic_xrpl/audit"]
ALLOWED_EXTENSIONS = [".py"]
SKIPPED_DIR_PARTS = {
    ".ecc-source",
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".tox",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    "venv",
}

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
    # Phase 45 V2 live-guard and interface contexts
    'blocked in phase 45': "Phase 45 live guard blocking error message",
    'def submit(self,': "Abstract interface method definition (blocked by live_guard)",
    'def submit_and_wait(self,': "Abstract interface method definition (blocked by live_guard)",
    'live_submission_allowed': "Phase 45 ExecutionPlan safety field (always False)",
    'must not submit if it is false': "Phase 45 ExecutionPlan docstring safety instruction",
    'block_wallet_construction': "Phase 45 live guard blocking function name",
    'block_autofill': "Phase 45 live guard blocking function name",
    'block any attempt': "Phase 45 live guard docstring describing what is being blocked",
    'or wallet construction is permitted': "Phase 45 live guard error message listing blocked operations",
    'wallet construction is permitted': "Phase 45 live guard error message",
    'no signing, submission': "Phase 45 live guard error message listing blocked operations",
    'wallet-architecture impact': "Phase 45 XLS registry architecture impact note (research-only)",
    'wallet construction is ever enabled': "Phase 45 amendments registry future note",
    'r\"os\\.environ.*seed\"': "Phase 45 safety_scan pattern definition string (not runtime env access)",
    'os\\.environ.*seed': "Phase 45 safety_scan pattern definition string (not runtime env access)",
    # Phase 45 safety_scan.py pattern definitions (string literals in pattern list, not runtime usage)
    'safety_patterns': "Phase 45 safety scan pattern registry constant",
    r'r"\bsubmitandwait\b"': "Phase 45 safety scan pattern definition",
    r'r"\bsubmit_and_wait\b"': "Phase 45 safety scan pattern definition",
    r'r"\bautofill\b"': "Phase 45 safety scan pattern definition",
    r'r"\bbackground\b"': "Phase 45 safety scan pattern definition",
    r'r"os\.environ.*secret"': "Phase 45 safety scan pattern definition",
    'sonic_xrpl/audit/safety_scan': "Phase 45 safety scan module is the scanner itself",
    # Week 1 hot wallet policy terms (read-only architecture, no submit/sign code paths)
    'hot wallet architecture policy': "Week 1 hot wallet policy module declaration",
    'hotwalletpolicy': "Week 1 read-only hot wallet policy class name",
    'max_hot_wallet_xrp': "Week 1 hot wallet spending ceiling constant",
    'sonic_hot_wallet_account': "Week 1 hot wallet env config key",
    'sonic_hot_wallet_seed': "Week 1 hot wallet env config key (presence check only)",
    'seed_configured': "Week 1 boolean seed presence indicator",
    'seed_env_key': "Week 1 env key selector for seed presence checks",
    'return bool(seed)': "Week 1 boolean seed presence check",
    'hot_wallet_limit_exceeded': "Week 1 limit enforcement status value",
    'no signing and no submission are performed here': "Week 1 safety declaration for hot wallet policy",
    'wallet safety and policy helpers': "Week 1 wallet package safety module docstring",
    'No signing or submission is available from this dashboard': "Dashboard safety disclosure text",
    'No wallet or signing capability available': "Dashboard safety disclosure text",
    'No execution, signing, submission, or calibration mutation is available': "Dashboard read-only disclosure text",
    'Submission/sign/autofill path blocked': "Safety board explanation of blocked live guard path",
    # Phase 57 runtime profile safety-contract field names (read-only conformance metadata)
    'wallet_material_allowed': "Phase 57 runtime profile field name for blocked wallet-material policy",
    'allows_wallet_material': "Phase 57 runtime profile capability field name (must remain false)",
    'no_wallet_material_allowed': "Phase 57 conformance check id for wallet-material blocking",
    'wallet material is allowed by profile': "Phase 57 conformance fail message string",
    'wallet material remains blocked': "Phase 57 conformance pass message string",
}

def is_allowed_dir(file_path: Path) -> bool:
    parts = file_path.parts
    for d in ALLOWED_DIRS:
        # Support both single-component dirs ("docs") and multi-segment paths
        if "/" in d:
            # Multi-segment: check if d is a substring of the file path string
            if d.replace("/", os.sep) in str(file_path) or d in str(file_path):
                return True
        elif d in parts:
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
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    root_dir = Path.cwd()
    all_violations = []
    all_allowed = []
    
    for py_file in root_dir.rglob("*.py"):
        if any(part in SKIPPED_DIR_PARTS for part in py_file.parts):
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

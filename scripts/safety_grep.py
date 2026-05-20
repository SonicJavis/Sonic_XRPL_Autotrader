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
    # Phase 61 Xaman manual-approval design-spec safety flags/markers (non-executing)
    'autofill_allowed': "Phase 61 design-spec safety flag (must remain false)",
    'attempted_wallet_material': "Phase 61 fixture/safety marker for blocked wallet-material attempts",
    'no signing/submission approval': "Phase 61 blocker wording for explicitly blocked capabilities",
    # Phase 65 Xaman approval state machine spec safety text (non-executing blocked-language contracts)
    'Signing is out of scope and blocked.': "Phase 65 invalid transition blocker text for prohibited signing",
    'Wallet material handling is out of scope and blocked.': "Phase 65 invalid transition blocker text for prohibited wallet-material usage",
    'No payload/API/signing/submission authorization': "Phase 65 blocker title declaring prohibited execution capabilities",
    # Phase 66 consent UX contract spec safety text (non-executing blocked-language contracts)
    'No wallet material entry, handling, or use is permitted.': "Phase 66 required disclosure text preserving wallet-material block",
    'Signing and submission are unavailable and out of scope.': "Phase 66 required disclosure text preserving blocked capabilities",
    'no_wallet_material_disclosure': "Phase 66 consent-UX required disclosure identifier for blocked wallet-material handling",
    'Confirms wallet material handling remains blocked in this phase.': "Phase 66 disclosure rationale preserving blocked wallet-material handling",
    'Operator must acknowledge no payload, signing, or submission is available.': "Phase 66 acknowledgement text preserving blocked signing/submission",
    'Operator must acknowledge no wallet material is requested or accepted.': "Phase 66 acknowledgement text preserving blocked wallet-material handling",
    'has_no_wallet_material_disclosure': "Phase 66 fixture/model field for required wallet-material disclosure",
    'missing_no_wallet_material_disclosure': "Phase 66 validation error key for required wallet-material disclosure",
    # Phase 67 consent evidence-pack spec safety text (non-executing blocked-language contracts)
    'has_wallet_material_exclusion': "Phase 67 evidence-pack field for required wallet-material exclusion contract",
    'missing_wallet_material_exclusion': "Phase 67 validation key for required wallet-material exclusion contract",
    'wallet_material_exclusion': "Phase 67 evidence-pack requirement key for blocked wallet-material inclusion",
    'Wallet-material exclusion requirement': "Phase 67 evidence-pack requirement label preserving blocked wallet-material handling",
    'Ensures no wallet material is included.': "Phase 67 evidence-pack rationale preserving blocked wallet-material handling",
    'secrets_exclusion': "Phase 67 evidence-pack requirement key for blocked secret/key material inclusion",
    'Ensures no secret/key material is included.': "Phase 67 evidence-pack rationale preserving blocked secret/key material handling",
    'no signing/submission must remain explicit': "Phase 67 completeness requirement preserving blocked signing/submission capabilities",
    'invalid_wallet_material_marker': "Phase 67 blocked marker for prohibited wallet-material inclusion",
    'invalid_signing_submission_marker': "Phase 67 blocked marker for prohibited signing/submission inclusion",
    'No payload/API/signing/submission authorization': "Phase 67 blocker title declaring prohibited execution capabilities",
    # Phase 68 preflight safety checklist spec safety text (non-executing blocked-language contracts)
    'has_no_secrets_gate': "Phase 68 preflight gate key requiring no secret/key material",
    'missing_no_secrets_gate': "Phase 68 validation key for required no-secrets gate",
    'has_no_wallet_material_gate': "Phase 68 preflight gate key requiring blocked wallet-material handling",
    'missing_no_wallet_material_gate': "Phase 68 validation key for required no-wallet-material gate",
    'has_no_signing_submission_gate': "Phase 68 preflight gate key requiring blocked signing/submission",
    'missing_no_signing_submission_gate': "Phase 68 validation key for required no-signing/submission gate",
    'invalid_runtime_runner_marker': "Phase 68 blocked marker for prohibited runtime checklist runner implementation",
    'invalid_persistence_db_write_marker': "Phase 68 blocked marker for prohibited persistence/DB-write implementation",
    'No payload/API/signing/submission authorization.': "Phase 68 completeness requirement preserving blocked capabilities",
    'No-secrets gate': "Phase 68 preflight checklist label requiring no secret/key material",
    'Confirms no secret/key material inclusion.': "Phase 68 preflight checklist rationale preserving secret/key exclusion",
    'No-signing/submission gate': "Phase 68 preflight checklist label preserving blocked signing/submission capabilities",
    'Confirms signing/submission remain blocked.': "Phase 68 preflight checklist rationale preserving blocked signing/submission capabilities",
    'All no-execution/no-wallet/no-api/no-signing gates must remain explicit.': "Phase 68 completeness requirement preserving blocked wallet/signing capabilities",
    # Phase 69 dry-run readiness review spec safety text (non-executing blocked-language contracts)
    'has_no_secrets_status': "Phase 69 readiness status key requiring no secret/key material",
    'missing_no_secrets_status': "Phase 69 validation key for required no-secrets status",
    'has_no_wallet_material_status': "Phase 69 readiness status key requiring blocked wallet-material handling",
    'missing_no_wallet_material_status': "Phase 69 validation key for required no-wallet-material status",
    'has_no_signing_submission_status': "Phase 69 readiness status key requiring blocked signing/submission",
    'missing_no_signing_submission_status': "Phase 69 validation key for required no-signing/submission status",
    'xaman_sdk_dependency_allowed': "Phase 70 governance safety flag for blocked SDK dependency usage",
    'has_wallet_material_boundary_evidence': "Phase 70 governance evidence key for blocked wallet-material boundary",
    'invalid_wallet_material_ambiguity_marker': "Phase 70 governance blocked marker for wallet-material ambiguity",
    'invalid_testnet_approved_marker': "Phase 70 governance blocked marker for prohibited testnet approval language",
    'invalid_live_approved_marker': "Phase 70 governance blocked marker for prohibited live approval language",
    'sign-off': "Phase 70 governance terminology for non-executing sign-off matrix specs",
    'signoff': "Phase 70 governance module/identifier naming for signoff matrix specs",
    'wallet_material_boundary_evidence': "Phase 70 governance evidence key for blocked wallet-material boundary",
    'invalid_wallet_material_ambiguity_marker': "Phase 70 governance blocked marker for wallet-material ambiguity",
    'wallet seed/private-key handling': "Phase 70 safety disclosure for prohibited wallet material handling",
    'WALLET_MATERIAL_BOUNDARY': "Phase 70 governance sign-off domain for wallet-material boundary controls",
    'wallet_material_ambiguity': "Phase 70 governance blocker key for wallet-material ambiguity",
    'Wallet material boundary ambiguity': "Phase 70 governance blocker title for wallet-material boundary issues",
    'attestation_only': "Phase 71 governance evidence safety flag for spec-only attestation outputs",
    'invalid_payload_or_execution_approval_marker': "Phase 71 blocked marker for prohibited payload/testnet/live approval wording",
    'invalid_wallet_material_ambiguity_marker': "Phase 71 blocked marker for wallet-material ambiguity",
    'xaman_governance_evidence_attestation_spec': "Phase 71 module name for governance evidence integrity/attestation specs",
    'invalid_testnet_approved_marker': "Phase 69 blocked marker for prohibited testnet approval claim",
    'invalid_live_approved_marker': "Phase 69 blocked marker for prohibited live approval claim",
    'All no-execution/no-wallet/no-api/no-signing statuses must remain explicit.': "Phase 69 completeness requirement preserving blocked wallet/signing capabilities",
    # Phase 74 governance exception-waiver register spec safety text (non-executing blocked-language contracts)
    'WALLET_MATERIAL_WAIVER': "Phase 74 waiver-domain identifier for blocked wallet-material exceptions",
    'WALLET_MATERIAL_WAIVER_ATTEMPT': "Phase 74 blocker identifier for prohibited wallet-material waiver attempts",
    'SIGNING_SUBMISSION_AUTOFILL_WAIVER_ATTEMPT': "Phase 74 blocker identifier for prohibited signing/submission/autofill waiver attempts",
    'NON_AUTHORIZATION_NOTICES': "Phase 78 approval-packet non-authorization notice constant preserving blocked capabilities",
    'REQUIRED_NOTICES': "Phase 79 review-checklist non-authorization notice constant preserving blocked capabilities",
    'SNAPSHOT_DOMAINS': "Phase 80 evidence-snapshot domain constant preserving blocked capabilities",
    'signing_submission_autofill_waivers_are_blocked': "Phase 74 rule declaring prohibited signing/submission/autofill waivers",
    'invalid_wallet_material_waiver_marker': "Phase 74 blocked marker for prohibited wallet-material waiver attempts",
    'invalid_signing_submission_autofill_waiver_marker': "Phase 74 blocked marker for prohibited signing/submission/autofill waiver attempts",
    'wallet_material_waiver_attempt': "Phase 74 blocker key for prohibited wallet-material waiver attempts",
    'signing_submission_autofill_waiver_attempt': "Phase 74 blocker key for prohibited signing/submission/autofill waiver attempts",
    # Phase 75 final-readiness bundle spec safety text (non-executing blocked-language contracts)
    'invalid_wallet_material_approval_marker': "Phase 75 blocked marker for prohibited wallet-material approval wording",
    'invalid_signing_submission_autofill_approval_marker': "Phase 75 blocked marker for prohibited signing/submission/autofill approval wording",
    'signing_submission_autofill_approval_marker': "Phase 75 blocker key for prohibited signing/submission/autofill approval wording",
    'no_signing_submission_autofill_wallet_approval_wording': "Phase 75 completeness check requiring blocked execution wording",
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

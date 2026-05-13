from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]

PHASE58B_DOCS = {
    "docs/LIVE_READINESS_POLICY.md": [
        "live trading remains blocked",
        "phase 58b",
        "does not authorize live trading",
        "future dedicated live-enablement phase",
        "explicit human approval",
        "transaction signing",
        "transaction submission",
        "transaction autofill",
        "wallet seed/private-key",
        "xaman payload creation",
        "firstledger live ingestion",
        "runtime mutation",
        "full_auto",
        "autonomous execution",
        "blocker register",
        "threat model",
        "dependency audit",
        "secrets-management",
        "rollback",
        "kill-switch",
        "audit logging",
        "manual approval gates",
    ],
    "docs/CANONICAL_RUNTIME_OWNERSHIP_POLICY.md": [
        "`src/sonic_xrpl/` is the canonical future runtime target",
        "`app/` is the current runnable legacy api/paper runtime surface",
        "`execution_prototype/` is historical/reference-only",
        "no future feature may assign new runtime authority to `execution_prototype/`",
        "`app/` must not receive new trading/execution authority",
        "phase 58b",
        "not implemented here",
    ],
    "docs/XAMAN_FUTURE_INTEGRATION_POLICY.md": [
        "xaman is future/manual-approval-only",
        "no v2 xaman payload creation implementation exists today",
        "historical `execution_prototype` xaman helpers are non-canonical reference material",
        "must begin with a design spec",
        "payload lifecycle",
        "user-consent",
        "audit trail",
        "replay-protection",
        "secrets/key-material",
        "failure modes",
        "no signing implementation",
        "no transaction submission implementation",
        "no transaction autofill implementation",
        "no wallet seed/private-key handling implementation",
    ],
    "docs/FIRSTLEDGER_FUTURE_INGESTION_POLICY.md": [
        "fixture/source-backed signal evidence only",
        "no production live firstledger adapter is authorized",
        "no firstledger signal can directly trigger live execution",
        "source provenance validation",
        "source trust scoring",
        "stale/missing evidence handling",
        "replay-protection",
        "rate-limit and backoff policy",
        "fail-closed classification",
        "operator-review",
        "synthetic evidence cannot become `buy_candidate`",
        "live coupling to execution remains blocked",
    ],
    "docs/POLICY_INDEX.md": [
        "safety model",
        "canonical path decision",
        "live readiness policy",
        "canonical runtime ownership policy",
        "xaman future integration policy",
        "firstledger future ingestion policy",
        "phase 58a safety-review triage policy",
        "roadmap",
        "phase ledger",
    ],
}

PROHIBITED_AUTHORIZATION_PHRASES = (
    "live execution is authorized",
    "live trading is authorized",
    "phase 58b authorizes live",
    "phase 58b enables live",
)


def _read(path: str) -> str:
    return (REPO_ROOT / path).read_text(encoding="utf-8").lower()


def test_phase58b_policy_docs_exist() -> None:
    for rel_path in PHASE58B_DOCS:
        assert (REPO_ROOT / rel_path).exists(), f"missing policy doc: {rel_path}"


def test_phase58b_policy_docs_contain_required_blocking_language() -> None:
    for rel_path, required_phrases in PHASE58B_DOCS.items():
        text = _read(rel_path)
        for phrase in required_phrases:
            assert phrase.lower() in text, f"missing phrase in {rel_path}: {phrase}"


def test_phase58b_policy_docs_do_not_authorize_live_execution() -> None:
    for rel_path in PHASE58B_DOCS:
        text = _read(rel_path)
        for forbidden in PROHIBITED_AUTHORIZATION_PHRASES:
            assert forbidden not in text, f"forbidden authorization language in {rel_path}: {forbidden}"

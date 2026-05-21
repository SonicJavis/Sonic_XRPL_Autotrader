import ast
from pathlib import Path

from sonic_xrpl.xaman_governance_closure_response_evidence_pack_review_digest_spec import (
    build_xaman_governance_closure_response_evidence_pack_review_digest_spec,
    load_xaman_governance_closure_response_evidence_pack_review_digest_fixture,
)

MODULE = Path("src/sonic_xrpl/xaman_governance_closure_response_evidence_pack_review_digest_spec")
FIXTURE = Path("tests/fixtures/xaman_governance_closure_response_evidence_pack_review_digest_spec/complete_spec_review_ready_evidence_pack_review_digest.json")

FORBIDDEN_IMPORT_FRAGMENTS = (
    "xaman",
    "xrpl.wallet",
    "xrpl.transaction",
    "app.",
    "execution_prototype",
    "requests",
    "httpx",
    "websocket",
    "sqlite3",
)


def test_phase89_module_has_no_runtime_or_wallet_imports():
    for path in MODULE.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                names = []
                if isinstance(node, ast.Import):
                    names = [alias.name for alias in node.names]
                else:
                    names = [node.module or ""]
                for name in names:
                    lowered = name.lower()
                    if lowered.startswith("sonic_xrpl.xaman_governance_closure_response_evidence_pack_review_digest_spec"):
                        continue
                    assert not any(fragment in lowered for fragment in FORBIDDEN_IMPORT_FRAGMENTS), (path, name)


def test_phase89_safety_flags_remain_fail_closed():
    report = build_xaman_governance_closure_response_evidence_pack_review_digest_spec(
        load_xaman_governance_closure_response_evidence_pack_review_digest_fixture(FIXTURE)
    )
    flags = report.spec.safety_flags
    assert flags.spec_only is True
    assert flags.closure_response_evidence_pack_review_digest_spec_only is True
    assert flags.runtime_evidence_pack_review_digest_service_allowed is False
    assert flags.download_service_allowed is False
    assert flags.api_route_allowed is False
    assert flags.dashboard_ui_allowed is False
    assert flags.safety_bypass_allowed is False
    assert flags.testnet_execution_allowed is False
    assert flags.xaman_payload_creation_allowed is False
    assert flags.xaman_api_calls_allowed is False
    assert flags.xaman_sdk_dependency_allowed is False
    assert flags.signing_allowed is False
    assert flags.submission_allowed is False
    assert flags.autofill_allowed is False
    assert flags.wallet_material_allowed is False
    assert flags.live_execution_allowed is False
    assert flags.runtime_mutation_allowed is False

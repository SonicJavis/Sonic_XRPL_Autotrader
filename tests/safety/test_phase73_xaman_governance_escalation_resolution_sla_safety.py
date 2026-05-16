from pathlib import Path

from sonic_xrpl.xaman_governance_escalation_resolution_sla_spec import (
    build_xaman_governance_escalation_resolution_sla_spec,
    load_xaman_governance_escalation_resolution_sla_fixture,
)


def _run(path: str):
    return build_xaman_governance_escalation_resolution_sla_spec(
        load_xaman_governance_escalation_resolution_sla_fixture(path)
    )


def test_phase73_module_has_no_network_wallet_or_execution_calls():
    combined = "\n".join(
        path.read_text(encoding="utf-8")
        for path in Path(
            "src/sonic_xrpl/xaman_governance_escalation_resolution_sla_spec"
        ).glob("*.py")
    )
    forbidden = [
        "requests.get(",
        "requests.post(",
        "http://",
        "https://",
        "submitAndWait",
        "autofill(",
        "Wallet(",
        "fromSeed",
        "sqlite3.connect(",
        "session.commit(",
    ]
    for token in forbidden:
        assert token not in combined


def test_phase73_flags_block_runtime_scheduler_notifications_payload_and_execution():
    report = _run(
        "tests/fixtures/xaman_governance_escalation_resolution_sla_spec/complete_spec_review_ready_sla_bundle.json"
    )
    flags = report.spec.safety_flags
    assert flags.spec_only is True
    assert flags.sla_spec_only is True
    assert flags.runtime_sla_engine_allowed is False
    assert flags.scheduler_allowed is False
    assert flags.notification_allowed is False
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

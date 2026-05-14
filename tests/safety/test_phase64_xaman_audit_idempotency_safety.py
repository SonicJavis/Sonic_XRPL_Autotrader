from pathlib import Path

from sonic_xrpl.xaman_audit_idempotency_spec import (
    build_xaman_audit_idempotency_spec,
    load_xaman_audit_idempotency_fixture,
)


def _run(path: str):
    return build_xaman_audit_idempotency_spec(load_xaman_audit_idempotency_fixture(path))


def test_phase64_module_has_no_runtime_or_db_or_network_usage():
    combined = "\n".join(
        path.read_text(encoding="utf-8")
        for path in Path("src/sonic_xrpl/xaman_audit_idempotency_spec").glob("*.py")
    )
    forbidden = [
        "FastAPI(",
        "@app.post",
        "requests.get(",
        "requests.post(",
        "sqlite3.connect(",
        "session.add(",
        "session.commit(",
        "http://",
        "https://",
        "submitAndWait",
        "fromSeed",
        "Wallet(",
    ]
    for token in forbidden:
        assert token not in combined


def test_phase64_flags_block_runtime_persistence_and_execution():
    report = _run("tests/fixtures/xaman_audit_idempotency_spec/healthy_audit_idempotency_spec.json")
    flags = report.spec.safety_flags
    assert flags.persistence_implementation_allowed is False
    assert flags.database_writes_allowed is False
    assert flags.callback_handler_allowed is False
    assert flags.webhook_runtime_allowed is False
    assert flags.payload_creation_allowed is False
    assert flags.xaman_api_calls_allowed is False
    assert flags.signing_allowed is False
    assert flags.submission_allowed is False
    assert flags.wallet_material_allowed is False
    assert flags.testnet_execution_allowed is False
    assert flags.live_execution_allowed is False


def test_phase64_attempted_runtime_markers_fail_closed():
    report = _run(
        "tests/fixtures/xaman_audit_idempotency_spec/attempted_testnet_live_execution_marker.json"
    )
    assert "blocked_attempted_testnet_execution" in report.validation_errors
    assert "blocked_attempted_live_execution" in report.validation_errors

from pathlib import Path

from sonic_xrpl.xaman_approval_state_machine_spec import (
    build_xaman_approval_state_machine_spec,
    load_xaman_approval_state_machine_fixture,
)


def _run(path: str):
    return build_xaman_approval_state_machine_spec(load_xaman_approval_state_machine_fixture(path))


def test_phase65_module_has_no_runtime_state_machine_or_network_or_db_usage():
    combined = "\n".join(
        path.read_text(encoding="utf-8") for path in Path("src/sonic_xrpl/xaman_approval_state_machine_spec").glob("*.py")
    )
    forbidden = [
        "FastAPI(",
        "@app.post",
        "requests.get(",
        "requests.post(",
        "sqlite3.connect(",
        "session.add(",
        "session.commit(",
        "while True",
        "http://",
        "https://",
        "submitAndWait",
        "fromSeed",
        "Wallet(",
    ]
    for token in forbidden:
        assert token not in combined


def test_phase65_flags_block_runtime_persistence_execution():
    report = _run("tests/fixtures/xaman_approval_state_machine_spec/healthy_approval_state_machine_spec.json")
    f = report.spec.safety_flags
    assert f.runtime_state_machine_allowed is False
    assert f.persistence_implementation_allowed is False
    assert f.database_writes_allowed is False
    assert f.callback_handler_allowed is False
    assert f.webhook_runtime_allowed is False
    assert f.payload_creation_allowed is False
    assert f.xaman_api_calls_allowed is False
    assert f.signing_allowed is False
    assert f.submission_allowed is False
    assert f.wallet_material_allowed is False
    assert f.testnet_execution_allowed is False
    assert f.live_execution_allowed is False


def test_phase65_attempted_runtime_markers_fail_closed():
    report = _run("tests/fixtures/xaman_approval_state_machine_spec/attempted_runtime_state_machine_marker.json")
    assert "blocked_attempted_runtime_state_machine_marker" in report.validation_errors

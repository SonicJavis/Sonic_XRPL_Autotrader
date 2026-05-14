from pathlib import Path

from sonic_xrpl.xaman_operator_consent_ux_spec import (
    build_xaman_operator_consent_ux_spec,
    load_xaman_operator_consent_ux_fixture,
)


def _run(path: str):
    return build_xaman_operator_consent_ux_spec(load_xaman_operator_consent_ux_fixture(path))


def test_phase66_module_has_no_ui_api_network_or_db_usage():
    combined = "\n".join(
        path.read_text(encoding="utf-8")
        for path in Path("src/sonic_xrpl/xaman_operator_consent_ux_spec").glob("*.py")
    )
    forbidden = [
        "FastAPI(",
        "@app.get",
        "@app.post",
        "streamlit",
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


def test_phase66_flags_block_ui_runtime_persistence_execution():
    report = _run("tests/fixtures/xaman_operator_consent_ux_spec/healthy_consent_ux_contract.json")
    f = report.spec.safety_flags
    assert f.ui_implementation_allowed is False
    assert f.api_route_allowed is False
    assert f.runtime_consent_service_allowed is False
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


def test_phase66_attempted_ui_marker_fails_closed():
    report = _run("tests/fixtures/xaman_operator_consent_ux_spec/attempted_ui_implementation_marker.json")
    assert "blocked_attempted_ui_implementation_marker" in report.validation_errors

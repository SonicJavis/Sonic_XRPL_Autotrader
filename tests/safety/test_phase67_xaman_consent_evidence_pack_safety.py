from pathlib import Path

from sonic_xrpl.xaman_consent_evidence_pack_spec import (
    build_xaman_consent_evidence_pack_spec,
    load_xaman_consent_evidence_pack_fixture,
)


def _run(path: str):
    return build_xaman_consent_evidence_pack_spec(load_xaman_consent_evidence_pack_fixture(path))


def test_phase67_module_has_no_ui_api_network_db_or_export_runtime_usage():
    combined = "\n".join(
        path.read_text(encoding="utf-8")
        for path in Path("src/sonic_xrpl/xaman_consent_evidence_pack_spec").glob("*.py")
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
        "open(",
        "write(",
        "http://",
        "https://",
        "submitAndWait",
        "fromSeed",
        "Wallet(",
    ]
    for token in forbidden:
        assert token not in combined


def test_phase67_flags_block_ui_api_runtime_export_persistence_execution():
    report = _run("tests/fixtures/xaman_consent_evidence_pack_spec/healthy_evidence_pack.json")
    f = report.spec.safety_flags
    assert f.export_implementation_allowed is False
    assert f.file_write_allowed is False
    assert f.ui_implementation_allowed is False
    assert f.api_route_allowed is False
    assert f.runtime_service_allowed is False
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


def test_phase67_invalid_export_marker_fails_closed():
    report = _run("tests/fixtures/xaman_consent_evidence_pack_spec/invalid_export_file_write_marker.json")
    assert "blocked_invalid_export_file_write_marker" in report.validation_errors

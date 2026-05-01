from __future__ import annotations

import json
from pathlib import Path

import pytest

from execution_prototype.audit import append_audit_record, read_audit_records
from execution_prototype.cli import main
from execution_prototype.intent_contract import ensure_safety_gates, parse_intent, validate_safety_gates
from execution_prototype.submit import CONFIRMATION_PHRASE, require_manual_confirmation, submit_manual
from execution_prototype.wizard import (
    RiskAcknowledgement,
    build_wizard_package,
    classify_execution_type,
    execution_reality_messages,
    liquidity_explanation,
    partial_fill_range,
    require_risk_acknowledgement,
)
from execution_prototype.xaman_payload import build_deep_link, build_xaman_payload
from execution_prototype.xrpl_tx_builder import build_unsigned_transaction, transaction_fingerprint


def test_no_import_leakage_from_main_system() -> None:
    root = Path("execution_prototype")
    for path in root.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        if "tests" in path.parts:
            continue
        source = path.read_text(encoding="utf-8")
        assert "from app." not in source
        assert "import app." not in source


def test_offer_create_generation_is_deterministic() -> None:
    intent = parse_intent(_intent(preferred_source="orderbook"))

    first = build_unsigned_transaction(intent)
    second = build_unsigned_transaction(intent)

    assert first == second
    assert first["TransactionType"] == "OfferCreate"
    assert first["Flags"] == 0
    assert first["TakerGets"]["currency"] == "USD"
    assert first["TakerPays"] == "12500000"
    assert transaction_fingerprint(first) == transaction_fingerprint(second)


def test_payment_generation_for_path_or_amm_context() -> None:
    intent = parse_intent(_intent(preferred_source="amm"))

    tx = build_unsigned_transaction(intent)

    assert tx["TransactionType"] == "Payment"
    assert tx["Amount"]["currency"] == "USD"
    assert tx["SendMax"] == "12500000"
    assert tx["Flags"] == 0


def test_safety_gates_block_avoid_and_stale_intents() -> None:
    avoid = parse_intent(_intent(feasibility_decision="avoid"))
    stale = parse_intent(_intent(decay_decision="stale"))

    assert "execution_feasibility_avoid" in validate_safety_gates(avoid)
    assert "liquidity_decay_stale_or_invalid" in validate_safety_gates(stale)
    with pytest.raises(ValueError):
        ensure_safety_gates(avoid)
    with pytest.raises(ValueError):
        build_unsigned_transaction(stale)


def test_xaman_payload_is_unsigned_and_deterministic() -> None:
    intent = parse_intent(_intent(preferred_source="orderbook"))
    tx = build_unsigned_transaction(intent)

    first = build_xaman_payload(tx)
    second = build_xaman_payload(tx)
    link = build_deep_link(first)

    assert first == second
    assert first["options"]["submit"] is False
    assert first["txjson"] == tx
    assert link.startswith("xaman://xapp/sign/")


def test_manual_confirmation_required() -> None:
    with pytest.raises(ValueError):
        require_manual_confirmation("YES")

    require_manual_confirmation(CONFIRMATION_PHRASE)


def test_submit_manual_requires_confirmation_and_records_audit(tmp_path) -> None:
    intent = parse_intent(_intent(preferred_source="orderbook"))
    tx = build_unsigned_transaction(intent)
    audit_path = tmp_path / "audit.jsonl"

    with pytest.raises(ValueError):
        submit_manual(intent=intent, unsigned_tx=tx, confirmation="WRONG", audit_path=audit_path)

    result = submit_manual(
        intent=intent,
        unsigned_tx=tx,
        confirmation=CONFIRMATION_PHRASE,
        trade_type_understood=True,
        partial_fill_accepted=True,
        price_impact_understood=True,
        audit_path=audit_path,
    )

    assert result["submitted"] is False
    records = read_audit_records(audit_path)
    assert len(records) == 1
    assert records[0]["intent_id"] == "intent_test"
    assert records[0]["user_confirmed"] is True
    assert records[0]["user_acknowledged_risk"] is True
    assert records[0]["execution_type"] == "OfferCreate"
    assert records[0]["liquidity_source"] == "orderbook"
    assert records[0]["decay_status"] == "fresh"
    assert records[0]["expected_fill_range"]["expected_fill_ratio"] == 0.8


def test_submit_manual_uses_injected_submitter_only_after_confirmation(tmp_path) -> None:
    intent = parse_intent(_intent(preferred_source="orderbook"))
    tx = build_unsigned_transaction(intent)
    calls: list[str] = []

    def fake_submitter(blob: str) -> dict[str, object]:
        calls.append(blob)
        return {"tx_hash": "ABC123"}

    result = submit_manual(
        intent=intent,
        unsigned_tx=tx,
        confirmation=CONFIRMATION_PHRASE,
        trade_type_understood=True,
        partial_fill_accepted=True,
        price_impact_understood=True,
        signed_blob="signed-by-user-outside-this-tool",
        submitter=fake_submitter,
        audit_path=tmp_path / "audit.jsonl",
    )

    assert calls == ["signed-by-user-outside-this-tool"]
    assert result["submitted"] is True
    assert result["tx_hash"] == "ABC123"


def test_audit_logging_is_append_only(tmp_path) -> None:
    audit_path = tmp_path / "audit.jsonl"
    tx = {"TransactionType": "OfferCreate", "Flags": 0}

    append_audit_record(
        intent_id="a",
        tx_type="OfferCreate",
        tx_payload=tx,
        user_confirmed=True,
        submitted=False,
        path=audit_path,
    )
    append_audit_record(
        intent_id="b",
        tx_type="OfferCreate",
        tx_payload=tx,
        user_confirmed=True,
        submitted=False,
        path=audit_path,
    )

    records = read_audit_records(audit_path)
    assert [row["intent_id"] for row in records] == ["a", "b"]


def test_cli_validate_build_and_xaman_outputs(tmp_path, capsys) -> None:
    intent_file = tmp_path / "intent.json"
    tx_file = tmp_path / "tx.json"
    payload_file = tmp_path / "payload.json"
    intent_file.write_text(json.dumps(_intent()), encoding="utf-8")

    assert main(["validate-intent", str(intent_file)]) == 0
    assert main(["build-tx", str(intent_file), "--out", str(tx_file)]) == 0
    assert main(["generate-xaman", str(intent_file), "--out", str(payload_file)]) == 0

    assert json.loads(tx_file.read_text(encoding="utf-8"))["txjson"]["TransactionType"] == "OfferCreate"
    assert "deep_link" in json.loads(payload_file.read_text(encoding="utf-8"))
    captured = capsys.readouterr()
    assert '"valid": true' in captured.out


def test_cli_wizard_preview_outputs_risk_surface(tmp_path) -> None:
    intent_file = tmp_path / "intent.json"
    wizard_file = tmp_path / "wizard.json"
    intent_file.write_text(json.dumps(_intent(preferred_source="amm")), encoding="utf-8")

    assert main(["wizard-preview", str(intent_file), "--out", str(wizard_file)]) == 0

    body = json.loads(wizard_file.read_text(encoding="utf-8"))
    assert body["execution_type"]["tx_type"] == "Payment"
    assert body["liquidity"]["liquidity_source"] == "amm"
    assert body["confirmation_required"]["partial_fill_accepted"] is True
    assert body["is_executable"] is False


def test_cli_submit_records_unsubmitted_manual_confirmation(tmp_path) -> None:
    intent_file = tmp_path / "intent.json"
    audit_path = tmp_path / "audit.jsonl"
    intent_file.write_text(json.dumps(_intent()), encoding="utf-8")

    code = main(
        [
            "submit",
            str(intent_file),
            "--confirmation",
            CONFIRMATION_PHRASE,
            "--understand-type",
            "--accept-partial-fill",
            "--understand-price-impact",
            "--audit-log",
            str(audit_path),
        ]
    )

    assert code == 0
    assert read_audit_records(audit_path)[0]["submitted"] is False
    assert read_audit_records(audit_path)[0]["user_acknowledged_risk"] is True


def test_wizard_classifies_orderbook_and_payment_types() -> None:
    orderbook = parse_intent(_intent(preferred_source="orderbook"))
    amm = parse_intent(_intent(preferred_source="amm"))

    assert classify_execution_type(orderbook)["tx_type"] == "OfferCreate"
    assert classify_execution_type(orderbook)["label"] == "Orderbook trade (limit-style)"
    assert classify_execution_type(amm)["tx_type"] == "Payment"
    assert classify_execution_type(amm)["label"] == "Path-based trade (AMM / routing)"


def test_wizard_displays_partial_fill_and_xrpl_reality_messages() -> None:
    orderbook = parse_intent(_intent(preferred_source="orderbook"))
    amm = parse_intent(_intent(preferred_source="amm"))

    fill = partial_fill_range(orderbook)
    assert 0.0 <= fill["min_fill_estimate"] <= fill["expected_fill_ratio"] <= fill["max_fill_estimate"] <= 1.0
    assert "May partially fill." in execution_reality_messages(orderbook)
    assert "Route may fail at submission time." in execution_reality_messages(amm)
    assert "funded offers" in liquidity_explanation(orderbook)["explanation"]
    assert "price impact increases with size" in liquidity_explanation(amm)["explanation"]


def test_wizard_package_is_deterministic_and_contains_manual_risk_prompts() -> None:
    intent = parse_intent(_intent(preferred_source="hybrid"))

    first = build_wizard_package(intent)
    second = build_wizard_package(intent)

    assert first == second
    assert first["execution_type"]["tx_type"] == "Payment"
    assert first["partial_fill_note"] == "XRPL offers can be partially filled depending on liquidity."
    assert first["confirmation_required"]["phrase"] == CONFIRMATION_PHRASE
    assert first["xaman_qr"]["format"] == "qr_source_text"
    assert first["xaman_instructions"] == ["Scan with Xaman to sign.", "Review transaction before approving."]
    assert first["post_signing_warning"] == "Transaction success is NOT guaranteed; ledger validation determines final outcome."
    assert first["is_executable"] is False


def test_stale_intent_blocks_wizard_package() -> None:
    stale = parse_intent(_intent(decay_decision="stale"))

    with pytest.raises(ValueError):
        build_wizard_package(stale)


def test_upgraded_risk_acknowledgement_requires_all_flags() -> None:
    with pytest.raises(ValueError):
        require_risk_acknowledgement(
            RiskAcknowledgement(
                confirmation=CONFIRMATION_PHRASE,
                trade_type_understood=True,
                partial_fill_accepted=False,
                price_impact_understood=True,
            )
        )

    require_risk_acknowledgement(
        RiskAcknowledgement(
            confirmation=CONFIRMATION_PHRASE,
            trade_type_understood=True,
            partial_fill_accepted=True,
            price_impact_understood=True,
        )
    )


def _intent(
    *,
    preferred_source: str = "orderbook",
    feasibility_decision: str = "feasible",
    liquidity_decision: str = "usable",
    decay_decision: str = "fresh",
) -> dict[str, object]:
    return {
        "intent_id": "intent_test",
        "action": "buy",
        "token": "USD",
        "issuer": "rIssuer",
        "size": 12.5,
        "execution_feasibility": {
            "decision": feasibility_decision,
            "expected_fill_ratio": 0.8,
            "expected_slippage": 0.02,
            "is_executable": False,
        },
        "liquidity_source_model": {
            "decision": liquidity_decision,
            "liquidity_source": preferred_source,
            "preferred_source": preferred_source,
            "is_executable": False,
        },
        "liquidity_decay": {
            "decision": decay_decision,
            "decay_factor": 0.95,
            "is_executable": False,
        },
    }

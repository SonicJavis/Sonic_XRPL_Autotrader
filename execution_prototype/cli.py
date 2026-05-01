from __future__ import annotations

import argparse
import json
from pathlib import Path

from execution_prototype.audit import append_audit_record
from execution_prototype.intent_contract import ensure_safety_gates, load_intent_file, risk_summary, validate_safety_gates
from execution_prototype.payload_session import (
    create_session_from_intent_file,
    load_session,
    mark_failed,
    mark_signed,
    mark_validated,
    record_result,
    record_submission,
)
from execution_prototype.submit import CONFIRMATION_PHRASE, require_manual_confirmation
from execution_prototype.wizard import audit_context, build_wizard_package
from execution_prototype.xaman_payload import build_deep_link, build_xaman_payload
from execution_prototype.xrpl_tx_builder import build_unsigned_transaction, transaction_fingerprint


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Air-gapped XRPL manual execution prototype")
    sub = parser.add_subparsers(dest="command", required=True)

    load_parser = sub.add_parser("load-intent")
    load_parser.add_argument("file")

    validate_parser = sub.add_parser("validate-intent")
    validate_parser.add_argument("file")

    risk_parser = sub.add_parser("show-risk")
    risk_parser.add_argument("file")

    build_parser = sub.add_parser("build-tx")
    build_parser.add_argument("file")
    build_parser.add_argument("--account", default="rMANUAL_ACCOUNT_PLACEHOLDER")
    build_parser.add_argument("--out")

    xaman_parser = sub.add_parser("generate-xaman")
    xaman_parser.add_argument("file")
    xaman_parser.add_argument("--account", default="rMANUAL_ACCOUNT_PLACEHOLDER")
    xaman_parser.add_argument("--out")

    wizard_parser = sub.add_parser("wizard-preview")
    wizard_parser.add_argument("file")
    wizard_parser.add_argument("--account", default="rMANUAL_ACCOUNT_PLACEHOLDER")
    wizard_parser.add_argument("--out")

    submit_parser = sub.add_parser("submit")
    submit_parser.add_argument("file")
    submit_parser.add_argument("--account", default="rMANUAL_ACCOUNT_PLACEHOLDER")
    submit_parser.add_argument("--confirmation", required=True)
    submit_parser.add_argument("--understand-type", action="store_true")
    submit_parser.add_argument("--accept-partial-fill", action="store_true")
    submit_parser.add_argument("--understand-price-impact", action="store_true")
    submit_parser.add_argument("--audit-log", default=str(Path(__file__).with_name("audit_log.jsonl")))

    create_session_parser = sub.add_parser("create-session")
    create_session_parser.add_argument("file")
    create_session_parser.add_argument("--account", default="rMANUAL_ACCOUNT_PLACEHOLDER")
    create_session_parser.add_argument("--confirmation", required=True)
    create_session_parser.add_argument("--session-log", default=str(Path(__file__).with_name("payload_sessions.jsonl")))
    create_session_parser.add_argument("--audit-log", default=str(Path(__file__).with_name("lifecycle_audit_log.jsonl")))

    show_session_parser = sub.add_parser("show-session")
    show_session_parser.add_argument("session_id")
    show_session_parser.add_argument("--confirmation", required=True)
    show_session_parser.add_argument("--session-log", default=str(Path(__file__).with_name("payload_sessions.jsonl")))

    mark_signed_parser = sub.add_parser("mark-signed")
    mark_signed_parser.add_argument("session_id")
    mark_signed_parser.add_argument("--confirmation", required=True)
    mark_signed_parser.add_argument("--session-log", default=str(Path(__file__).with_name("payload_sessions.jsonl")))
    mark_signed_parser.add_argument("--audit-log", default=str(Path(__file__).with_name("lifecycle_audit_log.jsonl")))

    record_submission_parser = sub.add_parser("record-submission")
    record_submission_parser.add_argument("session_id")
    record_submission_parser.add_argument("tx_hash")
    record_submission_parser.add_argument("--confirmation", required=True)
    record_submission_parser.add_argument("--session-log", default=str(Path(__file__).with_name("payload_sessions.jsonl")))
    record_submission_parser.add_argument("--audit-log", default=str(Path(__file__).with_name("lifecycle_audit_log.jsonl")))

    record_result_parser = sub.add_parser("record-result")
    record_result_parser.add_argument("session_id")
    record_result_parser.add_argument("engine_result")
    record_result_parser.add_argument("--engine-result-message")
    record_result_parser.add_argument("--confirmation", required=True)
    record_result_parser.add_argument("--session-log", default=str(Path(__file__).with_name("payload_sessions.jsonl")))
    record_result_parser.add_argument("--audit-log", default=str(Path(__file__).with_name("lifecycle_audit_log.jsonl")))

    mark_validated_parser = sub.add_parser("mark-validated")
    mark_validated_parser.add_argument("session_id")
    mark_validated_parser.add_argument("--ledger-index", type=int, required=True)
    mark_validated_parser.add_argument("--confirmation", required=True)
    mark_validated_parser.add_argument("--session-log", default=str(Path(__file__).with_name("payload_sessions.jsonl")))
    mark_validated_parser.add_argument("--audit-log", default=str(Path(__file__).with_name("lifecycle_audit_log.jsonl")))

    mark_failed_parser = sub.add_parser("mark-failed")
    mark_failed_parser.add_argument("session_id")
    mark_failed_parser.add_argument("--engine-result", required=True)
    mark_failed_parser.add_argument("--confirmation", required=True)
    mark_failed_parser.add_argument("--session-log", default=str(Path(__file__).with_name("payload_sessions.jsonl")))
    mark_failed_parser.add_argument("--audit-log", default=str(Path(__file__).with_name("lifecycle_audit_log.jsonl")))

    args = parser.parse_args(argv)
    if args.command in {
        "create-session",
        "show-session",
        "mark-signed",
        "record-submission",
        "record-result",
        "mark-validated",
        "mark-failed",
    }:
        require_manual_confirmation(args.confirmation)
        return _handle_session_command(args)

    intent = load_intent_file(args.file)

    if args.command == "load-intent":
        print(_json(intent.to_dict()))
        return 0
    if args.command == "validate-intent":
        failures = validate_safety_gates(intent)
        print(_json({"valid": not failures, "blocked_reasons": failures, "is_executable": False}))
        return 1 if failures else 0
    if args.command == "show-risk":
        print(_json(risk_summary(intent)))
        return 0
    if args.command == "build-tx":
        tx = build_unsigned_transaction(intent, account=args.account)
        body = {"fingerprint": transaction_fingerprint(tx), "txjson": tx, "is_executable": False}
        _write_or_print(body, args.out)
        return 0
    if args.command == "generate-xaman":
        tx = build_unsigned_transaction(intent, account=args.account)
        payload = build_xaman_payload(tx)
        body = {"payload": payload, "deep_link": build_deep_link(payload), "is_executable": False}
        _write_or_print(body, args.out)
        return 0
    if args.command == "wizard-preview":
        body = build_wizard_package(intent, account=args.account)
        _write_or_print(body, args.out)
        return 0
    if args.command == "submit":
        ensure_safety_gates(intent)
        require_manual_confirmation(args.confirmation)
        if not (args.understand_type and args.accept_partial_fill and args.understand_price_impact):
            raise ValueError("risk acknowledgement flags are required")
        tx = build_unsigned_transaction(intent, account=args.account)
        append_audit_record(
            intent_id=intent.intent_id,
            tx_type=str(tx["TransactionType"]),
            tx_payload=tx,
            user_confirmed=True,
            submitted=False,
            **audit_context(intent),
            path=args.audit_log,
        )
        print(_json({"submitted": False, "reason": "offline_cli_records_manual_confirmation_only", "is_executable": False}))
        return 0
    return 2


def _handle_session_command(args: argparse.Namespace) -> int:
    if args.command == "create-session":
        session = create_session_from_intent_file(
            args.file,
            account=args.account,
            session_log=args.session_log,
            audit_log=args.audit_log,
        )
        print(_json(session.to_dict()))
        return 0
    if args.command == "show-session":
        print(_json(load_session(args.session_id, session_log=args.session_log).to_dict()))
        return 0
    if args.command == "mark-signed":
        print(_json(mark_signed(args.session_id, session_log=args.session_log, audit_log=args.audit_log).to_dict()))
        return 0
    if args.command == "record-submission":
        print(_json(record_submission(args.session_id, args.tx_hash, session_log=args.session_log, audit_log=args.audit_log).to_dict()))
        return 0
    if args.command == "record-result":
        print(
            _json(
                record_result(
                    args.session_id,
                    args.engine_result,
                    engine_result_message=args.engine_result_message,
                    session_log=args.session_log,
                    audit_log=args.audit_log,
                ).to_dict()
            )
        )
        return 0
    if args.command == "mark-validated":
        print(_json(mark_validated(args.session_id, ledger_index=args.ledger_index, session_log=args.session_log, audit_log=args.audit_log).to_dict()))
        return 0
    if args.command == "mark-failed":
        print(_json(mark_failed(args.session_id, engine_result=args.engine_result, session_log=args.session_log, audit_log=args.audit_log).to_dict()))
        return 0
    return 2


def _write_or_print(body: dict[str, object], path: str | None) -> None:
    encoded = _json(body)
    if path:
        Path(path).write_text(encoded + "\n", encoding="utf-8")
    else:
        print(encoded)


def _json(body: dict[str, object]) -> str:
    return json.dumps(body, sort_keys=True, indent=2)


if __name__ == "__main__":
    raise SystemExit(main())

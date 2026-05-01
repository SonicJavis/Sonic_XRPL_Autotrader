from __future__ import annotations

import argparse
import json
from pathlib import Path

from execution_prototype.audit import append_audit_record
from execution_prototype.intent_contract import ensure_safety_gates, load_intent_file, risk_summary, validate_safety_gates
from execution_prototype.submit import CONFIRMATION_PHRASE, require_manual_confirmation
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

    submit_parser = sub.add_parser("submit")
    submit_parser.add_argument("file")
    submit_parser.add_argument("--account", default="rMANUAL_ACCOUNT_PLACEHOLDER")
    submit_parser.add_argument("--confirmation", required=True)
    submit_parser.add_argument("--audit-log", default=str(Path(__file__).with_name("audit_log.jsonl")))

    args = parser.parse_args(argv)
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
    if args.command == "submit":
        ensure_safety_gates(intent)
        require_manual_confirmation(args.confirmation)
        tx = build_unsigned_transaction(intent, account=args.account)
        append_audit_record(
            intent_id=intent.intent_id,
            tx_type=str(tx["TransactionType"]),
            tx_payload=tx,
            user_confirmed=True,
            submitted=False,
            path=args.audit_log,
        )
        print(_json({"submitted": False, "reason": "offline_cli_records_manual_confirmation_only", "is_executable": False}))
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

"""V2 CLI main entry point.

Usage:
  python -m sonic_xrpl.cli.main --help
  python -m sonic_xrpl.cli.main health
  python -m sonic_xrpl.cli.main audit
  python -m sonic_xrpl.cli.main capabilities
  python -m sonic_xrpl.cli.main safety-scan
  python -m sonic_xrpl.cli.main reconcile --help
  python -m sonic_xrpl.cli.main simulate --help

All commands work offline. No network access required by default.
"""

from __future__ import annotations

import argparse
import sys


def main(argv: list[str] | None = None) -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="sonic_xrpl",
        description="Sonic XRPL Autotrader V2 — Phase 45 Foundation",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="sonic_xrpl 2.0.0-alpha (Phase 45)",
    )

    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND")

    # health
    health_parser = subparsers.add_parser("health", help="Show system health")
    health_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # audit
    audit_parser = subparsers.add_parser("audit", help="Run V2 audit validator")
    audit_parser.add_argument(
        "--write-report",
        action="store_true",
        help="Write audit report to docs/audit/",
    )

    # capabilities
    subparsers.add_parser(
        "capabilities", help="Show XRPL protocol capability matrix"
    )

    # safety-scan
    safety_parser = subparsers.add_parser(
        "safety-scan", help="Run V2 safety scan"
    )
    safety_parser.add_argument("--verbose", action="store_true")
    safety_parser.add_argument(
        "--path",
        action="append",
        dest="scan_dirs",
        metavar="DIR",
        help=(
            "Scan only this directory (relative to repo root). "
            "May be specified multiple times. "
            "Defaults to the standard source-controlled directories."
        ),
    )
    safety_parser.add_argument(
        "--max-files",
        type=int,
        default=None,
        metavar="N",
        help="Stop after scanning N files (default: unlimited).",
    )
    safety_parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=None,
        metavar="T",
        help="Abort the scan after T seconds (default: no limit).",
    )

    # reconcile
    reconcile_parser = subparsers.add_parser(
        "reconcile", help="Run reconciliation (V2 + Phase 30 bridge)"
    )
    reconcile_parser.add_argument(
        "--legacy", action="store_true", help="Use Phase 30 legacy reconciliation"
    )

    # simulate
    simulate_parser = subparsers.add_parser(
        "simulate", help="Run simulation models (offline)"
    )
    simulate_parser.add_argument(
        "--amount", type=float, default=100.0, help="Trade amount"
    )
    simulate_parser.add_argument(
        "--model",
        choices=["fixed", "amm_impact", "orderbook_depth"],
        default="fixed",
        help="Fill model type",
    )

    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0

    if args.command == "health":
        return _cmd_health(args)
    if args.command == "audit":
        return _cmd_audit(args)
    if args.command == "capabilities":
        return _cmd_capabilities()
    if args.command == "safety-scan":
        return _cmd_safety_scan(args)
    if args.command == "reconcile":
        return _cmd_reconcile(args)
    if args.command == "simulate":
        return _cmd_simulate(args)

    parser.print_help()
    return 0


def _cmd_health(args) -> int:
    """Display system health."""
    from sonic_xrpl.telemetry.health import get_system_health

    health = get_system_health()

    if getattr(args, "json", False):
        import json
        print(json.dumps({
            "mode": health.mode.value,
            "live_trading_blocked": health.live_trading_blocked,
            "enabled_capabilities": health.enabled_capabilities,
            "notes": health.notes,
        }, indent=2))
    else:
        print("=== Sonic XRPL V2 — System Health ===")
        print(f"Mode               : {health.mode.value}")
        print(f"Live trading       : {'BLOCKED' if health.live_trading_blocked else 'ENABLED'}")
        print(f"Enabled capabilities: {len(health.enabled_capabilities)}")
        for note in health.notes:
            print(f"  {note}")

    return 0


def _cmd_audit(args) -> int:
    """Run V2 audit validator."""
    from pathlib import Path
    from sonic_xrpl.audit.validator import run_full_audit, write_reports

    repo_root = Path(__file__).resolve().parent.parent.parent.parent
    print("=== V2 Audit Validator ===")
    report = run_full_audit(repo_root)

    for check in report.checks:
        icon = "✅" if check.passed else ("⚠️ " if check.severity == "warning" else "❌")
        print(f"  {icon} {check.name}: {check.message}")

    print()
    print(
        f"Result: {report.passed_count} passed / "
        f"{report.failed_count} failed / "
        f"{report.warning_count} warnings"
    )

    if getattr(args, "write_report", False):
        write_reports(report, repo_root)
        print("Report written to docs/audit/latest_audit_report.{md,json}")

    return 0 if report.overall_passed else 1


def _cmd_capabilities() -> int:
    """Show protocol capability matrix."""
    from sonic_xrpl.protocol.capability_matrix import CAPABILITY_MATRIX
    from sonic_xrpl.protocol.amendments import AmendmentStatus

    print("=== XRPL Protocol Capability Matrix ===")
    print()

    groups = {
        AmendmentStatus.ENABLED: "ENABLED (usable)",
        AmendmentStatus.FEATURE_GATED: "FEATURE-GATED (not on mainnet)",
        AmendmentStatus.OBSOLETE: "OBSOLETE (do not use)",
        AmendmentStatus.RESEARCH_ONLY: "RESEARCH-ONLY",
    }

    for status, label in groups.items():
        caps = [
            name for name, cap in CAPABILITY_MATRIX.items()
            if cap.status == status
        ]
        if caps:
            print(f"  {label}:")
            for cap in sorted(caps):
                print(f"    - {cap}")
            print()

    return 0


def _cmd_safety_scan(args) -> int:
    """Run V2 safety scan."""
    import signal
    from pathlib import Path
    from sonic_xrpl.audit.safety_scan import (
        SafetyClassification,
        run_safety_scan,
        get_blocked_findings,
        get_review_findings,
    )

    repo_root = Path(__file__).resolve().parent.parent.parent.parent

    scan_dirs = getattr(args, "scan_dirs", None)  # None → default source dirs
    max_files = getattr(args, "max_files", None)
    timeout_seconds = getattr(args, "timeout_seconds", None)

    print("=== V2 Safety Scan ===")

    # Optional hard timeout via SIGALRM (Unix only; skipped on Windows).
    if timeout_seconds is not None:
        try:
            limit = timeout_seconds

            def _timeout_handler(signum, frame, _limit=limit):
                raise TimeoutError(f"Safety scan aborted after {_limit}s")

            signal.signal(signal.SIGALRM, _timeout_handler)
            signal.alarm(timeout_seconds)
        except (AttributeError, OSError):
            pass  # SIGALRM not available on Windows

    try:
        findings = run_safety_scan(repo_root, scan_dirs=scan_dirs, max_files=max_files)
    finally:
        if timeout_seconds is not None:
            try:
                signal.alarm(0)
            except (AttributeError, OSError):
                pass

    blocked = get_blocked_findings(findings)
    review = get_review_findings(findings)

    if blocked:
        print(f"\n❌ BLOCKED ({len(blocked)} findings):")
        for f in blocked[:10]:
            print(f"  {f.file_path}:{f.line_no}: {f.pattern} — {f.reason}")

    if review:
        print(f"\n⚠️  REQUIRES REVIEW ({len(review)} findings):")
        for f in review[:10]:
            print(f"  {f.file_path}:{f.line_no}: {f.pattern}")

    if getattr(args, "verbose", False):
        print(f"\nAll findings: {len(findings)}")
        for f in findings:
            print(f"  [{f.classification.value}] {f.file_path}:{f.line_no}")

    if not blocked:
        print(f"\n✅ Safety scan passed ({len(findings)} total findings, none blocked)")
        return 0
    else:
        print(f"\n❌ Safety scan failed ({len(blocked)} blocked findings)")
        return 1


def _cmd_reconcile(args) -> int:
    """Run reconciliation."""
    from sonic_xrpl.reconciliation.legacy_phase30_adapter import (
        LEGACY_AVAILABLE,
        get_legacy_status,
    )

    print("=== V2 Reconciliation ===")
    status = get_legacy_status()
    print(f"  Phase 30 legacy: {'available' if status['legacy_available'] else 'not available'}")

    if getattr(args, "legacy", False):
        if not LEGACY_AVAILABLE:
            print(f"  ⚠️  Legacy Phase 30 not available: {status['import_error']}")
            return 2
        print("  Using Phase 30 legacy reconciliation (bridge)")
    else:
        print("  Using V2 reconciliation")
        print("  (No data loaded — use integration mode for real reconciliation)")

    return 0


def _cmd_simulate(args) -> int:
    """Run simulation models."""
    from sonic_xrpl.simulation.fill_model import FillModelType, estimate_fill
    from sonic_xrpl.simulation.slippage import estimate_slippage
    from sonic_xrpl.simulation.fees import estimate_fee
    from sonic_xrpl.simulation.latency import estimate_latency

    amount = getattr(args, "amount", 100.0)
    model_str = getattr(args, "model", "fixed")
    model_type = FillModelType(model_str)

    print(f"=== V2 Simulation (amount={amount}, model={model_str}) ===")
    print()

    fill = estimate_fill(amount, model_type)
    print(f"  Fill estimate     : {fill.expected_fill_pct:.1%} ({fill.notes})")

    slippage = estimate_slippage(amount)
    print(f"  Slippage estimate : {slippage.basis_points:.1f} bps ({slippage.pct:.4%})")

    fee = estimate_fee()
    print(f"  Fee estimate      : {fee.base_fee_drops} drops base / {fee.escalated_fee_drops} drops escalated")

    latency = estimate_latency()
    print(f"  Latency estimate  : {latency.total_ms}ms total ({latency.ledger_close_ms}ms ledger + {latency.network_ms}ms network)")

    print()
    print("  NOTE: Simulation only — no guaranteed fills. Live submission is BLOCKED.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

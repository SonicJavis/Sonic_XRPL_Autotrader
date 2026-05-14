"""V2 CLI main entry point.

Usage:
  python -m sonic_xrpl.cli.main --help
  python -m sonic_xrpl.cli.main health
  python -m sonic_xrpl.cli.main audit
  python -m sonic_xrpl.cli.main capabilities
  python -m sonic_xrpl.cli.main safety-scan
  python -m sonic_xrpl.cli.main reconcile --help
  python -m sonic_xrpl.cli.main simulate --help
  python -m sonic_xrpl.cli.main market-snapshot --path tests/fixtures/xrpl
  python -m sonic_xrpl.cli.main market-snapshot-report --path tests/fixtures/xrpl
  python -m sonic_xrpl.cli.main firstledger-signals --fixture tests/fixtures/firstledger/source_backed_candidates.json
  python -m sonic_xrpl.cli.main firstledger-signal-report --fixture tests/fixtures/firstledger/source_backed_candidates.json --output-dir reports/phase49
  python -m sonic_xrpl.cli.main firstledger-intelligence --fixture tests/fixtures/firstledger_intelligence/source_backed_healthy.json
  python -m sonic_xrpl.cli.main firstledger-intelligence-report --fixture tests/fixtures/firstledger_intelligence/source_backed_healthy.json
  python -m sonic_xrpl.cli.main paper-sniper-simulation --fixture tests/fixtures/paper_sniper_simulation/healthy_candidate_simulated.json
  python -m sonic_xrpl.cli.main paper-sniper-simulation-report --fixture tests/fixtures/paper_sniper_simulation/healthy_candidate_simulated.json
  python -m sonic_xrpl.cli.main xaman-manual-approval-spec --fixture tests/fixtures/xaman_manual_approval_spec/healthy_design_only.json
  python -m sonic_xrpl.cli.main xaman-manual-approval-spec-report --fixture tests/fixtures/xaman_manual_approval_spec/healthy_design_only.json
  python -m sonic_xrpl.cli.main xaman-testnet-payload-spec --fixture tests/fixtures/xaman_testnet_payload_spec/healthy_design_review.json
  python -m sonic_xrpl.cli.main xaman-testnet-payload-spec-report --fixture tests/fixtures/xaman_testnet_payload_spec/healthy_design_review.json
  python -m sonic_xrpl.cli.main xaman-callback-verification-spec --fixture tests/fixtures/xaman_callback_verification_spec/healthy_callback_spec.json
  python -m sonic_xrpl.cli.main xaman-callback-verification-spec-report --fixture tests/fixtures/xaman_callback_verification_spec/healthy_callback_spec.json
  python -m sonic_xrpl.cli.main xaman-audit-idempotency-spec --fixture tests/fixtures/xaman_audit_idempotency_spec/healthy_audit_idempotency_spec.json
  python -m sonic_xrpl.cli.main xaman-audit-idempotency-spec-report --fixture tests/fixtures/xaman_audit_idempotency_spec/healthy_audit_idempotency_spec.json
  python -m sonic_xrpl.cli.main paper-outcomes --signals-fixture tests/fixtures/firstledger/source_backed_candidates.json --outcomes-fixture tests/fixtures/outcomes/paper_observations.json
  python -m sonic_xrpl.cli.main outcome-corpus --fixture tests/fixtures/outcome_corpus/source_backed_multi_window.json
  python -m sonic_xrpl.cli.main calibration-readiness --fixture tests/fixtures/calibration_review/sufficient_source_backed_evidence.json
  python -m sonic_xrpl.cli.main calibration-proposals --fixture tests/fixtures/calibration_proposal/ready_for_review_recommendations.json
  python -m sonic_xrpl.cli.main calibration-approval-ledger --proposal-fixture tests/fixtures/calibration_proposal/ready_for_review_recommendations.json --review-fixture tests/fixtures/calibration_approval/approved_change_request.json
  python -m sonic_xrpl.cli.main calibration-implementation-plan --approval-ledger reports/phase55/latest_calibration_approval_ledger.json --change-requests reports/phase55/latest_calibration_change_requests.json

All commands work offline. No network access required by default.
"""

from __future__ import annotations

import argparse
import sys


def main(argv: list[str] | None = None) -> int:
    """Main CLI entry point."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
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
    subparsers.add_parser("killswitch-status", help="Show persistent kill switch state")
    killswitch_toggle_parser = subparsers.add_parser("killswitch-toggle", help="Toggle persistent kill switch")
    killswitch_toggle_parser.add_argument("--active", choices=["true", "false"], required=True, help="Set active state")
    killswitch_toggle_parser.add_argument("--reason", default="manual_override", help="Reason for state change")
    killswitch_toggle_parser.add_argument("--actor", default="cli", help="Actor performing state change")

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

    # fixtures
    fixtures_parser = subparsers.add_parser("fixtures", help="Show fixture manifest info")
    fixtures_parser.add_argument("--path", required=True, help="Path to fixture directory")

    # fixture-health
    fixture_health_parser = subparsers.add_parser("fixture-health", help="Run fixture health check")
    fixture_health_parser.add_argument("--path", required=True, help="Path to fixture directory")

    # fixture-account
    fixture_account_parser = subparsers.add_parser("fixture-account", help="Show account info from fixture")
    fixture_account_parser.add_argument("--path", required=True, help="Path to fixture directory")
    fixture_account_parser.add_argument("--account", required=True, help="Account identifier (prefix match)")

    # fixture-amm
    fixture_amm_parser = subparsers.add_parser("fixture-amm", help="Show AMM info from fixture")
    fixture_amm_parser.add_argument("--path", required=True, help="Path to fixture directory")
    fixture_amm_parser.add_argument("--asset-a", required=True, help="Asset A (e.g. XRP)")
    fixture_amm_parser.add_argument("--asset-b", required=True, help="Asset B (e.g. USD_rIssuer)")

    # fixture-balance-changes
    fixture_bc_parser = subparsers.add_parser("fixture-balance-changes", help="Parse metadata and show balance changes")
    fixture_bc_parser.add_argument("--metadata", required=True, help="Path to metadata JSON file")

    # market-snapshot
    ms_parser = subparsers.add_parser("market-snapshot", help="Build and display a market snapshot from fixtures")
    ms_parser.add_argument("--path", required=True, help="Path to fixture directory")
    ms_parser.add_argument("--ledger-index", type=int, default=None, help="Ledger index to snapshot (default: latest)")
    ms_parser.add_argument("--account", action="append", dest="accounts", metavar="ACCOUNT", help="Account to include context for (may be repeated)")
    ms_parser.add_argument("--no-metadata", action="store_true", help="Skip metadata signal parsing")
    ms_parser.add_argument("--no-mpt", action="store_true", help="Skip MPT holder context")
    ms_parser.add_argument("--strict", action="store_true", help="Fail if fixture health check fails")
    ms_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # market-snapshot-report
    msr_parser = subparsers.add_parser("market-snapshot-report", help="Build market snapshot and write report files")
    msr_parser.add_argument("--path", required=True, help="Path to fixture directory")
    msr_parser.add_argument("--ledger-index", type=int, default=None, help="Ledger index to snapshot (default: latest)")
    msr_parser.add_argument("--account", action="append", dest="accounts", metavar="ACCOUNT", help="Account to include context for (may be repeated)")
    msr_parser.add_argument("--output-dir", default=None, help="Output directory for report files (default: reports/phase47/)")
    msr_parser.add_argument("--strict", action="store_true", help="Fail if fixture health check fails")

    fls_parser = subparsers.add_parser("firstledger-signals", help="Generate offline FirstLedger candidate signals from a fixture")
    fls_parser.add_argument("--fixture", required=True, help="Path to FirstLedger candidate fixture JSON")

    flr_parser = subparsers.add_parser("firstledger-signal-report", help="Write offline FirstLedger signal reports")
    flr_parser.add_argument("--fixture", required=True, help="Path to FirstLedger candidate fixture JSON")
    flr_parser.add_argument("--output-dir", required=True, help="Output directory for report files")
    fli_parser = subparsers.add_parser("firstledger-intelligence", help="Build Phase 59 offline FirstLedger intelligence verdicts")
    fli_parser.add_argument("--fixture", required=True, help="Path to FirstLedger intelligence fixture JSON")
    fli_parser.add_argument("--json", action="store_true", help="Output as JSON")
    flir_parser = subparsers.add_parser("firstledger-intelligence-report", help="Render Phase 59 intelligence report text")
    flir_parser.add_argument("--fixture", required=True, help="Path to FirstLedger intelligence fixture JSON")
    pss_parser = subparsers.add_parser("paper-sniper-simulation", help="Run Phase 60 paper-only sniper simulation harness")
    pss_parser.add_argument("--fixture", required=True, help="Path to paper-sniper simulation fixture JSON")
    pss_parser.add_argument("--json", action="store_true", help="Output as JSON")
    pssr_parser = subparsers.add_parser("paper-sniper-simulation-report", help="Render Phase 60 paper-sniper simulation markdown summary")
    pssr_parser.add_argument("--fixture", required=True, help="Path to paper-sniper simulation fixture JSON")
    xms_parser = subparsers.add_parser("xaman-manual-approval-spec", help="Run Phase 61 Xaman manual-approval design spec")
    xms_parser.add_argument("--fixture", required=True, help="Path to xaman manual-approval fixture JSON")
    xms_parser.add_argument("--json", action="store_true", help="Output as JSON")
    xmsr_parser = subparsers.add_parser("xaman-manual-approval-spec-report", help="Render Phase 61 Xaman manual-approval markdown summary")
    xmsr_parser.add_argument("--fixture", required=True, help="Path to xaman manual-approval fixture JSON")
    xtps_parser = subparsers.add_parser("xaman-testnet-payload-spec", help="Run Phase 62 Xaman testnet payload schema review")
    xtps_parser.add_argument("--fixture", required=True, help="Path to xaman testnet payload fixture JSON")
    xtps_parser.add_argument("--json", action="store_true", help="Output as JSON")
    xtpsr_parser = subparsers.add_parser("xaman-testnet-payload-spec-report", help="Render Phase 62 Xaman testnet payload markdown summary")
    xtpsr_parser.add_argument("--fixture", required=True, help="Path to xaman testnet payload fixture JSON")
    xcvs_parser = subparsers.add_parser("xaman-callback-verification-spec", help="Run Phase 63 callback authenticity and replay-verification design spec")
    xcvs_parser.add_argument("--fixture", required=True, help="Path to xaman callback verification fixture JSON")
    xcvs_parser.add_argument("--json", action="store_true", help="Output as JSON")
    xcvsr_parser = subparsers.add_parser("xaman-callback-verification-spec-report", help="Render Phase 63 callback verification markdown summary")
    xcvsr_parser.add_argument("--fixture", required=True, help="Path to xaman callback verification fixture JSON")
    xais_parser = subparsers.add_parser("xaman-audit-idempotency-spec", help="Run Phase 64 audit trail and idempotency store design spec")
    xais_parser.add_argument("--fixture", required=True, help="Path to xaman audit/idempotency fixture JSON")
    xais_parser.add_argument("--json", action="store_true", help="Output as JSON")
    xaisr_parser = subparsers.add_parser("xaman-audit-idempotency-spec-report", help="Render Phase 64 audit/idempotency markdown summary")
    xaisr_parser.add_argument("--fixture", required=True, help="Path to xaman audit/idempotency fixture JSON")

    # Phase 50: signal review workflow (paper-only)
    sigreview_parser = subparsers.add_parser("signal-review", help="Run Phase 50 signal review from Phase 49 outputs")
    sigreview_parser.add_argument("--fixture", required=True, help="Path to Phase 49 signals fixture (JSON file or FirstLedger evidence)" )
    sigreview_parser.add_argument("--output-dir", default="reports/phase50", help="Output directory for review results")

    sigreview_report_parser = subparsers.add_parser("signal-review-report", help="Write Phase 50 signal review report (PDF/Markdown/JSON)")
    sigreview_report_parser.add_argument("--fixture", required=True, help="Path to Phase 49 signals fixture")
    sigreview_report_parser.add_argument("--output-dir", required=True, help="Output directory for the report")

    paper_intents_parser = subparsers.add_parser("paper-intents", help="Generate offline paper intents from Phase 49 signals")
    paper_intents_parser.add_argument("--fixture", required=True, help="Path to Phase 49 signals fixture")

    paper_outcomes_parser = subparsers.add_parser("paper-outcomes", help="Attribute paper outcomes to Phase 49 signals")
    paper_outcomes_parser.add_argument("--signals-fixture", required=True, help="Path to Phase 49 signal source fixture")
    paper_outcomes_parser.add_argument("--outcomes-fixture", required=True, help="Path to Phase 51 paper observations fixture")

    paper_outcome_report_parser = subparsers.add_parser("paper-outcome-report", help="Write Phase 51 paper outcome reports")
    paper_outcome_report_parser.add_argument("--signals-fixture", required=True, help="Path to Phase 49 signal source fixture")
    paper_outcome_report_parser.add_argument("--outcomes-fixture", required=True, help="Path to Phase 51 paper observations fixture")
    paper_outcome_report_parser.add_argument("--output-dir", required=True, help="Output directory for report files")

    signal_feedback_report_parser = subparsers.add_parser("signal-feedback-report", help="Write Phase 51 signal feedback reports")
    signal_feedback_report_parser.add_argument("--signals-fixture", required=True, help="Path to Phase 49 signal source fixture")
    signal_feedback_report_parser.add_argument("--outcomes-fixture", required=True, help="Path to Phase 51 paper observations fixture")
    signal_feedback_report_parser.add_argument("--output-dir", required=True, help="Output directory for report files")

    outcome_corpus_parser = subparsers.add_parser("outcome-corpus", help="Build a Phase 52 paper observation replay corpus")
    outcome_corpus_parser.add_argument("--fixture", action="append", required=True, help="Outcome corpus fixture file or directory; may be repeated")

    outcome_corpus_report_parser = subparsers.add_parser("outcome-corpus-report", help="Write Phase 52 outcome corpus reports")
    outcome_corpus_report_parser.add_argument("--fixture", action="append", required=True, help="Outcome corpus fixture file or directory; may be repeated")
    outcome_corpus_report_parser.add_argument("--output-dir", default="reports/phase52", help="Output directory for report files")

    outcome_corpus_quality_parser = subparsers.add_parser("outcome-corpus-quality", help="Print Phase 52 outcome corpus quality")
    outcome_corpus_quality_parser.add_argument("--fixture", action="append", required=True, help="Outcome corpus fixture file or directory; may be repeated")

    calibration_readiness_parser = subparsers.add_parser("calibration-readiness", help="Run Phase 53 calibration readiness review")
    calibration_readiness_parser.add_argument("--fixture", required=True, help="Calibration review fixture or Phase 52 corpus report")

    calibration_readiness_report_parser = subparsers.add_parser("calibration-readiness-report", help="Write Phase 53 calibration readiness reports")
    calibration_readiness_report_parser.add_argument("--fixture", required=True, help="Calibration review fixture or Phase 52 corpus report")
    calibration_readiness_report_parser.add_argument("--output-dir", default="reports/phase53", help="Output directory for report files")

    calibration_recommendations_parser = subparsers.add_parser("calibration-recommendations", help="Print Phase 53 threshold recommendations")
    calibration_recommendations_parser.add_argument("--fixture", required=True, help="Calibration review fixture or Phase 52 corpus report")

    calibration_proposals_parser = subparsers.add_parser("calibration-proposals", help="Build Phase 54 human-reviewed calibration proposals")
    calibration_proposals_parser.add_argument("--fixture", required=True, help="Phase 53 recommendations report or Phase 54 fixture")

    calibration_proposal_report_parser = subparsers.add_parser("calibration-proposal-report", help="Write Phase 54 calibration proposal reports")
    calibration_proposal_report_parser.add_argument("--fixture", required=True, help="Phase 53 recommendations report or Phase 54 fixture")
    calibration_proposal_report_parser.add_argument("--output-dir", default="reports/phase54", help="Output directory for report files")

    calibration_proposal_diff_parser = subparsers.add_parser("calibration-proposal-diff", help="Print Phase 54 proposed-only calibration diff")
    calibration_proposal_diff_parser.add_argument("--fixture", required=True, help="Phase 53 recommendations report or Phase 54 fixture")

    calibration_approval_parser = subparsers.add_parser("calibration-approval-ledger", help="Build Phase 55 approval ledger")
    calibration_approval_parser.add_argument("--proposal-fixture", required=True, help="Phase 54 proposal fixture or report")
    calibration_approval_parser.add_argument("--review-fixture", required=True, help="Phase 55 human review fixture")

    calibration_change_requests_parser = subparsers.add_parser("calibration-change-requests", help="Print Phase 55 change request artifacts")
    calibration_change_requests_parser.add_argument("--proposal-fixture", required=True, help="Phase 54 proposal fixture or report")
    calibration_change_requests_parser.add_argument("--review-fixture", required=True, help="Phase 55 human review fixture")

    calibration_approval_report_parser = subparsers.add_parser("calibration-approval-report", help="Write Phase 55 approval ledger reports")
    calibration_approval_report_parser.add_argument("--proposal-fixture", required=True, help="Phase 54 proposal fixture or report")
    calibration_approval_report_parser.add_argument("--review-fixture", required=True, help="Phase 55 human review fixture")
    calibration_approval_report_parser.add_argument("--output-dir", default="reports/phase55", help="Output directory for report files")

    calibration_impl_plan_parser = subparsers.add_parser("calibration-implementation-plan", help="Build Phase 56 implementation plan from Phase 55 artifacts")
    calibration_impl_plan_parser.add_argument("--approval-ledger", required=True, help="Phase 55 approval ledger JSON")
    calibration_impl_plan_parser.add_argument("--change-requests", required=True, help="Phase 55 change requests JSON")

    calibration_impl_dry_run_parser = subparsers.add_parser("calibration-implementation-dry-run", help="Render Phase 56 dry-run implementation preview")
    calibration_impl_dry_run_parser.add_argument("--approval-ledger", required=True, help="Phase 55 approval ledger JSON")
    calibration_impl_dry_run_parser.add_argument("--change-requests", required=True, help="Phase 55 change requests JSON")

    calibration_impl_report_parser = subparsers.add_parser("calibration-implementation-report", help="Write Phase 56 implementation plan and dry-run reports")
    calibration_impl_report_parser.add_argument("--approval-ledger", required=True, help="Phase 55 approval ledger JSON")
    calibration_impl_report_parser.add_argument("--change-requests", required=True, help="Phase 55 change requests JSON")
    calibration_impl_report_parser.add_argument("--output-dir", default="reports/phase56", help="Output directory for report files")

    runtime_profile_parser = subparsers.add_parser("runtime-profile", help="Show Phase 57 consolidated runtime profile")
    runtime_profile_parser.add_argument("--json", action="store_true", help="Output as JSON")

    runtime_profile_conformance_parser = subparsers.add_parser("runtime-profile-conformance", help="Run Phase 57 runtime profile conformance checks")
    runtime_profile_conformance_parser.add_argument("--json", action="store_true", help="Output as JSON")

    runtime_profile_report_parser = subparsers.add_parser("runtime-profile-report", help="Write Phase 57 runtime profile and conformance reports")
    runtime_profile_report_parser.add_argument("--output-dir", default="reports/phase57", help="Output directory for report files")

    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0

    if args.command == "health":
        return _cmd_health(args)
    if args.command == "killswitch-status":
        return _cmd_killswitch_status()
    if args.command == "killswitch-toggle":
        return _cmd_killswitch_toggle(args)
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
    if args.command == "fixtures":
        return _cmd_fixtures(args)
    if args.command == "fixture-health":
        return _cmd_fixture_health(args)
    if args.command == "fixture-account":
        return _cmd_fixture_account(args)
    if args.command == "fixture-amm":
        return _cmd_fixture_amm(args)
    if args.command == "fixture-balance-changes":
        return _cmd_fixture_balance_changes(args)
    if args.command == "market-snapshot":
        return _cmd_market_snapshot(args)
    if args.command == "market-snapshot-report":
        return _cmd_market_snapshot_report(args)
    if args.command == "firstledger-signals":
        return _cmd_firstledger_signals(args)
    if args.command == "firstledger-signal-report":
        return _cmd_firstledger_signal_report(args)
    if args.command == "firstledger-intelligence":
        return _cmd_firstledger_intelligence(args)
    if args.command == "firstledger-intelligence-report":
        return _cmd_firstledger_intelligence_report(args)
    if args.command == "paper-sniper-simulation":
        return _cmd_paper_sniper_simulation(args)
    if args.command == "paper-sniper-simulation-report":
        return _cmd_paper_sniper_simulation_report(args)
    if args.command == "xaman-manual-approval-spec":
        return _cmd_xaman_manual_approval_spec(args)
    if args.command == "xaman-manual-approval-spec-report":
        return _cmd_xaman_manual_approval_spec_report(args)
    if args.command == "xaman-testnet-payload-spec":
        return _cmd_xaman_testnet_payload_spec(args)
    if args.command == "xaman-testnet-payload-spec-report":
        return _cmd_xaman_testnet_payload_spec_report(args)
    if args.command == "xaman-callback-verification-spec":
        return _cmd_xaman_callback_verification_spec(args)
    if args.command == "xaman-callback-verification-spec-report":
        return _cmd_xaman_callback_verification_spec_report(args)
    if args.command == "xaman-audit-idempotency-spec":
        return _cmd_xaman_audit_idempotency_spec(args)
    if args.command == "xaman-audit-idempotency-spec-report":
        return _cmd_xaman_audit_idempotency_spec_report(args)

    if args.command == "signal-review":
        return _cmd_signal_review(args)
    if args.command == "signal-review-report":
        return _cmd_signal_review_report(args)
    if args.command == "paper-intents":
        return _cmd_paper_intents(args)
    if args.command == "paper-outcomes":
        return _cmd_paper_outcomes(args)
    if args.command == "paper-outcome-report":
        return _cmd_paper_outcome_report(args)
    if args.command == "signal-feedback-report":
        return _cmd_signal_feedback_report(args)
    if args.command == "outcome-corpus":
        return _cmd_outcome_corpus(args)
    if args.command == "outcome-corpus-report":
        return _cmd_outcome_corpus_report(args)
    if args.command == "outcome-corpus-quality":
        return _cmd_outcome_corpus_quality(args)
    if args.command == "calibration-readiness":
        return _cmd_calibration_readiness(args)
    if args.command == "calibration-readiness-report":
        return _cmd_calibration_readiness_report(args)
    if args.command == "calibration-recommendations":
        return _cmd_calibration_recommendations(args)
    if args.command == "calibration-proposals":
        return _cmd_calibration_proposals(args)
    if args.command == "calibration-proposal-report":
        return _cmd_calibration_proposal_report(args)
    if args.command == "calibration-proposal-diff":
        return _cmd_calibration_proposal_diff(args)
    if args.command == "calibration-approval-ledger":
        return _cmd_calibration_approval_ledger(args)
    if args.command == "calibration-change-requests":
        return _cmd_calibration_change_requests(args)
    if args.command == "calibration-approval-report":
        return _cmd_calibration_approval_report(args)
    if args.command == "calibration-implementation-plan":
        return _cmd_calibration_implementation_plan(args)
    if args.command == "calibration-implementation-dry-run":
        return _cmd_calibration_implementation_dry_run(args)
    if args.command == "calibration-implementation-report":
        return _cmd_calibration_implementation_report(args)
    if args.command == "runtime-profile":
        return _cmd_runtime_profile(args)
    if args.command == "runtime-profile-conformance":
        return _cmd_runtime_profile_conformance(args)
    if args.command == "runtime-profile-report":
        return _cmd_runtime_profile_report(args)

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
            "killswitch_active": health.killswitch_active,
            "enabled_capabilities": health.enabled_capabilities,
            "notes": health.notes,
        }, indent=2))
    else:
        print("=== Sonic XRPL V2 — System Health ===")
        print(f"Mode               : {health.mode.value}")
        print(f"Live trading       : {'BLOCKED' if health.live_trading_blocked else 'ENABLED'}")
        print(f"Kill switch        : {'ACTIVE' if health.killswitch_active else 'OFF'}")
        print(f"Enabled capabilities: {len(health.enabled_capabilities)}")
        for note in health.notes:
            print(f"  {note}")

    return 0


def _cmd_killswitch_status() -> int:
    """Show persistent kill switch status."""
    from sonic_xrpl.core.config import load_config
    from sonic_xrpl.core.killswitch import PersistentKillSwitch

    cfg = load_config()
    store = PersistentKillSwitch(cfg.killswitch_db_path)
    state = store.get_state()
    store.close()
    print("=== Persistent Kill Switch ===")
    print(f"active    : {str(state.is_active).lower()}")
    print(f"updated_at: {state.updated_at}")
    print(f"reason    : {state.reason}")
    print(f"updated_by: {state.updated_by}")
    return 0


def _cmd_killswitch_toggle(args) -> int:
    """Toggle persistent kill switch status."""
    from sonic_xrpl.core.config import load_config
    from sonic_xrpl.core.killswitch import PersistentKillSwitch

    cfg = load_config()
    active = str(args.active).lower() == "true"
    store = PersistentKillSwitch(cfg.killswitch_db_path)
    state = store.set_state(
        is_active=active,
        reason=str(args.reason),
        updated_by=str(args.actor),
    )
    store.close()
    print("=== Persistent Kill Switch Updated ===")
    print(f"active    : {str(state.is_active).lower()}")
    print(f"updated_at: {state.updated_at}")
    print(f"reason    : {state.reason}")
    print(f"updated_by: {state.updated_by}")
    return 0


def _cmd_audit(args) -> int:
    """Run V2 audit validator."""
    from pathlib import Path
    from sonic_xrpl.audit.validator import run_full_audit, write_reports

    repo_root = Path(__file__).resolve().parent.parent.parent.parent
    print("=== V2 Audit Validator ===")
    report = run_full_audit(repo_root)

    for check in report.checks:
        icon = "✅" if check.passed else ("WARN" if check.severity == "warning" else "❌")
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
        print(f"\nWARN REQUIRES REVIEW ({len(review)} findings):")
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
            print(f"  WARN Legacy Phase 30 not available: {status['import_error']}")
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


def _cmd_fixtures(args) -> int:
    """Show fixture manifest info."""
    from pathlib import Path
    from sonic_xrpl.providers.fixture_manifest import load_manifest
    from sonic_xrpl.providers.errors import FixtureMissingError

    fixture_dir = Path(args.path)
    try:
        manifest = load_manifest(fixture_dir)
    except FixtureMissingError as exc:
        print(f"❌ {exc}")
        return 1

    print("=== Fixture Manifest ===")
    print(f"  Name       : {manifest.name}")
    print(f"  Version    : {manifest.version}")
    print(f"  Network    : {manifest.network}")
    print(f"  Created    : {manifest.created_at}")
    print(f"  Ledger range: {manifest.ledger_min} – {manifest.ledger_max}")
    print(f"  Accounts   : {manifest.account_count}")
    print(f"  Transactions: {manifest.transaction_count}")
    print(f"  AMM pools  : {manifest.amm_count}")
    print(f"  Orderbooks : {manifest.orderbook_count}")
    if manifest.limitations:
        print(f"  Limitations: {'; '.join(manifest.limitations)}")
    return 0


def _cmd_fixture_health(args) -> int:
    """Run fixture health check."""
    from pathlib import Path
    from sonic_xrpl.providers.health import check_fixture_health, HealthStatus

    fixture_dir = Path(args.path)
    report = check_fixture_health(fixture_dir)

    print("=== Fixture Health ===")
    print(f"  Status     : {report.status.value.upper()}")
    print(f"  Manifest OK: {report.manifest_ok}")
    print(f"  Security scan: {'OK' if report.secret_scan_ok else 'ISSUES'}")
    for d, ok in report.dirs_ok.items():
        print(f"  dir/{d}: {'✅' if ok else '❌'}")
    if report.issues:
        print("  Issues:")
        for issue in report.issues:
            print(f"    - {issue}")
    return 0 if report.status == HealthStatus.HEALTHY else 1


def _cmd_fixture_account(args) -> int:
    """Show account info from fixture."""
    import json
    from pathlib import Path
    from sonic_xrpl.providers.fixture_store import FixtureStore
    from sonic_xrpl.providers.errors import FixtureMissingError

    fixture_dir = Path(args.path)
    store = FixtureStore(fixture_dir)
    account = args.account

    info = None
    try:
        info = store.load_account_info(account)
    except FixtureMissingError:
        accounts_dir = fixture_dir / "accounts"
        if accounts_dir.exists():
            for f in accounts_dir.glob("*.json"):
                if account.lower() in f.stem.lower():
                    try:
                        info = json.loads(f.read_text())
                        break
                    except Exception:
                        continue

    if info is None:
        print(f"❌ Account not found: {account}")
        return 1

    print("=== Account Info ===")
    acct = info.get("account_data", {})
    print(f"  Account  : {acct.get('Account', account)}")
    print(f"  Balance  : {acct.get('Balance', '?')} drops")
    print(f"  Sequence : {acct.get('Sequence', '?')}")
    print(f"  Flags    : {acct.get('Flags', '?')}")
    return 0


def _cmd_fixture_amm(args) -> int:
    """Show AMM info from fixture."""
    from pathlib import Path
    from sonic_xrpl.providers.fixture_store import FixtureStore
    from sonic_xrpl.providers.errors import FixtureMissingError

    fixture_dir = Path(args.path)
    store = FixtureStore(fixture_dir)
    asset_a = args.asset_a
    asset_b = args.asset_b

    try:
        amm = store.load_amm_info(asset_a, asset_b)
    except FixtureMissingError as exc:
        print(f"❌ {exc}")
        return 1

    print("=== AMM Info ===")
    amm_data = amm.get("amm", amm)
    print(f"  Account    : {amm_data.get('amm_account', '?')}")
    print(f"  Amount     : {amm_data.get('amount', '?')}")
    print(f"  Amount2    : {amm_data.get('amount2', '?')}")
    print(f"  Trading fee: {amm_data.get('trading_fee', '?')}")
    return 0


def _cmd_fixture_balance_changes(args) -> int:
    """Parse metadata file and show balance changes."""
    import json
    from pathlib import Path
    from sonic_xrpl.providers.balance_changes import extract_balance_changes

    metadata_path = Path(args.metadata)
    if not metadata_path.exists():
        print(f"❌ Metadata file not found: {metadata_path}")
        return 1

    try:
        metadata = json.loads(metadata_path.read_text())
    except Exception as exc:
        print(f"❌ Failed to parse metadata: {exc}")
        return 1

    changes = extract_balance_changes(metadata)
    print("=== Balance Changes ===")
    if not changes:
        print("  (none)")
    for ch in changes:
        print(f"  {ch.account}: {ch.value} {ch.asset_key}")
    return 0


def _cmd_market_snapshot(args) -> int:
    """Build and display a market snapshot from fixture data."""
    import json as _json
    from pathlib import Path
    from sonic_xrpl.market.snapshot_builder import build_market_snapshot
    from sonic_xrpl.market.errors import SnapshotBuildError, FixtureHealthError

    fixture_path = Path(args.path)
    accounts = getattr(args, "accounts", None) or []
    ledger_index = getattr(args, "ledger_index", None)
    include_metadata = not getattr(args, "no_metadata", False)
    include_mpt = not getattr(args, "no_mpt", False)
    strict = getattr(args, "strict", False)
    as_json = getattr(args, "json", False)

    try:
        snapshot = build_market_snapshot(
            fixture_path,
            ledger_index=ledger_index,
            accounts=accounts,
            include_metadata=include_metadata,
            include_mpt=include_mpt,
            strict=strict,
        )
    except (SnapshotBuildError, FixtureHealthError) as exc:
        print(f"❌ {exc}")
        return 1

    if as_json:
        from dataclasses import asdict
        print(_json.dumps(asdict(snapshot), indent=2, default=str))
        return 0

    print("=== Market Snapshot ===")
    print(f"  Snapshot ID  : {snapshot.snapshot_id}")
    print(f"  Created      : {snapshot.created_at}")
    print(f"  Fixture ID   : {snapshot.fixture_id}")
    print(f"  Ledger index : {snapshot.ledger_index}")
    print(f"  Network      : {snapshot.network}")
    print()
    print(f"  Assets       : {len(snapshot.assets)}")
    print(f"  AMM pools    : {len(snapshot.amms)}")
    print(f"  Orderbooks   : {len(snapshot.orderbooks)}")
    print(f"  Accounts     : {len(snapshot.accounts)}")
    print(f"  Trustlines   : {len(snapshot.trustlines)}")
    print(f"  MPT holders  : {len(snapshot.mpt_holders)}")
    print(f"  Metadata signals: {len(snapshot.metadata_signals)}")
    print()
    print(f"  Quality score: {snapshot.quality.score}/100")
    print(f"  Recommendation: {snapshot.quality.recommendation.value}")
    if snapshot.quality.missing_sections:
        print(f"  Missing sections: {', '.join(snapshot.quality.missing_sections)}")
    if snapshot.quality.protocol_warnings:
        print(f"  Protocol warnings:")
        for w in snapshot.quality.protocol_warnings:
            print(f"    WARN {w}")
    if snapshot.limitations:
        print(f"  Limitations:")
        for lim in snapshot.limitations[:5]:
            print(f"    - {lim}")
    print()
    print("  NOTE: Offline snapshot only — no live data, no execution.")
    return 0


def _cmd_market_snapshot_report(args) -> int:
    """Build a market snapshot and write JSON + Markdown report files."""
    from pathlib import Path
    from sonic_xrpl.market.snapshot_builder import build_market_snapshot
    from sonic_xrpl.market.report_writer import write_snapshot_report, write_snapshot_summary
    from sonic_xrpl.market.errors import SnapshotBuildError, FixtureHealthError

    fixture_path = Path(args.path)
    accounts = getattr(args, "accounts", None) or []
    ledger_index = getattr(args, "ledger_index", None)
    output_dir = getattr(args, "output_dir", None)
    strict = getattr(args, "strict", False)

    try:
        snapshot = build_market_snapshot(
            fixture_path,
            ledger_index=ledger_index,
            accounts=accounts,
            strict=strict,
        )
    except (SnapshotBuildError, FixtureHealthError) as exc:
        print(f"❌ {exc}")
        return 1

    json_path = write_snapshot_report(snapshot, output_dir)
    md_path = write_snapshot_summary(snapshot, output_dir)

    print("=== Market Snapshot Report ===")
    print(f"  Snapshot ID  : {snapshot.snapshot_id}")
    print(f"  Quality score: {snapshot.quality.score}/100 ({snapshot.quality.recommendation.value})")
    print(f"  JSON report  : {json_path}")
    print(f"  Summary      : {md_path}")
    return 0


def _cmd_firstledger_signals(args) -> int:
    """Generate deterministic offline FirstLedger candidate signals."""
    from sonic_xrpl.signals.firstledger_candidate import EMPTY_STATE, load_firstledger_candidate_evidence
    from sonic_xrpl.signals.classifier import classify_candidates

    candidates = load_firstledger_candidate_evidence(args.fixture)
    signals = classify_candidates(candidates)
    print("=== Phase 49 FirstLedger Signals ===")
    print("  Offline/read-only: yes")
    print("  Live execution    : BLOCKED")
    if not signals:
        print(f"  {EMPTY_STATE}")
        return 0
    for candidate, signal in zip(sorted(candidates, key=lambda c: c.candidate_id), signals):
        label = "synthetic fixture" if candidate.synthetic else "source-backed fixture"
        print(f"  - {signal.candidate_id}: {signal.signal_type.value} confidence={signal.confidence_score}/100 risk={signal.risk_score}/100 ({label})")
        print(f"    source={candidate.source_url or candidate.source_type or 'unknown'}")
        if signal.missing_required_evidence:
            print(f"    missing={', '.join(signal.missing_required_evidence)}")
        if signal.limitations:
            print(f"    limitations={'; '.join(signal.limitations)}")
        print("    live_execution_allowed=False")
    return 0


def _cmd_firstledger_signal_report(args) -> int:
    """Write deterministic offline FirstLedger signal reports."""
    from sonic_xrpl.signals.firstledger_candidate import generate_firstledger_signals
    from sonic_xrpl.signals.report_writer import write_signal_report

    signals = generate_firstledger_signals(args.fixture)
    json_path, md_path = write_signal_report(signals, args.output_dir)
    print("=== Phase 49 FirstLedger Signal Report ===")
    print("  Offline/read-only: yes")
    print("  Live execution    : BLOCKED")
    print(f"  Signals          : {len(signals)}")
    print(f"  JSON report      : {json_path}")
    print(f"  Summary          : {md_path}")
    return 0


def _phase59_intelligence(args):
    from sonic_xrpl.firstledger_intelligence import (
        build_intelligence_results,
        load_firstledger_intelligence_inputs,
    )

    inputs = load_firstledger_intelligence_inputs(args.fixture)
    return build_intelligence_results(inputs)


def _cmd_firstledger_intelligence(args) -> int:
    """Build Phase 59 FirstLedger intelligence verdicts (offline only)."""
    from sonic_xrpl.firstledger_intelligence.reporting import report_to_json_text

    results = _phase59_intelligence(args)
    if getattr(args, "json", False):
        print(report_to_json_text(results))
        return 0

    print("=== Phase 59 FirstLedger Intelligence ===")
    print("  Offline           : True")
    print("  Paper-only        : True")
    print("  Non-executing     : True")
    print("  Live execution    : BLOCKED")
    for item in results:
        print(
            f"  - {item.candidate_id}: {item.verdict.value} "
            f"confidence={item.confidence.score}/100 "
            f"paper_only={item.paper_only} live_execution_allowed={item.live_execution_allowed}"
        )
    return 0


def _cmd_firstledger_intelligence_report(args) -> int:
    """Render Phase 59 FirstLedger intelligence markdown report text."""
    from sonic_xrpl.firstledger_intelligence.reporting import render_intelligence_markdown

    results = _phase59_intelligence(args)
    print(render_intelligence_markdown(results))
    return 0


def _phase60_paper_sniper(args):
    from sonic_xrpl.paper_sniper_simulation import load_paper_sniper_batch, run_paper_sniper_simulation

    return run_paper_sniper_simulation(load_paper_sniper_batch(args.fixture))


def _cmd_paper_sniper_simulation(args) -> int:
    """Run Phase 60 paper-only sniper simulation harness."""
    from sonic_xrpl.paper_sniper_simulation.reporting import render_paper_sniper_report_json

    report = _phase60_paper_sniper(args)
    if getattr(args, "json", False):
        print(render_paper_sniper_report_json(report))
        return 0

    print("=== Phase 60 Paper Sniper Simulation ===")
    print("  Offline            : True")
    print("  Paper-only         : True")
    print("  Non-executing      : True")
    print("  Investment advice  : BLOCKED")
    print("  Live execution     : BLOCKED")
    print(f"  Total candidates   : {report.total_candidates}")
    print(f"  Simulated          : {report.simulated_candidates}")
    print(f"  Rejected           : {report.rejected_candidates}")
    print(f"  No-fill            : {report.no_fill_candidates}")
    print(f"  Partial-fill       : {report.partial_fill_candidates}")
    for item in report.results:
        print(
            f"  - {item.candidate_id}: {item.simulation_decision.value} "
            f"fill={item.fill_assumption.label.value} "
            f"paper_only={item.paper_only} live_execution_allowed={item.live_execution_allowed}"
        )
    return 0


def _cmd_paper_sniper_simulation_report(args) -> int:
    """Render Phase 60 paper-sniper simulation markdown text."""
    from sonic_xrpl.paper_sniper_simulation.reporting import render_paper_sniper_report_markdown

    report = _phase60_paper_sniper(args)
    print(render_paper_sniper_report_markdown(report))
    return 0


def _phase61_xaman_spec(args):
    from sonic_xrpl.xaman_manual_approval_spec import build_manual_approval_spec, load_manual_approval_spec_fixture

    return build_manual_approval_spec(load_manual_approval_spec_fixture(args.fixture))


def _cmd_xaman_manual_approval_spec(args) -> int:
    """Run Phase 61 design-spec-only Xaman manual approval workflow."""
    from sonic_xrpl.xaman_manual_approval_spec.reporting import (
        render_manual_approval_spec_json,
        render_manual_approval_spec_payload,
    )

    report = _phase61_xaman_spec(args)
    if getattr(args, "json", False):
        print(render_manual_approval_spec_json(report))
        return 0

    payload = render_manual_approval_spec_payload(report)
    print("=== Phase 61 Xaman Manual Approval Design Spec ===")
    print(f"  Fixture                  : {payload['fixture_id']}")
    print(f"  design_spec_only         : {payload['design_spec_only']}")
    print(f"  manual_approval_required : {payload['manual_approval_required']}")
    print(f"  payload_creation_allowed : {payload['payload_creation_allowed']}")
    print(f"  signing_allowed          : {payload['signing_allowed']}")
    print(f"  submission_allowed       : {payload['submission_allowed']}")
    print(f"  live_execution_allowed   : {payload['live_execution_allowed']}")
    print(f"  valid_design_spec        : {payload['valid_design_spec']}")
    for item in payload["validation_errors"]:
        print(f"  - error: {item}")
    return 0


def _cmd_xaman_manual_approval_spec_report(args) -> int:
    """Render Phase 61 design-spec-only Xaman manual approval markdown report."""
    from sonic_xrpl.xaman_manual_approval_spec.reporting import render_manual_approval_spec_markdown

    print(render_manual_approval_spec_markdown(_phase61_xaman_spec(args)))
    return 0


def _phase62_xaman_testnet_spec(args):
    from sonic_xrpl.xaman_testnet_payload_spec import (
        build_xaman_testnet_payload_spec,
        load_xaman_testnet_payload_fixture,
    )

    return build_xaman_testnet_payload_spec(load_xaman_testnet_payload_fixture(args.fixture))


def _cmd_xaman_testnet_payload_spec(args) -> int:
    """Run Phase 62 design-spec-only Xaman testnet payload schema review."""
    from sonic_xrpl.xaman_testnet_payload_spec.reporting import (
        render_xaman_testnet_payload_spec_json,
        render_xaman_testnet_payload_spec_payload,
    )

    report = _phase62_xaman_testnet_spec(args)
    if getattr(args, "json", False):
        print(render_xaman_testnet_payload_spec_json(report))
        return 0
    payload = render_xaman_testnet_payload_spec_payload(report)
    print("=== Phase 62 Xaman Testnet Payload Spec ===")
    print(f"  Fixture                  : {payload['fixture_id']}")
    print(f"  design_spec_only         : {payload['design_spec_only']}")
    print(f"  payload_creation_allowed : {payload['payload_creation_allowed']}")
    print(f"  xaman_api_calls_allowed  : {payload['xaman_api_calls_allowed']}")
    print(f"  signing_allowed          : {payload['signing_allowed']}")
    print(f"  submission_allowed       : {payload['submission_allowed']}")
    print(f"  live_execution_allowed   : {payload['live_execution_allowed']}")
    print(f"  valid_design_spec        : {payload['valid_design_spec']}")
    for item in payload["validation_errors"]:
        print(f"  - error: {item}")
    return 0


def _cmd_xaman_testnet_payload_spec_report(args) -> int:
    """Render Phase 62 design-spec-only Xaman testnet payload markdown report."""
    from sonic_xrpl.xaman_testnet_payload_spec.reporting import render_xaman_testnet_payload_spec_markdown

    print(render_xaman_testnet_payload_spec_markdown(_phase62_xaman_testnet_spec(args)))
    return 0


def _phase63_xaman_callback_spec(args):
    from sonic_xrpl.xaman_callback_verification_spec import (
        build_xaman_callback_verification_spec,
        load_xaman_callback_verification_fixture,
    )

    return build_xaman_callback_verification_spec(load_xaman_callback_verification_fixture(args.fixture))


def _cmd_xaman_callback_verification_spec(args) -> int:
    """Run Phase 63 callback verification design-spec review."""
    from sonic_xrpl.xaman_callback_verification_spec.reporting import (
        render_xaman_callback_verification_spec_json,
        render_xaman_callback_verification_spec_payload,
    )

    report = _phase63_xaman_callback_spec(args)
    if getattr(args, "json", False):
        print(render_xaman_callback_verification_spec_json(report))
        return 0
    payload = render_xaman_callback_verification_spec_payload(report)
    print("=== Phase 63 Xaman Callback Verification Spec ===")
    print(f"  Fixture                          : {payload['fixture_id']}")
    print(f"  callback_spec_only               : {payload['callback_spec_only']}")
    print(f"  verification_design_only         : {payload['verification_design_only']}")
    print(f"  runtime_callback_handler_allowed : {payload['runtime_callback_handler_allowed']}")
    print(f"  webhook_runtime_allowed          : {payload['webhook_runtime_allowed']}")
    print(f"  payload_creation_allowed         : {payload['payload_creation_allowed']}")
    print(f"  xaman_api_calls_allowed          : {payload['xaman_api_calls_allowed']}")
    print(f"  signing_allowed                  : {payload['signing_allowed']}")
    print(f"  submission_allowed               : {payload['submission_allowed']}")
    print(f"  testnet_execution_allowed        : {payload['testnet_execution_allowed']}")
    print(f"  live_execution_allowed           : {payload['live_execution_allowed']}")
    print(f"  valid_design_spec                : {payload['valid_design_spec']}")
    for item in payload["validation_errors"]:
        print(f"  - error: {item}")
    return 0


def _cmd_xaman_callback_verification_spec_report(args) -> int:
    """Render Phase 63 callback verification design-spec markdown report."""
    from sonic_xrpl.xaman_callback_verification_spec.reporting import render_xaman_callback_verification_spec_markdown

    print(render_xaman_callback_verification_spec_markdown(_phase63_xaman_callback_spec(args)))
    return 0


def _phase64_xaman_audit_idempotency_spec(args):
    from sonic_xrpl.xaman_audit_idempotency_spec import (
        build_xaman_audit_idempotency_spec,
        load_xaman_audit_idempotency_fixture,
    )

    return build_xaman_audit_idempotency_spec(load_xaman_audit_idempotency_fixture(args.fixture))


def _cmd_xaman_audit_idempotency_spec(args) -> int:
    """Run Phase 64 audit/idempotency design-spec review."""
    from sonic_xrpl.xaman_audit_idempotency_spec.reporting import (
        render_xaman_audit_idempotency_spec_json,
        render_xaman_audit_idempotency_spec_payload,
    )

    report = _phase64_xaman_audit_idempotency_spec(args)
    if getattr(args, "json", False):
        print(render_xaman_audit_idempotency_spec_json(report))
        return 0
    payload = render_xaman_audit_idempotency_spec_payload(report)
    print("=== Phase 64 Xaman Audit/Idempotency Spec ===")
    print(f"  Fixture                          : {payload['fixture_id']}")
    print(f"  outcome                          : {payload['outcome']}")
    print(f"  audit_spec_only                  : {payload['audit_spec_only']}")
    print(f"  idempotency_spec_only            : {payload['idempotency_spec_only']}")
    print(f"  persistence_implementation_allowed: {payload['persistence_implementation_allowed']}")
    print(f"  database_writes_allowed          : {payload['database_writes_allowed']}")
    print(f"  callback_handler_allowed         : {payload['callback_handler_allowed']}")
    print(f"  webhook_runtime_allowed          : {payload['webhook_runtime_allowed']}")
    print(f"  payload_creation_allowed         : {payload['payload_creation_allowed']}")
    print(f"  xaman_api_calls_allowed          : {payload['xaman_api_calls_allowed']}")
    print(f"  testnet_execution_allowed        : {payload['testnet_execution_allowed']}")
    print(f"  live_execution_allowed           : {payload['live_execution_allowed']}")
    for item in payload["validation_errors"]:
        print(f"  - error: {item}")
    return 0


def _cmd_xaman_audit_idempotency_spec_report(args) -> int:
    """Render Phase 64 audit/idempotency design-spec markdown report."""
    from sonic_xrpl.xaman_audit_idempotency_spec.reporting import render_xaman_audit_idempotency_spec_markdown

    print(render_xaman_audit_idempotency_spec_markdown(_phase64_xaman_audit_idempotency_spec(args)))
    return 0


def _cmd_signal_review(args) -> int:
    """Run Phase 50 signal review from Phase 49 fixtures (offline)."""
    from pathlib import Path
    from sonic_xrpl.signals.evidence import load_candidate_rows, evidence_from_rows
    from sonic_xrpl.signals.classifier import classify_candidates
    from sonic_xrpl.review.decision_policy import classify_candidate_for_phase50
    # Attempt to build review items from evidence
    rows = load_candidate_rows(args.fixture)
    evidences = evidence_from_rows(rows)
    # Build Phase 49 signals
    signals = classify_candidates(evidences)

    reviews = []
    papers = []
    intents = []
    for sig in signals:
        review_item, paper_decision, paper_intent = classify_candidate_for_phase50(sig)
        reviews.append(review_item)
        papers.append(paper_decision)
        intents.append(paper_intent)

    # Simple output for users
    print("=== Phase 50 Paper Review: Summary ===")
    print(f"Total candidates: {len(signals)}")
    class_counts = {}
    for r in reviews:
        class_counts[r.classification] = class_counts.get(r.classification, 0) + 1
    print("Classification counts:")
    for k, v in class_counts.items():
        print(f"- {k}: {v}")
    print("Live execution: BLOCKED (paper-only)")
    return 0

def _cmd_signal_review_report(args) -> int:
    """Generate a Phase 50 signal review report from fixture data."""
    from pathlib import Path
    from sonic_xrpl.review.report_writer import write_review_report
    from sonic_xrpl.signals.evidence import load_candidate_rows, evidence_from_rows
    from sonic_xrpl.signals.classifier import classify_candidates
    from sonic_xrpl.review.decision_policy import classify_candidate_for_phase50
    path = Path(args.fixture)
    rows = load_candidate_rows(path)
    evidences = evidence_from_rows(rows)
    signals = classify_candidates(evidences)
    # Minimal output: just build items
    review_items = []
    paper_decisions = []
    paper_intents = []
    for sig in signals:
        ri, pd, pi = classify_candidate_for_phase50(sig)
        review_items.append(ri)
        paper_decisions.append(pd)
        paper_intents.append(pi)
    # Create a small deterministic queue-like object
    from sonic_xrpl.review.models import ReviewQueue
    queue = ReviewQueue(queue_id=signals[0].signal_id if signals else "phase50", items=tuple(review_items), generated_at="1970-01-01T00:00:00+00:00", source_fixture=str(path))
    json_path, md_path = write_review_report(queue, review_items, paper_decisions, paper_intents, Path(args.output_dir))
    print(f"Wrote review JSON: {json_path}")
    print(f"Wrote review Markdown: {md_path}")
    return 0

def _cmd_paper_intents(args) -> int:
    """Generate offline paper intents for Phase 49 signals (no live actions)."""
    from pathlib import Path
    from sonic_xrpl.signals.evidence import load_candidate_rows, evidence_from_rows
    from sonic_xrpl.signals.classifier import classify_candidates
    from sonic_xrpl.review.decision_policy import classify_candidate_for_phase50
    path = Path(args.fixture)
    rows = load_candidate_rows(path)
    evidences = evidence_from_rows(rows)
    signals = classify_candidates(evidences)
    for sig in signals:
        _, _, pi = classify_candidate_for_phase50(sig)
        print(f"PaperIntent: {pi.intent_id} for candidate {sig.candidate_id} side={pi.side}")
    return 0


def _phase51_attributions(args):
    from sonic_xrpl.outcomes.attribution import build_outcome_attributions
    from sonic_xrpl.outcomes.observation import load_outcome_observations
    from sonic_xrpl.signals.firstledger_candidate import generate_firstledger_signals

    signals = generate_firstledger_signals(args.signals_fixture)
    observations = load_outcome_observations(args.outcomes_fixture)
    return build_outcome_attributions(signals, observations)


def _cmd_paper_outcomes(args) -> int:
    """Attribute paper outcomes to Phase 49 signal records."""
    attributions = _phase51_attributions(args)
    print("=== Phase 51 Paper Outcomes ===")
    print("  Offline/read-only: yes")
    print("  Live execution    : BLOCKED")
    print(f"  Attributions     : {len(attributions)}")
    for item in attributions:
        print(
            f"  - {item.candidate_id}: {item.signal_type} -> {item.outcome_label.value} "
            f"return_bps={item.observed_return_bps} window={item.window}"
        )
        print("    live_execution_allowed=False")
    return 0


def _cmd_paper_outcome_report(args) -> int:
    """Write Phase 51 paper outcome attribution reports."""
    from sonic_xrpl.outcomes.report_writer import write_outcome_report

    attributions = _phase51_attributions(args)
    json_path, md_path = write_outcome_report(attributions, args.output_dir)
    print("=== Phase 51 Paper Outcome Report ===")
    print("  Offline/read-only: yes")
    print("  Live execution    : BLOCKED")
    print(f"  JSON report      : {json_path}")
    print(f"  Summary          : {md_path}")
    return 0


def _cmd_signal_feedback_report(args) -> int:
    """Write Phase 51 paper-only signal feedback reports."""
    from sonic_xrpl.outcomes.feedback import build_signal_feedback
    from sonic_xrpl.outcomes.report_writer import write_feedback_report

    attributions = _phase51_attributions(args)
    feedback = build_signal_feedback(attributions)
    json_path, md_path = write_feedback_report(feedback, args.output_dir)
    print("=== Phase 51 Signal Feedback Report ===")
    print("  Offline/read-only: yes")
    print("  Live execution    : BLOCKED")
    print(f"  Total attributed : {feedback.total_attributed}")
    print(f"  JSON report      : {json_path}")
    print(f"  Summary          : {md_path}")
    return 0


def _phase52_corpus(args):
    from sonic_xrpl.outcome_corpus.builder import build_outcome_corpus

    return build_outcome_corpus(list(args.fixture))


def _cmd_outcome_corpus(args) -> int:
    """Build and summarize a Phase 52 paper observation corpus."""
    corpus = _phase52_corpus(args)
    print("=== Phase 52 Outcome Corpus ===")
    print("  Paper-only       : True")
    print("  Offline          : True")
    print("  Live execution    : BLOCKED")
    print(f"  Corpus ID        : {corpus.corpus_id}")
    print(f"  Replay cases     : {corpus.total_cases}")
    print(f"  Source-backed    : {corpus.source_backed_cases}")
    print(f"  Synthetic        : {corpus.synthetic_cases}")
    print(f"  Quality grade    : {corpus.quality_summary.quality_grade}")
    for case in corpus.replay_cases:
        print(
            f"  - {case.candidate_id}: windows={','.join(case.windows_present) or 'none'} "
            f"missing={','.join(case.windows_missing) or 'none'}"
        )
        print("    live_execution_allowed=False")
    return 0


def _cmd_outcome_corpus_report(args) -> int:
    """Write Phase 52 paper observation corpus reports."""
    from sonic_xrpl.outcome_corpus.report_writer import write_outcome_corpus_report

    corpus = _phase52_corpus(args)
    report = write_outcome_corpus_report(corpus, args.output_dir)
    print("=== Phase 52 Outcome Corpus Report ===")
    print("  Paper-only       : True")
    print("  Offline          : True")
    print("  Live execution    : BLOCKED")
    print(f"  Corpus ID        : {corpus.corpus_id}")
    print(f"  Quality grade    : {corpus.quality_summary.quality_grade}")
    for label, path in report.generated_files.items():
        print(f"  {label}: {path}")
    return 0


def _cmd_outcome_corpus_quality(args) -> int:
    """Print Phase 52 paper observation corpus quality."""
    corpus = _phase52_corpus(args)
    quality = corpus.quality_summary
    print("=== Phase 52 Outcome Corpus Quality ===")
    print("  Paper-only       : True")
    print("  Offline          : True")
    print("  Live execution    : BLOCKED")
    print(f"  Quality grade    : {quality.quality_grade}")
    print(f"  Total cases      : {quality.total_cases}")
    print(f"  Complete cases   : {quality.complete_cases}")
    print(f"  Partial cases    : {quality.partial_cases}")
    print(f"  Missing cases    : {quality.missing_observation_cases}")
    print(f"  Recommendation   : {quality.recommendation}")
    if quality.limitation_counts:
        print("  Limitation counts:")
        for limitation, count in quality.limitation_counts.items():
            print(f"    - {limitation}: {count}")
    return 0


def _phase53_review(args):
    from sonic_xrpl.calibration_review.loader import load_evidence_snapshot
    from sonic_xrpl.calibration_review.readiness import evaluate_readiness
    from sonic_xrpl.calibration_review.recommendations import build_threshold_recommendations

    snapshot = load_evidence_snapshot(args.fixture)
    result = evaluate_readiness(snapshot)
    recommendations = build_threshold_recommendations(result)
    return result, recommendations


def _cmd_calibration_readiness(args) -> int:
    """Run Phase 53 calibration readiness review."""
    result, recommendations = _phase53_review(args)
    snapshot = result.evidence_snapshot
    print("=== Phase 53 Calibration Readiness ===")
    print("  Paper-only        : True")
    print("  Offline           : True")
    print("  Live execution    : BLOCKED")
    print("  Runtime mutation  : BLOCKED")
    print(f"  Readiness status  : {result.status}")
    print(f"  Confidence        : {result.confidence}")
    print(f"  Recommendations   : {len(recommendations)}")
    print(f"  Corpus cases      : {snapshot.corpus_case_count}")
    print(f"  Source-backed     : {snapshot.source_backed_case_count}")
    print(f"  Synthetic         : {snapshot.synthetic_case_count}")
    if result.blockers:
        print("  Blockers:")
        for blocker in result.blockers:
            print(f"    - {blocker}")
    if result.warnings:
        print("  Warnings:")
        for warning in result.warnings:
            print(f"    - {warning}")
    return 0


def _cmd_calibration_readiness_report(args) -> int:
    """Write Phase 53 calibration readiness reports."""
    from sonic_xrpl.calibration_review.report_writer import write_calibration_review_report

    result, recommendations = _phase53_review(args)
    report = write_calibration_review_report(result, recommendations, args.output_dir)
    print("=== Phase 53 Calibration Readiness Report ===")
    print("  Paper-only        : True")
    print("  Offline           : True")
    print("  Live execution    : BLOCKED")
    print("  Runtime mutation  : BLOCKED")
    print(f"  Readiness status  : {result.status}")
    for label, path in report.generated_files.items():
        print(f"  {label}: {path}")
    return 0


def _cmd_calibration_recommendations(args) -> int:
    """Print Phase 53 advisory threshold recommendations."""
    result, recommendations = _phase53_review(args)
    print("=== Phase 53 Calibration Recommendations ===")
    print("  Paper-only        : True")
    print("  Offline           : True")
    print("  Live execution    : BLOCKED")
    print("  Runtime mutation  : BLOCKED")
    print("  Advisory only     : True")
    print("  Human review      : REQUIRED")
    print(f"  Readiness status  : {result.status}")
    for item in recommendations:
        print(
            f"  - {item.target}: {item.direction} confidence={item.confidence} "
            f"non_mutating={item.non_mutating} human_review={item.requires_human_review}"
        )
    return 0


def _phase54_pack(args):
    from sonic_xrpl.calibration_proposal import build_calibration_proposal_pack

    return build_calibration_proposal_pack(args.fixture)


def _cmd_calibration_proposals(args) -> int:
    """Build Phase 54 human-reviewed calibration proposals."""
    pack = _phase54_pack(args)
    print("=== Phase 54 Calibration Proposals ===")
    print("  Paper-only calibration proposals: True")
    print("  Human review required          : True")
    print("  No settings were changed       : True")
    print("  Live execution is blocked      : True")
    print(f"  Pack ID                        : {pack.pack_id}")
    print(f"  Exact proposals                : {len(pack.proposals)}")
    print(f"  Blocked recommendations        : {len(pack.blocked_recommendations)}")
    print(f"  Risk level                     : {pack.risk_summary.risk_level}")
    for proposal in pack.proposals:
        print(
            f"  - {proposal.parameter_ref.name}: {proposal.current_value} -> {proposal.proposed_value} "
            f"({proposal.direction}, proposed only)"
        )
    for blocked in pack.blocked_recommendations:
        print(f"  - blocked {blocked.recommendation_id}: {blocked.reason}")
    return 0


def _cmd_calibration_proposal_report(args) -> int:
    """Write Phase 54 calibration proposal reports."""
    from sonic_xrpl.calibration_proposal import write_calibration_proposal_report

    pack = _phase54_pack(args)
    generated = write_calibration_proposal_report(pack, args.output_dir)
    print("=== Phase 54 Calibration Proposal Report ===")
    print("  Paper-only calibration proposals: True")
    print("  Human review required          : True")
    print("  No settings were changed       : True")
    print("  Live execution is blocked      : True")
    print(f"  Pack ID                        : {pack.pack_id}")
    for label, path in generated.items():
        print(f"  {label}: {path}")
    return 0


def _cmd_calibration_proposal_diff(args) -> int:
    """Print Phase 54 calibration proposal diff."""
    from sonic_xrpl.calibration_proposal import render_proposal_diff

    pack = _phase54_pack(args)
    print(render_proposal_diff(pack))
    return 0


def _phase55_ledger(args):
    from sonic_xrpl.calibration_approval import build_approval_ledger

    return build_approval_ledger(args.proposal_fixture, args.review_fixture)


def _cmd_calibration_approval_ledger(args) -> int:
    """Build Phase 55 approval ledger."""
    ledger = _phase55_ledger(args)
    print("=== Phase 55 Calibration Approval Ledger ===")
    print("  Phase 55 approval ledger is offline, paper-only, and non-mutating.")
    print("  No calibration changes are applied.")
    print("  Live execution remains blocked.")
    print(f"  Ledger ID        : {ledger.ledger_id}")
    print(f"  Records          : {len(ledger.records)}")
    print(f"  Change requests  : {len(ledger.change_requests)}")
    print(f"  Approved         : {ledger.approved_count}")
    print(f"  Blocked          : {ledger.blocked_count}")
    print(f"  Invalid          : {ledger.invalid_count}")
    for decision, count in ledger.counts_by_decision.items():
        print(f"  - {decision}: {count}")
    return 0


def _cmd_calibration_change_requests(args) -> int:
    """Print Phase 55 change request artifacts."""
    ledger = _phase55_ledger(args)
    print("=== Phase 55 Calibration Change Requests ===")
    print("  Change requests are review artifacts only.")
    print("  apply_allowed=False")
    print("  runtime_mutation_allowed=False")
    print("  Live execution remains blocked.")
    if not ledger.change_requests:
        print("  No change requests generated.")
    for item in ledger.change_requests:
        print(
            f"  - {item.change_request_id}: {item.proposal_id} "
            f"{item.before_value} -> {item.after_value} delta={item.delta:+.2f} status={item.status}"
        )
    return 0


def _cmd_calibration_approval_report(args) -> int:
    """Write Phase 55 approval ledger reports."""
    from sonic_xrpl.calibration_approval import write_approval_reports

    ledger = _phase55_ledger(args)
    generated = write_approval_reports(ledger, args.proposal_fixture, args.review_fixture, args.output_dir)
    print("=== Phase 55 Calibration Approval Report ===")
    print("  Phase 55 approval ledger is offline, paper-only, and non-mutating.")
    print("  No calibration changes are applied.")
    print("  Live execution remains blocked.")
    print(f"  Ledger ID        : {ledger.ledger_id}")
    for label, path in generated.items():
        print(f"  {label}: {path}")
    return 0


def _phase56_plan(args):
    from sonic_xrpl.calibration_implementation_plan import build_calibration_implementation_plan

    return build_calibration_implementation_plan(args.approval_ledger, args.change_requests)


def _cmd_calibration_implementation_plan(args) -> int:
    """Build Phase 56 implementation plan."""
    plan = _phase56_plan(args)
    print("=== Phase 56 Calibration Implementation Plan ===")
    print("  Planning only      : True")
    print("  Dry run only       : True")
    print("  Runtime mutation   : BLOCKED")
    print("  Live execution     : BLOCKED")
    print(f"  Plan ID            : {plan.plan_id}")
    print(f"  Source ledger      : {plan.source_ledger_id}")
    print(f"  Source requests    : {plan.source_change_request_count}")
    print(f"  Implementation items: {len(plan.implementation_items)}")
    print(f"  Blocked items      : {len(plan.blocked_items)}")
    for item in plan.implementation_items:
        print(
            f"  - {item.implementation_item_id}: {item.target_namespace}.{item.target_parameter} "
            f"{item.current_value:.2f} -> {item.proposed_value:.2f} delta={item.exact_delta:+.2f}"
        )
    for blocked in plan.blocked_items:
        print(f"  - BLOCKED {blocked.change_request_id}: {blocked.reason}")
    return 0


def _cmd_calibration_implementation_dry_run(args) -> int:
    """Render Phase 56 dry-run implementation preview."""
    from sonic_xrpl.calibration_implementation_plan import render_dry_run_preview

    plan = _phase56_plan(args)
    print(render_dry_run_preview(plan.implementation_items))
    return 0


def _cmd_calibration_implementation_report(args) -> int:
    """Write Phase 56 implementation plan and dry-run reports."""
    from sonic_xrpl.calibration_implementation_plan import write_implementation_reports

    plan = _phase56_plan(args)
    generated = write_implementation_reports(plan, args.approval_ledger, args.change_requests, args.output_dir)
    print("=== Phase 56 Calibration Implementation Report ===")
    print("  Planning only      : True")
    print("  Dry run only       : True")
    print("  Runtime mutation   : BLOCKED")
    print("  Live execution     : BLOCKED")
    print(f"  Plan ID            : {plan.plan_id}")
    for label, path in generated.items():
        print(f"  {label}: {path}")
    return 0


def _cmd_runtime_profile(args) -> int:
    """Show Phase 57 consolidated runtime profile."""
    from sonic_xrpl.runtime_profile.models import jsonable
    from sonic_xrpl.runtime_profile.profiles import build_runtime_profile_snapshot

    profile = build_runtime_profile_snapshot()
    if getattr(args, "json", False):
        import json

        print(json.dumps(jsonable(profile), indent=2, sort_keys=True))
        return 0
    print("=== Phase 57 Runtime Profile ===")
    print(f"  Profile            : {profile.profile_name}")
    print(f"  Profile ID         : {profile.profile_id}")
    print(f"  Paper-only         : {profile.paper_only}")
    print(f"  Dry-run            : {profile.dry_run}")
    print(f"  Execution enabled  : {profile.execution_enabled}")
    print(f"  Live execution     : {'ALLOWED' if profile.live_execution_allowed else 'BLOCKED'}")
    print(f"  Runtime writes     : {profile.runtime_write_policy}")
    if profile.warnings:
        print("  Warnings:")
        for item in profile.warnings:
            print(f"    - {item}")
    if profile.limitations:
        print("  Limitations:")
        for item in profile.limitations:
            print(f"    - {item}")
    return 0


def _cmd_runtime_profile_conformance(args) -> int:
    """Run Phase 57 runtime profile conformance checks."""
    from sonic_xrpl.runtime_profile.conformance import evaluate_runtime_profile_conformance
    from sonic_xrpl.runtime_profile.models import FAIL, jsonable

    report = evaluate_runtime_profile_conformance()
    if getattr(args, "json", False):
        import json

        print(json.dumps(jsonable(report), indent=2, sort_keys=True))
    else:
        print("=== Phase 57 Runtime Profile Conformance ===")
        print(f"  Status             : {report.status}")
        for check in report.checks:
            print(f"  - {check.check_id}: {check.status} ({check.message})")
        if report.blockers:
            print("  Blockers:")
            for item in report.blockers:
                print(f"    - {item}")
        if report.warnings:
            print("  Warnings:")
            for item in report.warnings:
                print(f"    - {item}")
    return 1 if report.status == FAIL else 0


def _cmd_runtime_profile_report(args) -> int:
    """Write Phase 57 runtime profile and conformance reports."""
    from sonic_xrpl.runtime_profile.report_writer import write_runtime_profile_reports

    generated = write_runtime_profile_reports(args.output_dir)
    print("=== Phase 57 Runtime Profile Report ===")
    print("  Paper-only         : True")
    print("  Runtime mutation   : BLOCKED")
    print("  Live execution     : BLOCKED")
    for label, path in generated.items():
        print(f"  {label}: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

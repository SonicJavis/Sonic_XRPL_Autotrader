from __future__ import annotations

import streamlit as st
from sqlmodel import Session, select

from app.alpha.performance_engine import PerformanceEngine
from app.calibration.fundedness_proxy import FundednessProxy
from app.calibration.regime_classifier import RegimeClassificationInput, XRPLRegimeClassifier
from app.calibration.recommendation_engine import CalibrationErrorSample, ConfidenceWeightedCalibrationEngine
from app.calibration.temporal_comparison import compare_simulation_vs_sequence
from app.config import Settings
from app.db.models import (
    AlphaSignal,
    ExecutionFillSlice,
    ExecutionRecord,
    MarketDepthLevel,
    MarketSnapshot,
    PaperTrade,
    PaperTradeOutcome,
    Position,
    PositionExitFill,
    RiskDecisionRecord,
    RiskEvent,
    Signal,
    WatchedToken,
    XRPLOrderbookSequence,
    XRPLOrderbookSnapshot,
)
from app.db.session import engine, init_db
from app.execution.pnl_attribution_engine import PnLAttributionEngine
from app.execution.replay_engine import ReplayEngine
from app.risk.kill_switch import KillSwitch


def main() -> None:
    settings = Settings()
    init_db()

    st.set_page_config(page_title="Sonic XRPL Autotrader", page_icon="S", layout="wide")
    st.title("Sonic XRPL Autotrader Dashboard")
    st.caption("Paper/scanner visibility dashboard. Live trading controls are intentionally disabled.")

    kill_switch = KillSwitch()

    col1, col2, col3 = st.columns(3)
    col1.metric("Bot Mode", str(settings.BOT_MODE))
    col2.metric("Live Trading", "ENABLED" if settings.LIVE_TRADING_ENABLED else "DISABLED")
    col3.metric("Kill Switch", "ENGAGED" if kill_switch.is_engaged() else "OFF")

    with Session(engine) as session:
        tokens = session.exec(select(WatchedToken).order_by(WatchedToken.id.desc()).limit(50)).all()
        snapshots = session.exec(select(MarketSnapshot).order_by(MarketSnapshot.id.desc()).limit(100)).all()
        depth_levels = session.exec(select(MarketDepthLevel).order_by(MarketDepthLevel.id.desc()).limit(200)).all()
        signals = session.exec(select(Signal).order_by(Signal.id.desc()).limit(50)).all()
        alpha_signals = session.exec(select(AlphaSignal).order_by(AlphaSignal.id.desc()).limit(50)).all()
        outcomes = session.exec(select(PaperTradeOutcome).order_by(PaperTradeOutcome.id.desc()).limit(200)).all()
        positions = session.exec(select(Position).order_by(Position.entry_time.desc()).limit(200)).all()
        executions = session.exec(select(ExecutionRecord).order_by(ExecutionRecord.id.desc()).limit(300)).all()
        orderbook_sequences = session.exec(select(XRPLOrderbookSequence).order_by(XRPLOrderbookSequence.id.desc()).limit(300)).all()
        orderbook_snapshots = session.exec(select(XRPLOrderbookSnapshot).order_by(XRPLOrderbookSnapshot.id.desc()).limit(1200)).all()
        fill_slices = session.exec(select(ExecutionFillSlice).order_by(ExecutionFillSlice.id.desc()).limit(800)).all()
        exit_fills = session.exec(select(PositionExitFill).order_by(PositionExitFill.id.desc()).limit(300)).all()
        trades = session.exec(select(PaperTrade).order_by(PaperTrade.id.desc()).limit(50)).all()
        risk_decisions = session.exec(select(RiskDecisionRecord).order_by(RiskDecisionRecord.id.desc()).limit(50)).all()
        risk_events = session.exec(select(RiskEvent).order_by(RiskEvent.id.desc()).limit(50)).all()
        perf_engine = PerformanceEngine(settings)
        perf_summary = perf_engine.summary(session)
        alpha_breakdown = perf_engine.alpha_breakdown(session)
        pnl_engine = PnLAttributionEngine()
        realized = pnl_engine.realized_pnl_summary(session)
        unrealized = pnl_engine.unrealized_pnl_summary(
            session,
            execution_latency_ms=settings.EXECUTION_LATENCY_MS,
            max_snapshot_age_ms=settings.MAX_SNAPSHOT_AGE_MS,
            liquidity_haircut_pct=settings.EXECUTION_LIQUIDITY_HAIRCUT_PCT,
            snapshot_to_decision_ms=settings.SNAPSHOT_TO_DECISION_MS,
            decision_to_submission_ms=settings.DECISION_TO_SUBMISSION_MS,
            submission_to_inclusion_ms=settings.SUBMISSION_TO_INCLUSION_MS,
            latency_haircut_pct=settings.EXECUTION_LATENCY_HAIRCUT_PCT,
            contention_haircut_pct=settings.EXECUTION_CONTENTION_HAIRCUT_PCT,
            trustline_liquidity_discount_pct=settings.EXECUTION_TRUSTLINE_DISCOUNT_PCT,
            ledger_drift_pct=settings.EXECUTION_LEDGER_DRIFT_PCT,
            execution_window_snapshots=settings.EXECUTION_WINDOW_SNAPSHOTS,
        )
        failures = pnl_engine.list_failures(session, limit=300)
        replay_engine = ReplayEngine()
        replay_samples = [replay_engine.replay_execution(session, row.id) for row in executions[:80] if row.id is not None]

    realized_pnl = float(realized.get("realized_pnl_xrp", 0.0))
    unrealized_pnl_raw = unrealized.get("unrealized_pnl_xrp")
    unrealized_label = "n/a" if unrealized_pnl_raw is None else f"{float(unrealized_pnl_raw):.4f}"
    total_exec = len(executions)
    partial_exec = sum(1 for row in executions if row.fill_status == "PARTIAL")
    failed_exec = sum(1 for row in executions if row.failure_reason is not None or row.fill_status == "UNFILLED")
    requested_sum = sum(float(row.requested_size or 0.0) for row in executions)
    filled_sum = sum(float(row.filled_size or 0.0) for row in executions)
    fill_efficiency = 0.0 if requested_sum <= 0 else (filled_sum / requested_sum)

    q1, q2, q3, q4 = st.columns(4)
    q1.metric("Failure Rate", f"{(failed_exec / max(1, total_exec)) * 100:.1f}%")
    q2.metric("Partial Fill Rate", f"{(partial_exec / max(1, total_exec)) * 100:.1f}%")
    q3.metric("Fill Efficiency", f"{fill_efficiency * 100:.1f}%")
    q4.metric("Failure Count", str(len(failures)))

    h1, h2, h3 = st.columns(3)
    h1.metric("Realized PnL (XRP)", f"{realized_pnl:.4f}")
    h2.metric("Unrealized PnL (XRP)", unrealized_label)
    exit_success = sum(1 for row in positions if row.status == "CLOSED")
    h3.metric("Exit Success Rate", f"{(exit_success / max(1, len(positions))) * 100:.1f}%")

    snapshots_by_token: dict[int, list[XRPLOrderbookSnapshot]] = {}
    for snap in orderbook_snapshots:
        snapshots_by_token.setdefault(int(snap.token_id), []).append(snap)
    for token_snaps in snapshots_by_token.values():
        token_snaps.sort(key=lambda s: int(s.ledger_index))

    calibration_samples: list[CalibrationErrorSample] = []
    execution_survival: list[float] = []
    classified_regimes: list[str] = []
    classified_confidences: list[float] = []
    xrpl_flag_counts: dict[str, int] = {
        "possible_unfunded_liquidity": 0,
        "pathfinding_risk": 0,
        "inclusion_uncertainty": 0,
        "depth_illusion_risk": 0,
    }
    regime_classifier = XRPLRegimeClassifier()
    for row in executions:
        token_snaps = snapshots_by_token.get(int(row.token_id), [])
        lower = min(int(row.ledger_index_snapshot), int(row.ledger_index_inclusion))
        upper = max(int(row.ledger_index_snapshot), int(row.ledger_index_inclusion))
        sequence = [s for s in token_snaps if lower <= int(s.ledger_index) <= upper][:64]
        compared = compare_simulation_vs_sequence(execution=row, sequence=sequence)
        calibration_samples.append(
            CalibrationErrorSample(
                execution_survivability_error=compared.execution_survivability_error,
                slippage_underestimation=compared.slippage_underestimation,
                depth_overestimation=compared.depth_overestimation,
                latency_miss_error=compared.latency_miss_error,
            )
        )

        avg_depth = (
            sum((float(s.bid_depth_xrp) + float(s.ask_depth_xrp)) for s in sequence) / max(1, len(sequence))
            if sequence
            else 0.0
        )
        visible_depth_score = max(0.0, min(1.0, avg_depth / 1200.0))
        token_sequences = [seq for seq in orderbook_sequences if int(seq.token_id) == int(row.token_id)]
        token_volatility = (
            sum(float(seq.volatility_score) for seq in token_sequences) / max(1, len(token_sequences))
            if token_sequences
            else 1.0
        )
        token_decay = (
            sum(float(seq.decay_score) for seq in token_sequences) / max(1, len(token_sequences))
            if token_sequences
            else 1.0
        )
        classified = regime_classifier.classify(
            metrics=RegimeClassificationInput(
                visible_depth_score=visible_depth_score,
                execution_survivability_error=compared.execution_survivability_error,
                slippage_underestimation=compared.slippage_underestimation,
                depth_overestimation=compared.depth_overestimation,
                volatility_score=token_volatility,
                decay_score=token_decay,
                wall_flicker_rate=0.0,
                inclusion_uncertainty=max(0.0, min(1.0, compared.latency_miss_error)),
            )
        )
        classified_regimes.append(classified.regime)
        classified_confidences.append(classified.confidence)
        for flag_name, flag_enabled in classified.xrpl_flags.items():
            if flag_enabled:
                xrpl_flag_counts[flag_name] = xrpl_flag_counts.get(flag_name, 0) + 1

        execution_survival.append(max(0.0, min(1.0, 1.0 - compared.execution_survivability_error)))

    fail_in_real_rate = 0.0
    if calibration_samples:
        fail_in_real_rate = (
            sum(1 for s in calibration_samples if s.execution_survivability_error >= 0.25) / len(calibration_samples)
        )

    if executions:
        sample_snapshots = orderbook_snapshots[: min(200, len(orderbook_snapshots))]
        fundedness = FundednessProxy().evaluate(sample_snapshots).fundedness_confidence
    else:
        fundedness = 0.0

    avg_volatility = (
        sum(float(seq.volatility_score) for seq in orderbook_sequences) / len(orderbook_sequences)
        if orderbook_sequences
        else 1.0
    )
    sequence_stability = max(0.0, min(1.0, 1.0 - avg_volatility))

    dominant_regime = "UNKNOWN"
    if classified_regimes:
        dominant_regime = max(set(classified_regimes), key=classified_regimes.count)
    avg_confidence = 0.0 if not classified_confidences else (sum(classified_confidences) / len(classified_confidences))
    severity = "HIGH"
    if fail_in_real_rate >= 0.70:
        severity = "CRITICAL"
    elif fail_in_real_rate < 0.40:
        severity = "MEDIUM"

    recommendation = ConfidenceWeightedCalibrationEngine().recommend(
        samples=calibration_samples,
        fundedness_confidence=fundedness,
        sequence_stability=sequence_stability,
        confidence_floor_threshold=0.45,
        regime=dominant_regime,
        xrpl_risk_flags={k: (v > 0) for k, v in xrpl_flag_counts.items()},
        inclusion_uncertainty=min(1.0, max(0.0, 1.0 - avg_confidence)),
    )

    st.subheader("Simulator vs Reality")
    st.warning("ORDERBOOK MAY NOT BE FUNDED")
    st.warning("DEPTH MAY BE NON-EXECUTABLE")
    st.warning("XRPL PATHFINDING MAY DISTORT FILLS")

    s1, s2, s3 = st.columns(3)
    s1.metric("Simulated Trades Likely To Fail (%)", f"{fail_in_real_rate * 100:.1f}%")
    s2.metric(
        "Avg Survivability Error",
        f"{(sum(s.execution_survivability_error for s in calibration_samples) / max(1, len(calibration_samples))):.3f}",
    )
    s3.metric(
        "Avg Slippage Underestimation",
        f"{(sum(s.slippage_underestimation for s in calibration_samples) / max(1, len(calibration_samples))):.3f}",
    )
    s4, s5, s6 = st.columns(3)
    s4.metric("Regime", dominant_regime)
    s5.metric("Severity", severity)
    s6.metric("Confidence", f"{avg_confidence:.3f}")
    st.caption(
        "XRPL risk flags: " + ", ".join(f"{k}={v}" for k, v in sorted(xrpl_flag_counts.items(), key=lambda it: it[0]))
    )

    st.subheader("Liquidity Decay Heatmap")
    heat_bins: dict[str, int] = {}
    for seq in orderbook_sequences:
        decay_bucket = min(4, int(float(seq.decay_score) * 5.0))
        vol_bucket = min(4, int(float(seq.volatility_score) * 5.0))
        key = f"d{decay_bucket}-v{vol_bucket}"
        heat_bins[key] = heat_bins.get(key, 0) + 1
    heat_rows = [{"bucket": k, "count": v} for k, v in sorted(heat_bins.items(), key=lambda it: it[0])]
    if heat_rows:
        st.bar_chart(heat_rows, x="bucket", y="count", use_container_width=True)
    else:
        st.info("No sequence data available yet.")

    st.subheader("Execution Survival Rate")
    if execution_survival:
        st.metric("Average Survival Rate", f"{(sum(execution_survival) / len(execution_survival)) * 100:.1f}%")
        survival_series = [{"idx": idx, "survival": val} for idx, val in enumerate(reversed(execution_survival), start=1)]
        st.line_chart(survival_series, x="idx", y="survival", use_container_width=True)
    else:
        st.metric("Average Survival Rate", "0.0%")

    st.subheader("Calibration Confidence")
    if recommendation is None:
        st.metric("Confidence Score", "LOW")
        st.caption("Insufficient evidence for a safe conservative recommendation.")
    else:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Confidence Score", f"{recommendation.confidence_score:.3f}")
        c2.metric("Queue Haircut %", f"{recommendation.queue_haircut_pct * 100:.1f}%")
        c3.metric("Drift Haircut %", f"{recommendation.drift_haircut_pct * 100:.1f}%")
        c4.metric("Latency ms", str(recommendation.latency_ms))
        st.caption(recommendation.reasoning)

    st.subheader("Registered Tokens")
    st.dataframe([t.model_dump() for t in tokens], use_container_width=True)

    st.subheader("Market Snapshots")
    snapshot_rows = [s.model_dump() for s in snapshots]
    st.dataframe(snapshot_rows, use_container_width=True)

    if snapshot_rows:
        latest = snapshot_rows[0]
        spread_val = latest.get("spread_pct")
        good_structure = spread_val is not None and spread_val <= settings.MAX_SPREAD_PCT and latest.get(
            "liquidity_xrp", 0
        ) >= settings.MIN_LIQUIDITY_XRP and latest.get("bid_count", 0) >= 2 and latest.get("ask_count", 0) >= 2
        style = "green" if good_structure else "red"
        label = "GOOD STRUCTURE" if good_structure else "BAD TOKEN STRUCTURE"
        st.markdown(f"<h4 style='color:{style}'>{label}</h4>", unsafe_allow_html=True)

        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Price (XRP)", "n/a" if latest.get("price_xrp") is None else f"{latest.get('price_xrp', 0):.6f}")
        m2.metric("Spread %", "n/a" if spread_val is None else f"{spread_val:.3f}")
        m3.metric("Liquidity (XRP)", f"{latest.get('liquidity_xrp', 0):.2f}")
        best_bid = latest.get("best_bid")
        best_ask = latest.get("best_ask")
        m4.metric(
            "Best Bid / Ask",
            f"{best_bid:.6f} / {best_ask:.6f}" if best_bid is not None and best_ask is not None else "n/a",
        )
        m5.metric("Order Count", str(latest.get("tx_count", 0)))

        b1, b2 = st.columns(2)
        b1.metric("Liquidity Bid (XRP)", f"{latest.get('liquidity_bid_xrp', 0):.2f}")
        b2.metric("Liquidity Ask (XRP)", f"{latest.get('liquidity_ask_xrp', 0):.2f}")

    st.subheader("Latest Signals")
    st.dataframe([s.model_dump() for s in signals], use_container_width=True)

    st.subheader("Alpha Signals")
    alpha_rows = [s.model_dump() for s in alpha_signals]
    st.dataframe(alpha_rows, use_container_width=True)
    if alpha_rows:
        approved = sum(1 for row in alpha_rows if row.get("decision") == "APPROVE")
        rejected = sum(1 for row in alpha_rows if row.get("decision") == "REJECT")
        avg_score = sum(float(row.get("score", 0.0)) for row in alpha_rows) / max(1, len(alpha_rows))
        a1, a2, a3 = st.columns(3)
        a1.metric("Avg Alpha Score", f"{avg_score:.3f}")
        a2.metric("Approved", str(approved))
        a3.metric("Rejected", str(rejected))

    st.subheader("Depth Levels")
    st.dataframe([row.model_dump() for row in depth_levels], use_container_width=True)

    st.subheader("Paper Trades")
    st.dataframe([t.model_dump() for t in trades], use_container_width=True)

    st.subheader("Execution Failures (Priority View)")
    failed_outcomes = [
        {
            "signal_id": row.signal_id,
            "fill_status": row.fill_status,
            "failure_reason": row.failure_reason,
            "reason_closed": row.reason_closed,
            "entry_time": row.entry_time,
            "exit_time": row.exit_time,
        }
        for row in outcomes
        if (row.failure_reason is not None or row.fill_status == "UNFILLED")
    ]
    st.dataframe(failed_outcomes, use_container_width=True)

    st.subheader("Execution Inclusion Overview (Simulated/Paper)")
    status_counts: dict[str, int] = {}
    delays: list[int] = []
    for row in executions:
        status = str(row.inclusion_status or "INCLUDED")
        status_counts[status] = status_counts.get(status, 0) + 1
        delays.append(int(row.inclusion_delay_ledgers or 0))
    i1, i2, i3 = st.columns(3)
    i1.metric("Included", str(status_counts.get("INCLUDED", 0)))
    i2.metric("Delayed", str(status_counts.get("DELAYED", 0)))
    i3.metric("Failed Inclusion", str(status_counts.get("FAILED_INCLUSION", 0)))
    st.caption("Ledger delay distribution (simulated)")
    st.bar_chart([{"delay_ledgers": d} for d in delays], x="delay_ledgers", y="delay_ledgers", use_container_width=True)

    st.subheader("Paper Performance Attribution")
    p1, p2, p3, p4 = st.columns(4)
    p1.metric("Win Rate", f"{float(perf_summary.get('win_rate', 0.0)) * 100:.1f}%")
    p2.metric("Avg PnL (XRP)", f"{float(perf_summary.get('avg_pnl', 0.0)):.4f}")
    p3.metric("Fill Rate", f"{float(perf_summary.get('fill_rate', 0.0)) * 100:.1f}%")
    p4.metric("Avg Slippage Error", f"{float(perf_summary.get('avg_slippage_error', 0.0)):.3f}%")

    outcome_rows = [
        {
            "signal_id": row.signal_id,
            "expected_slippage_pct": row.expected_slippage_pct,
            "actual_slippage_pct": row.actual_slippage_pct,
            "pnl_xrp": row.pnl_xrp,
            "fill_pct": 0.0 if row.target_size_xrp <= 0 else (row.filled_size_xrp / row.target_size_xrp) * 100.0,
            "entry_time": row.entry_time,
            "exit_time": row.exit_time,
            "reason_closed": row.reason_closed,
        }
        for row in outcomes
    ]
    st.caption("All outcomes (realized and unresolved are not mixed into one aggregate)")
    st.dataframe(outcome_rows, use_container_width=True)

    st.subheader("Positions (Strict Attribution)")
    st.dataframe([p.model_dump() for p in positions], use_container_width=True)

    st.subheader("Execution Records")
    execution_rows = []
    for row in executions:
        execution_rows.append(
            {
                "id": row.id,
                "position_id": row.position_id,
                "side": row.side,
                "requested_size": row.requested_size,
                "filled_size": row.filled_size,
                "fill_status": row.fill_status,
                "avg_fill_price": row.avg_fill_price,
                "slippage_vs_top": row.slippage_vs_top,
                "failure_reason": row.failure_reason,
                "snapshot_age_ms": row.snapshot_age_ms,
                "execution_latency_ms": row.execution_latency_ms,
                "execution_time": row.execution_time,
            }
        )
    st.dataframe(execution_rows, use_container_width=True)

    st.subheader("Latency Degradation Metrics (Simulated/Paper)")
    if executions:
        avg_s2d = sum(float(r.snapshot_to_decision_ms or 0.0) for r in executions) / len(executions)
        avg_d2s = sum(float(r.decision_to_submission_ms or 0.0) for r in executions) / len(executions)
        avg_s2i = sum(float(r.submission_to_inclusion_ms or 0.0) for r in executions) / len(executions)
        avg_total = sum(float(r.total_execution_latency_ms or 0.0) for r in executions) / len(executions)
    else:
        avg_s2d = avg_d2s = avg_s2i = avg_total = 0.0
    l1, l2, l3, l4 = st.columns(4)
    l1.metric("Snapshot->Decision ms", f"{avg_s2d:.1f}")
    l2.metric("Decision->Submission ms", f"{avg_d2s:.1f}")
    l3.metric("Submission->Inclusion ms", f"{avg_s2i:.1f}")
    l4.metric("Total Execution Latency ms", f"{avg_total:.1f}")

    st.subheader("Fill Slices Per Execution")
    slice_rows = [
        {
            "execution_id": s.execution_id,
            "ledger_index": s.ledger_index,
            "fill_status": s.fill_status,
            "requested_size": s.requested_size,
            "filled_size": s.filled_size,
            "avg_price": s.avg_price,
        }
        for s in fill_slices
    ]
    st.dataframe(slice_rows, use_container_width=True)

    st.subheader("Replay Mismatch Alerts")
    replay_alerts = [
        {
            "execution_id": r.get("execution_id"),
            "status": r.get("status"),
            "mismatches": ",".join(r.get("mismatches", [])),
        }
        for r in replay_samples
        if r.get("status") == "REPLAY_MISMATCH"
    ]
    st.dataframe(replay_alerts, use_container_width=True)

    st.subheader("Exit Fill Ledger")
    st.dataframe([row.model_dump() for row in exit_fills], use_container_width=True)

    if outcome_rows:
        chronological = list(reversed(outcome_rows))
        win_rate_series: list[dict[str, float | str]] = []
        slippage_series: list[dict[str, float | str]] = []
        wins = 0
        for idx, row in enumerate(chronological, start=1):
            pnl_value = float(row.get("pnl_xrp") or 0.0)
            if pnl_value > 0:
                wins += 1
            timestamp = str(row.get("entry_time"))
            win_rate_series.append({"t": timestamp, "win_rate": wins / idx})
            slippage_series.append(
                {
                    "t": timestamp,
                    "slippage_error": abs(float(row.get("actual_slippage_pct") or 0.0) - float(row.get("expected_slippage_pct") or 0.0)),
                }
            )

        st.caption("Win rate over time")
        st.line_chart(win_rate_series, x="t", y="win_rate", use_container_width=True)

        st.caption("Slippage accuracy error over time")
        st.line_chart(slippage_series, x="t", y="slippage_error", use_container_width=True)

    component_rows = []
    for name, stats in alpha_breakdown.get("components", {}).items():
        component_rows.append(
            {
                "component": name,
                "samples": stats.get("samples", 0.0),
                "avg_pnl_high": stats.get("avg_pnl_high", 0.0),
                "avg_pnl_low": stats.get("avg_pnl_low", 0.0),
            }
        )

    if component_rows:
        st.caption("Component score vs PnL")
        st.dataframe(component_rows, use_container_width=True)
        st.bar_chart(component_rows, x="component", y=["avg_pnl_high", "avg_pnl_low"], use_container_width=True)

    st.subheader("Risk Decisions")
    st.dataframe([r.model_dump() for r in risk_decisions], use_container_width=True)

    st.subheader("Risk Events")
    st.dataframe([r.model_dump() for r in risk_events], use_container_width=True)


if __name__ == "__main__":
    main()

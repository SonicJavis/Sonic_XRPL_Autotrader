from __future__ import annotations

import json

import streamlit as st
from sqlmodel import Session, select

from app.alpha.performance_engine import PerformanceEngine
from app.calibration.fundedness_proxy import FundednessProxy
from app.calibration.regime_classifier import RegimeClassificationInput, XRPLRegimeClassifier
from app.calibration.recommendation_engine import CalibrationErrorSample, ConfidenceWeightedCalibrationEngine
from app.calibration.temporal_comparison import compare_simulation_vs_sequence
from app.config import Settings
from app.validation.dual_error_engine import DualErrorEngine, DualErrorInput
from app.validation.execution_bounds import ExecutionBoundsInput, ExecutionBoundsModel
from app.validation.xrpl_calibration_review import build_audit_export_bundle, build_review_record, review_to_dict
from app.validation.xrpl_calibration_recommendations import XRPLCalibrationRecommendationEngine
from app.validation.xrpl_order_intents import XRPLIntentSnapshot, build_order_intents, summarize_order_intents
from app.validation.observation_uncertainty import ObservationSample, ObservationUncertaintyModel
from app.validation.report_engine import UncertaintyReportEngine, ValidationSample
from app.db.models import (
    AlphaSignal,
    CalibrationReviewRecord,
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
    ShadowDecisionRecord,
    ShadowValidationRecord,
    Signal,
    WatchedToken,
    XRPLOrderbookSequence,
    XRPLOrderbookSnapshot,
)
from app.db.session import engine, init_db
from app.execution.pnl_attribution_engine import PnLAttributionEngine
from app.execution.replay_engine import ReplayEngine
from app.execution.execution_guard import assert_core_execution_disabled
from app.execution.xrpl_paper_execution import XRPLPaperExecutionEngine, summarize_simulations
from app.calibration.xrpl_bayesian_calibrator import build_xrpl_shadow_calibration_aggregate
from app.calibration.xrpl_memory_model import aggregate_by_issuer, aggregate_by_token, aggregate_global, build_memory_samples
from app.calibration.xrpl_regime_detector import XRPLRegimeDetector
from app.calibration.xrpl_time_execution_model import XRPLTimeExecutionModel, build_time_execution_input_from_shadow_execution
from app.decision.xrpl_trade_gate import XRPLTradeGate
from app.decision.xrpl_memory_weighting import XRPLMemoryWeighting, XRPLMemoryWeightingInput
from app.feedback.feedback_aggregator import DecisionFeedbackAggregator
from app.feedback.shadow_decision_tracker import ShadowDecisionTracker
from app.live.dashboard_metrics import build_live_dashboard_metrics
from app.live.xrpl_live_shadow_pipeline import default_live_drift, default_live_status
from app.live.xrpl_ingestion_models import XRPLIngestionHealth
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
        shadow_decisions = session.exec(
            select(ShadowDecisionRecord)
            .order_by(ShadowDecisionRecord.observed_at.desc(), ShadowDecisionRecord.id.desc())
            .limit(300)
        ).all()
        shadow_validations = session.exec(
            select(ShadowValidationRecord)
            .order_by(ShadowValidationRecord.created_at.desc(), ShadowValidationRecord.id.desc())
            .limit(300)
        ).all()
        calibration_reviews = session.exec(
            select(CalibrationReviewRecord)
            .order_by(CalibrationReviewRecord.reviewed_at.desc(), CalibrationReviewRecord.id.desc())
            .limit(300)
        ).all()
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
    validation_samples: list[ValidationSample] = []
    execution_bounds_rows: list[dict[str, float | int | str]] = []
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

        obs_samples = [
            ObservationSample(
                bid_depth_xrp=float(s.bid_depth_xrp),
                ask_depth_xrp=float(s.ask_depth_xrp),
                spread_pct=float(s.spread_pct),
                best_bid=float(s.best_bid),
                best_ask=float(s.best_ask),
                implied_mid_price=(float(s.best_bid) + float(s.best_ask)) / 2.0,
            )
            for s in sequence
        ]
        observation = ObservationUncertaintyModel().evaluate(obs_samples)

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

        bounds = ExecutionBoundsModel().compute(
            data=ExecutionBoundsInput(
                total_visible_depth_xrp=sum(float(s.ask_depth_xrp) for s in sequence),
                requested_size_xrp=float(row.requested_size or 0.0),
                depth_uncertainty=max(0.0, min(1.0, 1.0 - observation.depth_reliability_score)),
                fundedness_uncertainty=observation.fundedness_uncertainty,
                decay_rate=token_decay,
                regime=classified.regime,
            ),
            simulator_fill_size_xrp=float(row.filled_size or 0.0),
        )

        sim_fill_ratio = (
            0.0
            if float(row.requested_size or 0.0) <= 0
            else min(1.0, float(row.filled_size or 0.0) / float(row.requested_size or 1.0))
        )
        dual = DualErrorEngine().evaluate(
            DualErrorInput(
                simulator_fillable=float(row.filled_size or 0.0) > 0.0,
                simulator_fill_ratio=sim_fill_ratio,
                observed_depth_present=bool(sequence and any(float(s.ask_depth_xrp) > 0 for s in sequence)),
                observation_confidence=observation.observation_confidence,
                observed_fill_probability=bounds.fill_probability_range[1],
            )
        )

        validation_samples.append(
            ValidationSample(
                token_key=f"token:{row.token_id}",
                disagreement_score=dual.disagreement_score,
                false_confidence_flag=dual.false_confidence_flag,
                observation_confidence=observation.observation_confidence,
                simulator_within_bounds=bounds.simulator_within_bounds,
            )
        )

        execution_bounds_rows.append(
            {
                "execution_id": int(row.id or 0),
                "min_fill": round(bounds.min_executable_size, 4),
                "max_fill": round(bounds.max_possible_fill, 4),
                "confidence": round(bounds.confidence, 4),
                "within_bounds": "YES" if bounds.simulator_within_bounds else "NO",
            }
        )

        execution_survival.append(max(0.0, min(1.0, 1.0 - compared.execution_survivability_error)))

    uncertainty_report = UncertaintyReportEngine().build(validation_samples)
    live_dashboard = build_live_dashboard_metrics(executions=executions, orderbook_snapshots=orderbook_snapshots)
    ingestion_health = XRPLIngestionHealth(
        connected=False,
        latest_ledger_index=0,
        latest_validated_ledger_index=0,
        stale_snapshot_count=0,
        rejected_snapshot_count=0,
        reconnect_count=0,
        backoff_seconds=0.0,
        reason=("INGESTION_ENABLED_NOT_STARTED" if settings.XRPL_INGESTION_ENABLED else "INGESTION_DISABLED"),
        ingestion_enabled=settings.XRPL_INGESTION_ENABLED,
        ingestion_mode=settings.XRPL_INGESTION_MODE,
        ingestion_source=settings.XRPL_SHADOW_SOURCE,
    )
    xrpl_shadow_calibration = build_xrpl_shadow_calibration_aggregate(
        executions=executions,
        orderbook_snapshots=orderbook_snapshots,
    )
    decision_feedback = DecisionFeedbackAggregator().aggregate_from_executions(executions)
    shadow_decision_summary = ShadowDecisionTracker().summarize(shadow_decisions)
    validation_count = len(shadow_validations)
    validation_avg_disagreement = (
        0.0 if validation_count == 0 else sum(float(row.disagreement_score or 0.0) for row in shadow_validations) / validation_count
    )
    validation_avg_brier = 0.0 if validation_count == 0 else sum(float(row.brier_score or 0.0) for row in shadow_validations) / validation_count
    validation_overconfidence = (
        0.0 if validation_count == 0 else sum(1 for row in shadow_validations if row.overconfidence_flag) / validation_count
    )
    validation_underconfidence = (
        0.0 if validation_count == 0 else sum(1 for row in shadow_validations if row.underconfidence_flag) / validation_count
    )
    validation_attribution: dict[str, int] = {}
    for row in shadow_validations:
        validation_attribution[row.attribution] = validation_attribution.get(row.attribution, 0) + 1
    calibration_recommendations = [
        rec.to_dict()
        for rec in XRPLCalibrationRecommendationEngine().generate(shadow_validations, min_support=30)
    ]
    intent_snapshots_by_token = {}
    for token_id, rows in snapshots_by_token.items():
        if not rows:
            continue
        token = next((item for item in tokens if item.id == token_id), None)
        intent_snapshots_by_token[token_id] = XRPLIntentSnapshot.from_row(
            rows[-1],
            issuer="" if token is None else token.issuer,
            currency="" if token is None else token.currency,
        )
    simulated_intents = build_order_intents(
        recommendations=calibration_recommendations,
        snapshots_by_token=intent_snapshots_by_token,
        requested_size=100.0,
    )
    simulated_intent_summary = summarize_order_intents(simulated_intents)
    simulation_engine = XRPLPaperExecutionEngine()
    latest_snapshots_by_token = {token_id: rows[-1] for token_id, rows in snapshots_by_token.items() if rows}
    paper_simulations = [
        simulation_engine.simulate(
            intent=intent.to_dict(),
            quality_levels=_dashboard_quality_levels(latest_snapshots_by_token.get(int(intent.to_dict()["token_id"]))),
        ).to_dict()
        for intent in simulated_intents
    ]
    paper_simulation_summary = summarize_simulations(paper_simulations)
    execution_guard_status = assert_core_execution_disabled(settings).to_dict()
    tokens_by_id = {int(token.id): token for token in tokens if token.id is not None}
    memory_samples = build_memory_samples(executions, tokens_by_id=tokens_by_id)
    memory_global = aggregate_global(memory_samples)
    memory_tokens = aggregate_by_token(memory_samples)
    memory_issuers = aggregate_by_issuer(memory_samples)
    regime_detector = XRPLRegimeDetector()
    global_regime = regime_detector.assess(memory_global)
    time_execution_model = XRPLTimeExecutionModel()
    shadow_execution_rows = []
    time_execution_rows = []
    for row in executions:
        try:
            details = json.loads(str(row.execution_details_json or "{}"))
        except json.JSONDecodeError:
            details = {}
        if bool(details.get("shadow")):
            shadow_execution_rows.append(
                {
                    "execution_id": int(row.id or 0),
                    "entry_ledger": int(details.get("entry_ledger", row.ledger_index_snapshot or 0)),
                    "execution_ledger": int(row.ledger_index_execution or 0),
                    "fill_status": row.fill_status,
                    "filled_size": float(row.filled_size or 0.0),
                    "disagreement_score": round(float(details.get("disagreement_score", 0.0)), 4),
                    "path_execution_risk": round(float(details.get("path_execution_risk", 0.0)), 4),
                }
            )
            time_input = build_time_execution_input_from_shadow_execution(row, details)
            time_result = time_execution_model.evaluate(time_input)
            base_probability = max(0.0, min(1.0, float(time_input.base_fill_probability)))
            ev_before_drift = base_probability * (1.0 - max(0.0, float(time_input.slippage_estimate))) - (
                1.0 - base_probability
            )
            time_execution_rows.append(
                {
                    "execution_id": int(row.id or 0),
                    "latency_seconds": time_result.latency_seconds,
                    "ledger_delay": time_result.ledger_delay,
                    "price_drift": time_result.price_drift,
                    "drift_amplified": time_result.drift_amplified,
                    "path_complexity": int(time_input.path_complexity),
                    "liquidity_decay": time_result.liquidity_decay,
                    "effective_fill_probability": time_result.effective_fill_probability,
                    "ev_before_drift": round(ev_before_drift, 6),
                    "drift_adjusted_ev": time_result.drift_adjusted_ev,
                }
            )

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

    st.subheader("Ledger Status")
    ls1, ls2, ls3 = st.columns(3)
    ls1.metric("Latest Ledger", str(live_dashboard.latest_ledger_index))
    ls2.metric("Ledger Gaps", str(live_dashboard.ledger_gap_count))
    ls3.metric("Path Risk", f"{live_dashboard.avg_path_execution_risk:.3f}")

    st.subheader("Snapshot Age / Quality")
    sq1, sq2 = st.columns(2)
    sq1.metric("Snapshot Age ms", str(live_dashboard.snapshot_age_ms))
    sq2.metric("Snapshot Quality", f"{live_dashboard.snapshot_quality_score:.3f}")

    st.subheader("Shadow Executions (Ledger-Based)")
    se1, se2 = st.columns(2)
    se1.metric("Shadow Executions", str(live_dashboard.shadow_execution_count))
    se2.metric("Shadow Fill Rate", f"{live_dashboard.shadow_fill_rate * 100:.1f}%")
    st.dataframe(shadow_execution_rows[:50], use_container_width=True)

    st.subheader("Disagreement Score (Live)")
    st.warning("OBSERVED LIQUIDITY MAY NOT EXECUTE")
    st.warning("SIMULATION MAY BE OVER-OPTIMISTIC")
    st.warning("NO GROUND TRUTH AVAILABLE")
    st.warning("ORDERBOOK IS SNAPSHOT ONLY")
    st.warning("EXECUTION OCCURS AT LEDGER CLOSE")
    st.warning("LIQUIDITY MAY BE UNFUNDED")
    st.warning("PATHFINDING MAY ALTER RESULTS")

    uncertainty_level = "HIGH"
    if uncertainty_report.disagreement_score >= 0.70:
        uncertainty_level = "SEVERE"
    elif uncertainty_report.disagreement_score <= 0.30 and uncertainty_report.observation_confidence_avg >= 0.55:
        uncertainty_level = "MODERATE"

    s1, s2, s3, s4 = st.columns(4)
    s1.metric("Disagreement Score", f"{max(uncertainty_report.disagreement_score, live_dashboard.live_disagreement_score):.3f}")
    s2.metric("Uncertainty Level", uncertainty_level)
    s3.metric("Simulator Within Bounds %", f"{uncertainty_report.simulator_within_bounds_rate * 100:.1f}%")
    s4.metric("Simulated Trades Likely To Fail (%)", f"{fail_in_real_rate * 100:.1f}%")

    s5, s6, s7 = st.columns(3)
    s5.metric("Regime", dominant_regime)
    s6.metric("Severity", severity)
    s7.metric("Observation Confidence", f"{uncertainty_report.observation_confidence_avg:.3f}")
    st.caption(
        "XRPL risk flags: " + ", ".join(f"{k}={v}" for k, v in sorted(xrpl_flag_counts.items(), key=lambda it: it[0]))
    )

    st.subheader("Execution Possibility Range")
    st.dataframe(execution_bounds_rows[:50], use_container_width=True)

    st.subheader("XRPL Warnings")
    st.caption("Observed liquidity remains non-executable observation.")
    st.caption("Shadow execution remains read-only and ledger-aligned.")

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

    st.subheader("XRPL Bayesian Shadow Calibration")
    st.warning("XRPL liquidity remains uncertain")
    st.warning("Observed orderbook data may be stale or unfunded")
    st.warning("Calibration is advisory only")

    lower_bounds = xrpl_shadow_calibration.calibration
    b1, b2, b3, b4, b5 = st.columns(5)
    b1.metric("Liquidity Reliability Lower Bound", f"{lower_bounds.liquidity_reliability.lower_bound:.3f}")
    b2.metric("Path Reliability Lower Bound", f"{lower_bounds.path_reliability.lower_bound:.3f}")
    b3.metric("Latency Reliability Lower Bound", f"{lower_bounds.latency_reliability.lower_bound:.3f}")
    b4.metric("Fill Reliability Lower Bound", f"{lower_bounds.fill_reliability.lower_bound:.3f}")
    b5.metric("Competition Reliability Lower Bound", f"{lower_bounds.competition_reliability.lower_bound:.3f}")

    st.caption("Reliability lower bounds only; read-only shadow calibration under execution uncertainty.")

    shadow_calibration_rows = [
        {
            "execution_id": sample.execution_id,
            "snapshot_derived_liquidity": sample.snapshot_derived_liquidity,
            "observed_possible_fill": sample.observed_possible_fill,
            "shadow_disagreement": sample.error_metrics.weighted_error,
            "route_instability": sample.error_metrics.route_instability,
            "ledger_delay_error": sample.ledger_delay_error,
            "competition_penalty": sample.error_metrics.competition_penalty,
        }
        for sample in xrpl_shadow_calibration.samples
    ]

    st.subheader("Phantom Liquidity vs Observed Possible Fill")
    if shadow_calibration_rows:
        st.dataframe(shadow_calibration_rows[:50], use_container_width=True)
        st.bar_chart(
            shadow_calibration_rows[:50],
            x="execution_id",
            y=["snapshot_derived_liquidity", "observed_possible_fill"],
            use_container_width=True,
        )
    else:
        st.info("No shadow calibration samples available yet.")

    st.subheader("Route Instability Heatmap")
    if shadow_calibration_rows:
        route_heatmap = [
            {
                "execution_id": row["execution_id"],
                "route_instability": row["route_instability"],
                "shadow_disagreement": row["shadow_disagreement"],
            }
            for row in shadow_calibration_rows[:50]
        ]
        st.dataframe(route_heatmap, use_container_width=True)
    else:
        st.info("No route instability samples available yet.")

    st.subheader("Ledger Delay Distribution")
    if shadow_calibration_rows:
        st.bar_chart(
            [{"ledger_delay_error": row["ledger_delay_error"]} for row in shadow_calibration_rows],
            x="ledger_delay_error",
            y="ledger_delay_error",
            use_container_width=True,
        )
    else:
        st.info("No ledger delay samples available yet.")

    st.subheader("Competition Failure Rate")
    st.metric("Competition Failure Rate", f"{xrpl_shadow_calibration.competition_failure_rate * 100:.1f}%")
    st.caption(
        f"Expected slippage multiplier: {xrpl_shadow_calibration.calibration.recommendations.expected_slippage_multiplier:.3f}; "
        f"Execution probability floor: {xrpl_shadow_calibration.calibration.recommendations.execution_probability_floor:.3f}"
    )

    st.subheader("XRPL Trade Gate – Advisory Only")
    st.warning("XRPL liquidity remains uncertain")
    st.warning("Paths may change between ledgers")
    st.warning("Observed fill is probabilistic")
    st.warning("Memory weighting is advisory only")
    st.warning("No decision is auto-executed")
    st.warning("Token/issuer memory is based on shadow observations only")

    shadow_requested_default = 100.0
    if shadow_execution_rows:
        shadow_requested_default = float(shadow_execution_rows[0].get("filled_size", 100.0) or 100.0)
        shadow_requested_default = max(1.0, shadow_requested_default)
    gate_requested_size = float(
        st.number_input("Advisory Requested Size", min_value=0.0, value=shadow_requested_default, step=10.0)
    )
    gate_expected_profit = float(
        st.number_input("Advisory Expected Profit", value=max(1.0, gate_requested_size * 0.05), step=1.0)
    )
    gate_expected_loss = float(
        st.number_input("Advisory Expected Loss", min_value=0.0, value=max(1.0, gate_requested_size * 0.03), step=1.0)
    )

    gate_fill_probability = max(
        0.0,
        min(
            1.0,
            xrpl_shadow_calibration.calibration.fill_reliability.lower_bound
            * (1.0 - xrpl_shadow_calibration.route_instability_avg)
            * (1.0 - xrpl_shadow_calibration.competition_failure_rate)
            * (2.718281828459045 ** (-xrpl_shadow_calibration.ledger_delay_error_avg)),
        ),
    )
    gate_adjusted_slippage = (
        xrpl_shadow_calibration.calibration.recommendations.expected_slippage_multiplier
        * (1.0 + xrpl_shadow_calibration.route_instability_avg)
        * (1.0 + xrpl_shadow_calibration.competition_failure_rate)
    )
    gate_adjusted_ev = (
        gate_fill_probability * gate_expected_profit
        - ((1.0 - gate_fill_probability) * gate_expected_loss)
        - (gate_adjusted_slippage * gate_requested_size * 0.01)
    )
    gate_memory_weighting = XRPLMemoryWeighting().evaluate(
        XRPLMemoryWeightingInput(
            global_aggregate=memory_global,
            token_aggregate=memory_tokens[0] if memory_tokens else None,
            issuer_aggregate=memory_issuers[0] if memory_issuers else None,
            global_regime=global_regime,
            token_regime=regime_detector.assess(memory_tokens[0]) if memory_tokens else None,
            issuer_regime=regime_detector.assess(memory_issuers[0]) if memory_issuers else None,
        )
    )
    gate_decision = XRPLTradeGate().evaluate_trade(
        requested_size=gate_requested_size,
        effective_size=(
            gate_requested_size
            * (1.0 - xrpl_shadow_calibration.calibration.recommendations.liquidity_haircut)
            * (1.0 - xrpl_shadow_calibration.phantom_penalty_avg)
            * gate_fill_probability
        ),
        latency_path_adjusted_probability=gate_fill_probability,
        memory_adjusted_probability=gate_fill_probability * gate_memory_weighting.execution_probability_multiplier,
        memory_adjusted_effective_size=(
            gate_requested_size
            * (1.0 - xrpl_shadow_calibration.calibration.recommendations.liquidity_haircut)
            * (1.0 - xrpl_shadow_calibration.phantom_penalty_avg)
            * gate_fill_probability
            * gate_memory_weighting.effective_size_multiplier
        ),
        uncertainty_adjusted_value=gate_adjusted_ev - gate_memory_weighting.ev_penalty,
        drift_adjusted_ev=gate_adjusted_ev - gate_memory_weighting.ev_penalty,
        threshold=0.0,
        slippage_multiplier=gate_adjusted_slippage * gate_memory_weighting.slippage_multiplier_boost,
        liquidity_haircut=xrpl_shadow_calibration.calibration.recommendations.liquidity_haircut,
        phantom_penalty=xrpl_shadow_calibration.phantom_penalty_avg,
        route_instability=xrpl_shadow_calibration.route_instability_avg,
        competition_penalty=xrpl_shadow_calibration.competition_failure_rate,
        memory_risk_flags=gate_memory_weighting.risk_flags,
    )

    tg1, tg2, tg3, tg4 = st.columns(4)
    tg1.metric("Allow Trade", "YES" if gate_decision.allow_trade else "NO")
    tg2.metric("Execution Probability", f"{gate_decision.latency_path_adjusted_probability:.3f}")
    tg3.metric("Effective Size", f"{gate_decision.effective_size:.3f}")
    tg4.metric("Drift Adjusted EV", f"{gate_decision.drift_adjusted_ev:.3f}")

    tr1, tr2, tr3, tr4 = st.columns(4)
    tr1.metric("Phantom Penalty", f"{xrpl_shadow_calibration.phantom_penalty_avg:.3f}")
    tr2.metric("Route Instability", f"{xrpl_shadow_calibration.route_instability_avg:.3f}")
    tr3.metric("Competition Penalty", f"{xrpl_shadow_calibration.competition_failure_rate:.3f}")
    tr4.metric("Ledger Delay Error", f"{xrpl_shadow_calibration.ledger_delay_error_avg:.3f}")

    mw1, mw2, mw3, mw4 = st.columns(4)
    mw1.metric("Memory Probability Multiplier", f"{gate_memory_weighting.execution_probability_multiplier:.3f}")
    mw2.metric("Memory Size Multiplier", f"{gate_memory_weighting.effective_size_multiplier:.3f}")
    mw3.metric("Memory Slippage Boost", f"{gate_memory_weighting.slippage_multiplier_boost:.3f}")
    mw4.metric("Memory EV Penalty", f"{gate_memory_weighting.ev_penalty:.3f}")
    st.caption(
        "Memory risk flags: "
        + (", ".join(gate_memory_weighting.risk_flags) if gate_memory_weighting.risk_flags else "none")
    )
    st.caption("Advisory risk flags: " + (", ".join(gate_decision.risk_flags) if gate_decision.risk_flags else "none"))
    st.progress(max(0.0, min(1.0, gate_decision.latency_path_adjusted_probability)))
    st.bar_chart(
        [
            {"label": "requested_size", "value": gate_requested_size},
            {"label": "effective_size", "value": gate_decision.effective_size},
        ],
        x="label",
        y="value",
        use_container_width=True,
    )
    gate_base_ev = (
        xrpl_shadow_calibration.calibration.fill_reliability.lower_bound * gate_expected_profit
        - ((1.0 - xrpl_shadow_calibration.calibration.fill_reliability.lower_bound) * gate_expected_loss)
    )
    st.bar_chart(
        [
            {"label": "ev_before_adjustment", "value": gate_base_ev},
            {"label": "ev_after_drift", "value": gate_decision.drift_adjusted_ev},
        ],
        x="label",
        y="value",
        use_container_width=True,
    )

    st.subheader("XRPL Time Execution Model – Shadow Only")
    if time_execution_rows:
        st.bar_chart(time_execution_rows[:50], x="execution_id", y="latency_seconds", use_container_width=True)
        st.scatter_chart(time_execution_rows[:50], x="latency_seconds", y="price_drift", use_container_width=True)
        st.scatter_chart(
            time_execution_rows[:50],
            x="path_complexity",
            y="effective_fill_probability",
            use_container_width=True,
        )
        st.line_chart(time_execution_rows[:50], x="execution_id", y="liquidity_decay", use_container_width=True)
        st.bar_chart(
            time_execution_rows[:50],
            x="execution_id",
            y=["ev_before_drift", "drift_adjusted_ev"],
            use_container_width=True,
        )
    else:
        st.info("No time execution samples available yet.")

    st.subheader("XRPL Memory + Regime Detection")
    st.warning("XRPL liquidity remains uncertain")
    st.warning("Memory is derived from shadow observations")
    st.warning("Issuer behaviour may change abruptly")
    st.warning("Calibration is advisory only")
    mr1, mr2, mr3 = st.columns(3)
    mr1.metric("Global Risk Level", memory_global.advisory_risk_level)
    mr2.metric("Current Regime", global_regime.regime)
    mr3.metric("Regime Severity", f"{global_regime.severity_score:.3f}")

    token_memory_rows = [
        {
            "token_id": row.key,
            "samples": row.sample_count,
            "risk": row.advisory_risk_level,
            "regime": regime_detector.assess(row).regime,
            "phantom_penalty": row.avg_phantom_penalty,
            "liquidity_decay": row.avg_liquidity_decay,
            "route_instability": row.avg_route_instability,
            "fill_probability": row.avg_effective_fill_probability,
            "pressure": row.regime_pressure_score,
        }
        for row in memory_tokens
    ]
    issuer_memory_rows = [
        {
            "issuer": row.key,
            "samples": row.sample_count,
            "risk": row.advisory_risk_level,
            "regime": regime_detector.assess(row).regime,
            "latency_seconds": row.avg_latency_seconds,
            "competition_penalty": row.avg_competition_penalty,
            "path_complexity": row.avg_path_complexity,
            "pressure": row.regime_pressure_score,
        }
        for row in memory_issuers
    ]
    st.caption("Token-level memory")
    st.dataframe(token_memory_rows, use_container_width=True)
    st.caption("Issuer-level memory")
    st.dataframe(issuer_memory_rows, use_container_width=True)
    st.caption("Top risky tokens")
    st.dataframe(sorted(token_memory_rows, key=lambda row: float(row["pressure"]), reverse=True)[:10], use_container_width=True)
    st.caption("Top unstable issuers")
    st.dataframe(
        sorted(
            issuer_memory_rows,
            key=lambda row: (float(row["path_complexity"]) + float(row["competition_penalty"]) + float(row["latency_seconds"]) / 20.0),
            reverse=True,
        )[:10],
        use_container_width=True,
    )

    st.subheader("XRPL Continuous Shadow Loop")
    st.warning("Shadow decisions are advisory only")
    st.warning("No XRPL transaction is created or submitted")
    st.warning("Observed liquidity is uncertain and may not execute")
    st.warning("book_offers is snapshot-based only")
    shadow_decision_rows = [
        {
            "id": int(row.id or 0),
            "token_id": int(row.token_id),
            "issuer": row.issuer,
            "currency": row.currency,
            "ledger_index": int(row.ledger_index),
            "probability": float(row.memory_adjusted_probability),
            "effective_size": float(row.memory_adjusted_effective_size),
            "drift_adjusted_ev": float(row.drift_adjusted_ev),
            "regime": row.regime,
            "risk": row.advisory_risk_level,
            "observed_at": row.observed_at,
        }
        for row in shadow_decisions
    ]
    sl1, sl2, sl3, sl4 = st.columns(4)
    sl1.metric("Shadow Decisions", str(shadow_decision_summary.sample_count))
    sl2.metric("Avg Memory Probability", f"{shadow_decision_summary.avg_memory_adjusted_probability:.3f}")
    sl3.metric("Blocked Advisory Rate", f"{shadow_decision_summary.blocked_rate * 100:.1f}%")
    sl4.metric("Avg Drift EV", f"{shadow_decision_summary.avg_drift_adjusted_ev:.3f}")
    st.caption("Latest shadow decisions")
    st.dataframe(shadow_decision_rows[:100], use_container_width=True)
    if shadow_decision_rows:
        st.line_chart(list(reversed(shadow_decision_rows[:100])), x="observed_at", y="probability", use_container_width=True)
        st.bar_chart(
            [{"regime": key, "count": value} for key, value in shadow_decision_summary.regime_distribution.items()],
            x="regime",
            y="count",
            use_container_width=True,
        )
        st.bar_chart(
            [{"risk_flag": key, "count": value} for key, value in shadow_decision_summary.risk_flag_counts.items()],
            x="risk_flag",
            y="count",
            use_container_width=True,
        )
    else:
        st.info("No continuous shadow decisions recorded yet.")

    st.subheader("XRPL Validation — Prediction vs Outcome Windows")
    st.warning("No ground truth exists")
    st.warning("Observed outcomes are probabilistic")
    st.warning("Validation reflects observed disagreement under uncertainty")
    vx1, vx2, vx3, vx4 = st.columns(4)
    vx1.metric("Disagreement Score", f"{validation_avg_disagreement:.3f}")
    vx2.metric("Brier Score", f"{validation_avg_brier:.3f}")
    vx3.metric("Overconfidence Rate", f"{validation_overconfidence * 100:.1f}%")
    vx4.metric("Underconfidence Rate", f"{validation_underconfidence * 100:.1f}%")
    validation_rows = [
        {
            "decision_id": int(row.decision_id),
            "token_id": int(row.token_id),
            "regime": row.predicted_regime,
            "disagreement_score": float(row.disagreement_score),
            "brier_score": float(row.brier_score),
            "attribution": row.attribution,
            "created_at": row.created_at,
        }
        for row in shadow_validations
    ]
    if validation_rows:
        st.bar_chart(
            [{"attribution": key, "count": value} for key, value in sorted(validation_attribution.items())],
            x="attribution",
            y="count",
            use_container_width=True,
        )
        st.dataframe(validation_rows[:100], use_container_width=True)
    else:
        st.info("No shadow validation windows recorded yet.")

    st.subheader("XRPL Calibration Recommendations - Human Review")
    st.warning("Review surface only; no settings are changed")
    st.warning("Recommendations summarize observed disagreement under uncertainty")
    st.warning("Each item is a suggested review for a probabilistic outcome")
    recommendation_rows = [
        {
            "recommendation_id": row["recommendation_id"],
            "schema_version": row["schema_version"],
            "token_id": row["scope"].get("token_id"),
            "issuer": row["scope"].get("issuer"),
            "attribution": row["scope"].get("attribution", ""),
            "regime": row["scope"].get("regime", ""),
            "support_size": row["support_size"],
            "effective_sample_size": row["effective_sample_size"],
            "stability_score": row["stability_score"],
            "recommendation_strength": row["recommendation_strength"],
            "suggestion_direction": row["suggestion_direction"],
            "target_component": row["target_component"],
            "rationale": row["rationale"],
        }
        for row in calibration_recommendations
    ]
    review_history_rows = [review_to_dict(row) for row in calibration_reviews]
    if recommendation_rows:
        st.dataframe(recommendation_rows[:100], use_container_width=True)
        st.caption("Grouped by attribution")
        st.dataframe(
            sorted(recommendation_rows, key=lambda row: (str(row["attribution"]), str(row["regime"]), int(row["token_id"] or 0)))[:100],
            use_container_width=True,
        )
        recommendation_by_id = {str(row["recommendation_id"]): row for row in calibration_recommendations}
        with st.form("calibration_recommendation_review_form", clear_on_submit=False):
            st.caption("Record review")
            selected_recommendation_id = st.selectbox("Recommendation ID", sorted(recommendation_by_id))
            review_decision = st.selectbox("Review decision", ["noted", "deferred", "rejected", "accepted"])
            review_notes = st.text_area("Review notes", value="", max_chars=1000)
            reviewer_id = st.text_input("Reviewer ID", value="", max_chars=120)
            reviewed_at_text = st.text_input("Reviewed at UTC", value="1970-01-01T00:00:00+00:00")
            if st.form_submit_button("Record review"):
                try:
                    reviewed_at = datetime.fromisoformat(reviewed_at_text)
                    review_record = build_review_record(
                        recommendation=recommendation_by_id[selected_recommendation_id],
                        decision=review_decision,
                        review_notes=review_notes,
                        reviewer_id=(reviewer_id or None),
                        reviewed_at=reviewed_at,
                    )
                    with Session(engine) as review_session:
                        review_session.add(review_record)
                        review_session.commit()
                    st.success("Recorded review only; no settings changed.")
                except ValueError as exc:
                    st.error(f"Review was not recorded: {exc}")
    else:
        st.info("No calibration recommendations available for human review yet.")
    st.caption("Current review history")
    st.dataframe(review_history_rows[:100], use_container_width=True)
    audit_bundle = build_audit_export_bundle(
        recommendations=calibration_recommendations,
        reviews=calibration_reviews,
        deterministic=True,
    )
    st.download_button(
        "Export audit bundle",
        data=json.dumps(audit_bundle, sort_keys=True, indent=2),
        file_name="xrpl_calibration_audit_bundle.json",
        mime="application/json",
    )
    st.download_button(
        "Export review summary CSV",
        data=str(audit_bundle["csv_review_summary"]),
        file_name="xrpl_calibration_review_summary.csv",
        mime="text/csv",
    )

    st.subheader("XRPL Order Intent Simulation")
    st.warning("Derived from validated ledger data only")
    st.warning("Execution not guaranteed on XRPL")
    st.warning("Estimates based on current snapshot only")
    oi1, oi2, oi3, oi4 = st.columns(4)
    oi1.metric("Intent Count", str(simulated_intent_summary["count"]))
    oi2.metric("Avg Liquidity Score", f"{float(simulated_intent_summary['avg_liquidity_score']):.3f}")
    oi3.metric("Avg Fill Ratio", f"{float(simulated_intent_summary['avg_expected_fill_ratio']):.3f}")
    oi4.metric("Avg Path Viability", f"{float(simulated_intent_summary['avg_path_viability_score']):.3f}")
    intent_rows = [
        {
            "intent_id": row["intent_id"],
            "action": row["action"],
            "token_id": row["token_id"],
            "issuer": row["issuer"],
            "ledger_index": row["xrpl_context"]["ledger_index"],
            "liquidity_score": row["execution_estimates"]["liquidity_score"],
            "estimated_slippage": row["execution_estimates"]["estimated_slippage"],
            "expected_fill_ratio": row["execution_estimates"]["expected_fill_ratio"],
            "path_viability_score": row["pathfinding"]["path_viability_score"],
            "confidence_adjusted_fill": row["fill_model"]["confidence_adjusted_fill"],
        }
        for row in (intent.to_dict() for intent in simulated_intents)
    ]
    if intent_rows:
        st.dataframe(intent_rows[:100], use_container_width=True)
    else:
        st.info("No simulated order intents available from current validation and snapshot data.")

    st.subheader("XRPL Execution Feasibility")
    st.warning("Feasibility is advisory only")
    st.warning("No execution can be triggered from this panel")
    st.warning("Scores are based on current normalized liquidity snapshot")
    st.warning("XRPL routing and fills are not guaranteed")
    st.warning("AMM/hybrid liquidity is modelled as advisory context only")
    feasibility_rows = [
        {
            "intent_id": row["intent_id"],
            "score": row["execution_feasibility"]["execution_feasibility_score"],
            "route_type": row["execution_feasibility"]["route_type"],
            "expected_fill_ratio": row["execution_feasibility"]["expected_fill_ratio"],
            "expected_slippage": row["execution_feasibility"]["expected_slippage"],
            "weakest_hop_capacity": row["execution_feasibility"]["weakest_hop_capacity"],
            "quality_levels_required": row["execution_feasibility"]["quality_levels_required"],
            "decision": row["execution_feasibility"]["decision"],
            "avoid_reason": row["execution_feasibility"]["avoid_reason"],
            "failure_modes": ", ".join(row["execution_feasibility"]["failure_modes"]),
        }
        for row in (intent.to_dict() for intent in simulated_intents)
    ]
    if feasibility_rows:
        st.dataframe(feasibility_rows[:100], use_container_width=True)
    else:
        st.info("No feasibility rows available from current normalized liquidity snapshots.")

    st.subheader("XRPL Liquidity Source")
    st.warning("XRPL uses both orderbooks and AMMs")
    st.warning("Best execution is not guaranteed")
    st.warning("Liquidity conditions change per ledger")
    st.warning("No execution is triggered from this panel")
    liquidity_source_rows = [
        {
            "intent_id": row["intent_id"],
            "source_type": row["liquidity_source_model"]["liquidity_source"],
            "preferred_source": row["liquidity_source_model"]["preferred_source"],
            "orderbook_score": row["liquidity_source_model"]["orderbook_score"],
            "amm_score": row["liquidity_source_model"]["amm_score"],
            "hybrid_score": row["liquidity_source_model"]["hybrid_score"],
            "price_impact": row["liquidity_source_model"]["expected_price_impact"],
            "fill_ratio": row["liquidity_source_model"]["expected_fill_ratio"],
            "decision": row["liquidity_source_model"]["decision"],
            "warnings": ", ".join(row["liquidity_source_model"]["liquidity_warnings"]),
        }
        for row in (intent.to_dict() for intent in simulated_intents)
    ]
    if liquidity_source_rows:
        st.dataframe(liquidity_source_rows[:100], use_container_width=True)
    else:
        st.info("No liquidity source rows available from current snapshots.")

    st.subheader("XRPL Liquidity Freshness")
    st.warning("XRPL data validity is ledger-based")
    st.warning("Liquidity decays with ledger progression")
    st.warning("AMM liquidity changes rapidly per ledger")
    st.warning("No execution is triggered from this panel")
    freshness_rows = [
        {
            "intent_id": row["intent_id"],
            "ledger_age": row["liquidity_decay"]["snapshot_age_ledgers"],
            "decay_factor": row["liquidity_decay"]["decay_factor"],
            "decayed_feasibility": row["liquidity_decay"]["decayed_feasibility_score"],
            "decayed_fill_confidence": row["liquidity_decay"]["decayed_fill_confidence"],
            "decision": row["liquidity_decay"]["decision"],
            "warnings": ", ".join(row["liquidity_decay"]["warnings"]),
        }
        for row in (intent.to_dict() for intent in simulated_intents)
    ]
    if freshness_rows:
        st.dataframe(freshness_rows[:100], use_container_width=True)
    else:
        st.info("No freshness rows available from current ledger snapshots.")

    st.subheader("Paper Execution Simulation (XRPL)")
    st.warning("Simulated XRPL execution only")
    st.warning("Routing and fills are not guaranteed")
    st.warning("Based on current ledger snapshot")
    ps1, ps2, ps3, ps4 = st.columns(4)
    ps1.metric("Avg Fill Ratio", f"{float(paper_simulation_summary['avg_fill_ratio']):.3f}")
    ps2.metric("Avg Slippage", f"{float(paper_simulation_summary['avg_slippage']):.3f}")
    ps3.metric("Failure Rate", f"{float(paper_simulation_summary['failure_rate']) * 100:.1f}%")
    ps4.metric("Success Rate", f"{float(paper_simulation_summary['success_rate']) * 100:.1f}%")
    simulation_rows = [
        {
            "simulation_id": row["simulation_id"],
            "intent_id": row["intent_id"],
            "fill_ratio": row["fill_ratio"],
            "execution_status": row["execution_status"],
            "slippage_realized": row["slippage_realized"],
            "failure_reason": row["failure_reason"],
            "quality_levels_consumed": row["xrpl_execution_context"]["quality_levels_consumed"],
        }
        for row in paper_simulations
    ]
    if simulation_rows:
        st.dataframe(simulation_rows[:100], use_container_width=True)
    else:
        st.info("No paper execution simulations available from current intent and snapshot data.")

    st.subheader("Execution Boundary Guard")
    st.warning("Core execution boundary is fail-closed")
    st.warning("No signing or submission is available from this dashboard")
    st.warning("Manual approval cannot mutate execution configuration")
    eg1, eg2, eg3 = st.columns(3)
    eg1.metric("Allowed", "YES" if execution_guard_status["allowed"] else "NO")
    eg2.metric("Reason", str(execution_guard_status["reason"]))
    eg3.metric("Executable", "YES" if execution_guard_status["is_executable"] else "NO")

    st.subheader("XRPL Read-Only Ingestion Status")
    st.warning("Read-only XRPL observation only")
    st.warning("No transaction is created or submitted")
    st.warning("book_offers is snapshot polling only")
    st.warning("Observed liquidity may not execute")
    st.warning("Ingestion status does not imply executable liquidity")
    ih1, ih2, ih3, ih4 = st.columns(4)
    ih1.metric("Configured", "YES" if settings.XRPL_INGESTION_ENABLED else "NO")
    ih2.metric("Connected", "YES" if ingestion_health.connected else "NO")
    ih3.metric("Latest Ledger", str(ingestion_health.latest_ledger_index))
    ih4.metric("Validated Ledger", str(ingestion_health.latest_validated_ledger_index))
    ih5, ih6, ih7, ih8 = st.columns(4)
    ih5.metric("Stale Snapshots", str(ingestion_health.stale_snapshot_count))
    ih6.metric("Rejected Snapshots", str(ingestion_health.rejected_snapshot_count))
    ih7.metric("Reconnects", str(ingestion_health.reconnect_count))
    ih8.metric("Backoff Seconds", f"{ingestion_health.backoff_seconds:.1f}")
    st.caption(f"Ingestion reason: {ingestion_health.reason}")

    st.subheader("XRPL Live Shadow Mode")
    st.warning("XRPL orderbook is snapshot-based")
    st.warning("Observed liquidity may not execute")
    st.warning("No transaction is submitted")
    st.warning("System is advisory only")
    li1, li2, li3, li4 = st.columns(4)
    li1.metric("Ingestion Mode", ingestion_health.ingestion_mode)
    li2.metric("Source", ingestion_health.ingestion_source)
    li3.metric("Snapshot Rate", f"{ingestion_health.snapshot_rate_per_sec:.3f}/s")
    li4.metric("Avg Latency ms", f"{ingestion_health.last_snapshot_latency_ms:.1f}")
    li5, li6, li7 = st.columns(3)
    li5.metric("Rejection %", f"{ingestion_health.snapshot_rejection_rate * 100:.1f}%")
    li6.metric("Stale Snapshots", str(ingestion_health.stale_snapshot_count))
    li7.metric("Ledger Gaps", str(ingestion_health.ledger_gap_count))

    st.subheader("XRPL Live Probabilistic Observatory")
    st.warning("Ledger event-time drives validation windows")
    st.warning("Processing time is observability only")
    st.warning("No calibration setting is changed from this panel")
    live_status = default_live_status()
    live_drift = default_live_drift()
    lo1, lo2, lo3, lo4 = st.columns(4)
    lo1.metric("Current Ledger", str(live_status["current_ledger"]))
    lo2.metric("Buffer Size", str(live_status["buffer_size"]))
    lo3.metric("Ledger Lag", str(live_status["ledger_lag"]))
    lo4.metric("Health", str(live_status["health_state"]))
    latency = live_status["latency"]
    lp1, lp2, lp3 = st.columns(3)
    lp1.metric("Ingestion p95 ms", f"{latency['ingestion_latency_ms']['p95']:.1f}")
    lp2.metric("Processing p95 ms", f"{latency['processing_latency_ms']['p95']:.1f}")
    lp3.metric("Drift Magnitude", f"{float(live_drift['drift_magnitude']):.3f}")
    st.caption("Drift indicator is advisory-only and does not change calibration or review records.")

    st.subheader("XRPL Decision Quality – Ledger Aware")
    dq1, dq2, dq3, dq4 = st.columns(4)
    dq1.metric("Avg Fill Error", f"{decision_feedback.avg_fill_error:.3f}")
    dq2.metric("Avg EV Error", f"{decision_feedback.avg_ev_error:.3f}")
    dq3.metric("Overconfidence Rate", f"{decision_feedback.overconfidence_rate * 100:.1f}%")
    dq4.metric("Underconfidence Rate", f"{decision_feedback.underconfidence_rate * 100:.1f}%")

    dx1, dx2, dx3 = st.columns(3)
    dx1.metric("Ledger Delay Impact", f"{decision_feedback.avg_ledger_penalty:.3f}")
    dx2.metric("Route Instability", f"{decision_feedback.avg_route_instability:.3f}")
    dx3.metric("Competition Proxy Rate", f"{decision_feedback.competition_proxy_rate * 100:.1f}%")

    if decision_feedback.samples:
        st.bar_chart(
            [{"fill_error": sample.fill_error} for sample in decision_feedback.samples],
            x="fill_error",
            y="fill_error",
            use_container_width=True,
        )
        st.bar_chart(
            [{"ev_error": sample.ev_error} for sample in decision_feedback.samples],
            x="ev_error",
            y="ev_error",
            use_container_width=True,
        )
        st.bar_chart(
            [{"ledger_penalty": sample.ledger_penalty} for sample in decision_feedback.samples],
            x="ledger_penalty",
            y="ledger_penalty",
            use_container_width=True,
        )
        route_trend = [
            {"decision_id": sample.decision_id, "route_instability": sample.route_instability}
            for sample in decision_feedback.samples
        ]
        st.line_chart(route_trend, x="decision_id", y="route_instability", use_container_width=True)
    else:
        st.info("No decision feedback samples available yet.")

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


def _dashboard_quality_levels(snapshot: XRPLOrderbookSnapshot | None) -> list[dict[str, object]]:
    if snapshot is None:
        return []
    rows = snapshot.levels_json if isinstance(snapshot.levels_json, list) else []
    levels = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        side = str(row.get("side", "ask")).lower()
        if side not in {"ask", "sell", "offer"}:
            continue
        price = float(row.get("price", row.get("price_xrp_per_token", row.get("quality", snapshot.best_ask))) or 0.0)
        size = float(row.get("xrp_value", row.get("available_size", row.get("token_amount", 0.0))) or 0.0)
        levels.append({"quality": price, "price": price, "available_size": size, "funded": bool(row.get("funded", True))})
    if levels:
        return levels
    return [{"quality": float(snapshot.best_ask), "price": float(snapshot.best_ask), "available_size": float(snapshot.ask_depth_xrp), "funded": True}]


if __name__ == "__main__":
    main()

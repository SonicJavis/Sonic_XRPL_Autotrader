from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
import json
import uuid

from sqlmodel import Session, select

from app.alpha.engine import AlphaEngine
from app.config import BotMode, Settings
from app.db.models import (
    AlphaCooldownRecord,
    AlphaSignal,
    AuditEvent,
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
)
from app.execution.fill_simulator import ExecutionResult, simulate_entry_buy, simulate_exit_sell, validate_orderbook
from app.execution.liquidity_decay import analyze_liquidity_decay
from app.execution.paper import PaperExecutor
from app.execution.pnl_attribution_engine import PnLAttributionEngine
from app.execution.scanner import build_scanner_context
from app.market_data.metrics import MarketMetrics
from app.market_data.snapshot_builder import build_snapshot_from_offers
from app.risk.risk_manager import RiskManager
from app.risk.rules import RiskContext, RiskDecision, RiskEvaluation
from app.strategies.strategy_registry import StrategyRegistry
from app.telemetry.events import TelemetryEvent
from app.telemetry.logging import get_logger, log_event
from app.xrpl_core.client import XRPLReadOnlyClient


class ExecutionPipeline:
    def __init__(
        self,
        settings: Settings,
        xrpl_client: XRPLReadOnlyClient,
        strategy_registry: StrategyRegistry,
        risk_manager: RiskManager,
        paper_executor: PaperExecutor,
        alpha_engine: AlphaEngine,
    ) -> None:
        self.settings = settings
        self.xrpl_client = xrpl_client
        self.strategy_registry = strategy_registry
        self.risk_manager = risk_manager
        self.paper_executor = paper_executor
        self.alpha_engine = alpha_engine
        self.pnl_attribution = PnLAttributionEngine()
        self.logger = get_logger()

    def run_once(self, session: Session, current_price_xrp: float = 1.0) -> dict[str, object]:
        request_id = str(uuid.uuid4())
        watched = session.exec(select(WatchedToken).where(WatchedToken.is_active == True).order_by(WatchedToken.id.asc())).all()
        if not watched:
            return {"request_id": request_id, "signals": 0, "paper_trades_opened": 0, "reason": "no watched tokens"}

        executed: list[int] = []
        signals_count = 0

        for token in watched:
            orderbook = self._fetch_orderbook(token)
            snapshot_payload = build_snapshot_from_offers(orderbook.get("offers", []))
            parsed = snapshot_payload["parsed"]

            valid_book, invalid_reason = validate_orderbook(parsed)

            if not snapshot_payload["valid"] or not valid_book:
                explicit_reason = "INVALID_ORDERBOOK" if not valid_book else "INVALID_ORDERBOOK"
                self._audit(
                    session,
                    request_id,
                    "snapshot_invalid",
                    {
                        "token_id": token.id,
                        "invalid_reasons": snapshot_payload["invalid_reasons"] + ([invalid_reason] if invalid_reason else []),
                        "reason": explicit_reason,
                        "orderbook_stats": {
                            "raw_offer_count": snapshot_payload["raw_offer_count"],
                            "filtered_offer_count": snapshot_payload["filtered_offer_count"],
                            "rejected_orders": snapshot_payload["rejected_orders"],
                            "price_deviation_warnings": snapshot_payload["price_deviation_warnings"],
                        },
                    },
                )
                log_event(
                    self.logger,
                    {
                        "request_id": request_id,
                        "event_type": "snapshot_invalid",
                        "token": f"{token.currency}:{token.issuer}",
                        "raw_offer_count": snapshot_payload["raw_offer_count"],
                        "filtered_offer_count": snapshot_payload["filtered_offer_count"],
                        "rejected_orders": snapshot_payload["rejected_orders"],
                        "price_deviation_warnings": snapshot_payload["price_deviation_warnings"],
                        "invalid_reasons": snapshot_payload["invalid_reasons"],
                    },
                )
                continue

            snapshot = MarketSnapshot(
                token_id=token.id,
                price_xrp=snapshot_payload["price_xrp"],
                liquidity_xrp=float(snapshot_payload["liquidity_xrp"]),
                liquidity_bid_xrp=float(snapshot_payload["liquidity_bid_xrp"]),
                liquidity_ask_xrp=float(snapshot_payload["liquidity_ask_xrp"]),
                spread_pct=snapshot_payload["spread_pct"],
                best_bid=float(parsed["best_bid"]["price"]) if parsed.get("best_bid") else None,
                best_ask=float(parsed["best_ask"]["price"]) if parsed.get("best_ask") else None,
                volume_estimate=0.0,
                tx_count=int(snapshot_payload["order_count"]),
                bid_count=int(snapshot_payload["bid_count"]),
                ask_count=int(snapshot_payload["ask_count"]),
            )
            session.add(snapshot)
            session.commit()
            session.refresh(snapshot)

            if token.id is not None:
                self._update_open_outcomes_for_token(session, token.id, snapshot)

            self._store_depth_levels(session, snapshot.id, parsed)
            if token.id is not None:
                self.pnl_attribution.update_positions_for_snapshot(
                    session,
                    token_id=token.id,
                    snapshot=snapshot,
                    execution_latency_ms=self.settings.EXECUTION_LATENCY_MS,
                    max_snapshot_age_ms=self.settings.MAX_SNAPSHOT_AGE_MS,
                    liquidity_haircut_pct=self.settings.EXECUTION_QUEUE_HAIRCUT_PCT,
                    snapshot_to_decision_ms=self.settings.SNAPSHOT_TO_DECISION_MS,
                    decision_to_submission_ms=self.settings.DECISION_TO_SUBMISSION_MS,
                    submission_to_inclusion_ms=self.settings.SUBMISSION_TO_INCLUSION_MS,
                    latency_haircut_pct=self.settings.EXECUTION_LATENCY_HAIRCUT_PCT,
                    contention_haircut_pct=self.settings.EXECUTION_CONTENTION_HAIRCUT_PCT,
                    trustline_liquidity_discount_pct=self.settings.EXECUTION_TRUSTLINE_DISCOUNT_PCT,
                    ledger_drift_pct=self.settings.EXECUTION_LEDGER_DRIFT_PCT,
                    execution_window_snapshots=self.settings.EXECUTION_WINDOW_SNAPSHOTS,
                    min_level_xrp=self.settings.EXECUTION_MIN_LEVEL_XRP,
                    max_levels=self.settings.EXECUTION_MAX_LEVELS,
                    min_exit_retry_ms=self.settings.MIN_EXIT_RETRY_MS,
                    max_exit_retries=self.settings.MAX_EXIT_RETRIES,
                    approve_exit_fn=lambda pos, snap: self._risk_approves_exit(),
                )

            history = session.exec(
                select(MarketSnapshot)
                .where(MarketSnapshot.token_id == token.id)
                .order_by(MarketSnapshot.created_at.desc())
                .limit(self.settings.ALPHA_STABILITY_WINDOW)
            ).all()
            history = list(reversed(history))

            target_size_xrp = min(self.settings.MAX_TRADE_XRP, max(1.0, float(snapshot_payload["liquidity_xrp"]) / 5000.0))
            alpha_eval = self.alpha_engine.evaluate(
                pair=f"{token.currency}:{token.issuer or 'XRP'}",
                spread_pct=snapshot_payload["spread_pct"],
                bids=parsed.get("bids", []),
                asks=parsed.get("asks", []),
                history=history,
                target_size_xrp=target_size_xrp,
                issuer=token.issuer,
            )

            decay = analyze_liquidity_decay(
                settings=self.settings,
                history=history,
                bids=parsed.get("bids", []),
                asks=parsed.get("asks", []),
                spread_pct=snapshot_payload["spread_pct"],
            )
            if bool(decay["collapse_flag"]):
                alpha_eval.reasons.append("reject: liquidity collapse detected")
            if bool(decay["spoof_flag"]):
                alpha_eval.reasons.append("reject: spoof pattern detected")
            if bool(decay["fake_spread_flag"]):
                alpha_eval.reasons.append("reject: fake tight spread detected")
            if bool(decay["collapse_flag"] or decay["spoof_flag"] or decay["fake_spread_flag"]):
                alpha_eval.decision = "REJECT"
            alpha_eval.manipulation_flags.update(
                {
                    "liquidity_collapse": bool(decay["collapse_flag"]),
                    "spoof_pattern": bool(decay["spoof_flag"]),
                    "fake_tight_spread": bool(decay["fake_spread_flag"]),
                }
            )

            if token.id is not None and self._token_in_cooldown(session, token.id, self.settings):
                alpha_eval.decision = "REJECT"
                alpha_eval.reasons = ["reject: alpha cooldown active"]

            if alpha_eval.decision != "APPROVE":
                if token.id is not None:
                    session.add(AlphaCooldownRecord(token_id=token.id))
                session.add(
                    RiskEvent(
                        event_type="ALPHA_REJECT",
                        severity="WARN",
                        reason="; ".join(alpha_eval.reasons),
                    )
                )
                session.commit()

            alpha_signal = AlphaSignal(
                token_id=token.id,
                snapshot_id=snapshot.id,
                pair=alpha_eval.pair,
                score=alpha_eval.score,
                decision=alpha_eval.decision,
                reasons_json=json.dumps(alpha_eval.reasons),
                spread_pct=alpha_eval.spread,
                depth_xrp=alpha_eval.depth_xrp,
                imbalance=alpha_eval.imbalance,
                slippage_pct=max(0.0, alpha_eval.slippage_estimate),
                fill_probability=alpha_eval.fill_probability,
                stability_score=alpha_eval.stability_score,
                spread_stability=alpha_eval.spread_stability,
                liquidity_consistency=alpha_eval.liquidity_consistency,
                mid_price_stability=alpha_eval.mid_price_stability,
                component_scores_json=json.dumps(alpha_eval.component_scores),
                manipulation_flags_json=json.dumps(alpha_eval.manipulation_flags),
            )
            session.add(alpha_signal)
            session.commit()
            session.refresh(alpha_signal)

            context = build_scanner_context(
                issuer=token.issuer,
                currency=token.currency,
                price_xrp=snapshot_payload["price_xrp"],
                spread_pct=snapshot_payload["spread_pct"],
                liquidity_xrp=float(snapshot_payload["liquidity_xrp"]),
                bid_count=int(snapshot_payload["bid_count"]),
                ask_count=int(snapshot_payload["ask_count"]),
            )

            candidates = self.strategy_registry.run_all_strategies(context)
            if alpha_eval.decision != "APPROVE":
                for candidate in candidates:
                    candidate.side = "HOLD"
                    candidate.suggested_size_xrp = 0.0
                    candidate.reason = f"alpha rejected: {'; '.join(alpha_eval.reasons)}"
            else:
                for candidate in candidates:
                    if candidate.side.upper() == "BUY":
                        candidate.reason = f"{candidate.reason}; alpha approved score={alpha_eval.score:.3f}"

            for candidate in candidates:
                signals_count += 1
                signal = Signal(
                    strategy_name=candidate.strategy_name,
                    issuer=candidate.issuer,
                    currency=candidate.currency,
                    side=candidate.side,
                    confidence=candidate.confidence,
                    risk_score=candidate.risk_score,
                    suggested_size_xrp=candidate.suggested_size_xrp,
                    reason=candidate.reason,
                )
                session.add(signal)
                session.commit()
                session.refresh(signal)

                slippage = self.risk_manager.estimate_slippage(candidate.suggested_size_xrp, parsed.get("asks", []))

                risk_eval = self.risk_manager.evaluate(
                    candidate,
                    RiskContext(
                        open_positions=len(session.exec(select(PaperTrade).where(PaperTrade.status == "OPEN")).all()),
                        total_exposure_xrp=sum(
                            float(t.size_xrp) for t in session.exec(select(PaperTrade).where(PaperTrade.status == "OPEN")).all()
                        ),
                        daily_loss_xrp=0.0,
                        market_snapshot=MarketMetrics(
                            price_xrp=snapshot_payload["price_xrp"],
                            liquidity_xrp=float(snapshot_payload["liquidity_xrp"]),
                            spread_pct=snapshot_payload["spread_pct"],
                            volume_estimate=0.0,
                            tx_count=int(snapshot_payload["order_count"]),
                            bid_count=int(snapshot_payload["bid_count"]),
                            ask_count=int(snapshot_payload["ask_count"]),
                        ),
                        bid_count=int(snapshot_payload["bid_count"]),
                        ask_count=int(snapshot_payload["ask_count"]),
                        bids=parsed.get("bids", []),
                        asks=parsed.get("asks", []),
                        slippage_pct=float(slippage["slippage_pct"]),
                        fill_possible=bool(slippage["fill_possible"]),
                        is_exit=False,
                        live_trading_requested=False,
                    ),
                )

                if bool(decay["collapse_flag"] or decay["spoof_flag"] or decay["fake_spread_flag"]):
                    decay_reasons: list[str] = []
                    if bool(decay["collapse_flag"]):
                        decay_reasons.append("liquidity_collapse")
                    if bool(decay["spoof_flag"]):
                        decay_reasons.append("spoof_pattern")
                    if bool(decay["fake_spread_flag"]):
                        decay_reasons.append("fake_tight_spread")
                    risk_eval = RiskEvaluation(
                        decision=RiskDecision.DENY,
                        reason=f"adversarial_liquidity_detected: {','.join(decay_reasons)}",
                        approved_size_xrp=0.0,
                    )

                risk_record = RiskDecisionRecord(
                    token_id=token.id,
                    snapshot_id=snapshot.id,
                    signal_id=signal.id,
                    decision=risk_eval.decision.value,
                    reason=risk_eval.reason,
                    score=alpha_eval.score,
                    reasons_json=json.dumps(alpha_eval.reasons),
                )
                session.add(risk_record)
                session.commit()
                session.refresh(risk_record)

                if risk_eval.decision != RiskDecision.APPROVE:
                    session.add(
                        RiskEvent(
                            event_type="RISK_DENIAL",
                            severity="WARN",
                            reason=risk_eval.reason,
                        )
                    )
                    session.commit()
                    self._audit(
                        session,
                        request_id,
                        "risk_denied",
                        {
                            "signal_id": signal.id,
                            "reason": risk_eval.reason,
                            "snapshot_id": snapshot.id,
                            "orderbook_stats": {
                                "bid_count": snapshot.bid_count,
                                "ask_count": snapshot.ask_count,
                                "spread_pct": snapshot.spread_pct,
                                "liquidity_xrp": snapshot.liquidity_xrp,
                            },
                        },
                    )
                    continue

                if self.settings.BOT_MODE == BotMode.PAPER_TRADING and candidate.side.upper() == "BUY":
                    if snapshot_payload["price_xrp"] is None:
                        self._audit(
                            session,
                            request_id,
                            "execution_skipped",
                            {
                                "signal_id": signal.id,
                                "reason": "missing execution price",
                                "snapshot_id": snapshot.id,
                            },
                        )
                        continue

                    snapshot_time = self._normalize_utc(snapshot.created_at)
                    signal_time = self._normalize_utc(signal.created_at)
                    execution_time = signal_time + self._latency_delta()

                    try:
                        reservation = self.paper_executor.reserve_capital(
                            session,
                            signal_id=signal.id,
                            issuer=candidate.issuer,
                            currency=candidate.currency,
                            requested_xrp=candidate.suggested_size_xrp,
                        )
                    except ValueError as exc:
                        session.add(
                            RiskEvent(
                                event_type="CAPITAL_DENIAL",
                                severity="WARN",
                                reason=str(exc),
                            )
                        )
                        session.commit()
                        self._audit(
                            session,
                            request_id,
                            "execution_skipped",
                            {
                                "signal_id": signal.id,
                                "reason": str(exc),
                                "snapshot_id": snapshot.id,
                            },
                        )
                        continue

                    strict_fill = simulate_entry_buy(
                        asks=parsed.get("asks", []),
                        best_bid=float(parsed["best_bid"]["price"]) if parsed.get("best_bid") else 0.0,
                        best_ask=float(parsed["best_ask"]["price"]) if parsed.get("best_ask") else 0.0,
                        requested_size_xrp=candidate.suggested_size_xrp,
                        snapshot_time=snapshot_time,
                        signal_time=signal_time,
                        execution_latency_ms=self.settings.EXECUTION_LATENCY_MS,
                        snapshot_to_decision_ms=self.settings.SNAPSHOT_TO_DECISION_MS,
                        decision_to_submission_ms=self.settings.DECISION_TO_SUBMISSION_MS,
                        submission_to_inclusion_ms=self.settings.SUBMISSION_TO_INCLUSION_MS,
                        max_snapshot_age_ms=self.settings.MAX_SNAPSHOT_AGE_MS,
                        liquidity_haircut_pct=self.settings.EXECUTION_QUEUE_HAIRCUT_PCT,
                        latency_haircut_pct=self.settings.EXECUTION_LATENCY_HAIRCUT_PCT,
                        contention_haircut_pct=self.settings.EXECUTION_CONTENTION_HAIRCUT_PCT,
                        trustline_liquidity_discount_pct=self.settings.EXECUTION_TRUSTLINE_DISCOUNT_PCT,
                        ledger_drift_pct=self.settings.EXECUTION_LEDGER_DRIFT_PCT,
                        execution_window_snapshots=self.settings.EXECUTION_WINDOW_SNAPSHOTS,
                        min_level_xrp=self.settings.EXECUTION_MIN_LEVEL_XRP,
                        max_levels=self.settings.EXECUTION_MAX_LEVELS,
                    )

                    fill_success = strict_fill.fill_success
                    partial_fill = strict_fill.partial_fill
                    actual_slippage = strict_fill.slippage_pct
                    expected_slippage = float(max(0.0, alpha_eval.slippage_estimate))
                    filled_size = strict_fill.filled_size
                    entry_price = float(strict_fill.avg_entry_price or 0.0)

                    reason_closed: str | None = None
                    if strict_fill.failure_reason == "STALE_MARKET_DATA":
                        reason_closed = "STALE_MARKET_DATA"
                    elif strict_fill.failure_reason == "INVALID_ORDERBOOK":
                        reason_closed = "INVALID_ORDERBOOK"
                    elif strict_fill.fill_status == "UNFILLED":
                        reason_closed = strict_fill.failure_reason or "NO_LIQUIDITY"
                    elif actual_slippage > self.settings.PERF_MAX_ACTUAL_SLIPPAGE_PCT:
                        reason_closed = "reality_filter: slippage_above_threshold"
                    else:
                        post_book = self._fetch_orderbook(token)
                        post_snapshot = build_snapshot_from_offers(post_book.get("offers", []))
                        post_liquidity = float(post_snapshot.get("liquidity_ask_xrp") or 0.0)
                        base_liquidity = float(snapshot_payload.get("liquidity_ask_xrp") or 0.0)
                        liquidity_ratio = (post_liquidity / base_liquidity) if base_liquidity > 0 else 0.0
                        if base_liquidity > 0 and liquidity_ratio < self.settings.PERF_BOOK_COLLAPSE_RATIO:
                            reason_closed = "reality_filter: book_collapsed_post_entry"
                        elif post_liquidity < self.settings.PERF_MIN_POST_ENTRY_LIQUIDITY_XRP:
                            reason_closed = "reality_filter: liquidity_disappeared"

                    outcome = PaperTradeOutcome(
                        token_id=token.id or 0,
                        signal_id=signal.id or 0,
                        snapshot_id=snapshot.id,
                        entry_price=entry_price,
                        expected_slippage_pct=expected_slippage,
                        actual_slippage_pct=actual_slippage,
                        target_size_xrp=candidate.suggested_size_xrp,
                        filled_size_xrp=filled_size,
                        fill_success=fill_success,
                        partial_fill=partial_fill,
                        fill_status=strict_fill.fill_status,
                        entry_time=execution_time,
                        snapshot_time=snapshot_time,
                        signal_time=signal_time,
                        execution_time=execution_time,
                        execution_latency_ms=self.settings.EXECUTION_LATENCY_MS,
                        snapshot_age_ms=strict_fill.snapshot_age_ms,
                        failure_reason=strict_fill.failure_reason,
                    )

                    try:
                        execution_record = self.pnl_attribution.create_execution_record(
                            session,
                            token_id=token.id or 0,
                            signal_id=signal.id or 0,
                            risk_decision_id=risk_record.id,
                            snapshot_id=snapshot.id or 0,
                            position_id=None,
                            side="BUY",
                            execution_result=strict_fill,
                            snapshot_time=snapshot_time,
                            signal_time=signal_time,
                            execution_time=execution_time,
                            xrpl_ledger_close_ms=self.settings.XRPL_LEDGER_CLOSE_MS,
                            min_ledger_delay=self.settings.MIN_LEDGER_DELAY,
                            max_ledger_delay=self.settings.MAX_LEDGER_DELAY,
                        )
                    except ValueError as exc:
                        self.paper_executor.release_reservation(
                            session,
                            reservation_id=reservation.id,
                            reason="FAILED_INVALID_TIMING",
                        )
                        session.add(
                            RiskEvent(
                                event_type="EXECUTION_INVALID_TIMING",
                                severity="ERROR",
                                reason=str(exc),
                            )
                        )
                        session.commit()
                        self._audit(
                            session,
                            request_id,
                            "execution_skipped",
                            {
                                "signal_id": signal.id,
                                "reason": "FAILED_INVALID_TIMING",
                                "snapshot_id": snapshot.id,
                            },
                        )
                        continue

                    if reason_closed is not None:
                        self.paper_executor.settle_entry_fill(
                            session,
                            reservation_id=reservation.id,
                            filled_xrp=0.0,
                            failure_reason=reason_closed,
                        )
                        outcome.exit_time = execution_time
                        outcome.exit_price = None
                        outcome.pnl_xrp = 0.0
                        outcome.reason_closed = reason_closed
                        session.add(outcome)
                        session.add(
                            RiskEvent(
                                event_type="REALITY_FILTER_REJECT",
                                severity="WARN",
                                reason=reason_closed,
                            )
                        )
                        session.commit()
                        log_event(
                            self.logger,
                            {
                                "event_type": "execution",
                                "requested": strict_fill.requested_size,
                                "filled": strict_fill.filled_size,
                                "status": strict_fill.fill_status,
                                "avg_price": strict_fill.avg_entry_price,
                                "slippage": strict_fill.slippage_pct,
                                "latency_ms": strict_fill.execution_latency_ms,
                                "reason": reason_closed,
                            },
                        )
                        self._audit(
                            session,
                            request_id,
                            "execution_skipped",
                            {
                                "signal_id": signal.id,
                                "reason": reason_closed,
                                "snapshot_id": snapshot.id,
                            },
                        )
                        continue

                    settled = self.paper_executor.settle_entry_fill(
                        session,
                        reservation_id=reservation.id,
                        filled_xrp=filled_size,
                        failure_reason=strict_fill.failure_reason,
                    )

                    if settled.deployed_xrp <= 0:
                        outcome.reason_closed = "ENTRY_FAILED"
                        outcome.failure_reason = outcome.failure_reason or "NO_DEPLOYED_CAPITAL"
                        outcome.exit_time = execution_time
                        outcome.pnl_xrp = 0.0
                        session.add(outcome)
                        session.commit()
                        continue

                    trade = self.paper_executor.open_trade(
                        session,
                        candidate,
                        entry_price_xrp=entry_price,
                        size_xrp=settled.deployed_xrp,
                        reservation_id=settled.id,
                    )
                    executed.append(trade.id)

                    pos = self.pnl_attribution.create_position_from_entry(
                        session,
                        token_id=token.id or 0,
                        issuer=token.issuer,
                        currency=token.currency,
                        signal_id=signal.id or 0,
                        risk_decision_id=risk_record.id,
                        execution_record_id=execution_record.id or 0,
                        snapshot_id=snapshot.id or 0,
                        execution_result=strict_fill,
                        alpha_signal=alpha_signal,
                        execution_time=execution_time,
                    )
                    if pos is None:
                        outcome.reason_closed = "ENTRY_FAILED"
                        outcome.failure_reason = outcome.failure_reason or "ENTRY_FAILED"
                    else:
                        outcome.reason_closed = None

                    session.add(outcome)
                    session.commit()

                    log_event(
                        self.logger,
                        {
                            "event_type": "execution",
                            "requested": strict_fill.requested_size,
                            "filled": strict_fill.filled_size,
                            "status": strict_fill.fill_status,
                            "avg_price": strict_fill.avg_entry_price,
                            "slippage": strict_fill.slippage_pct,
                            "latency_ms": strict_fill.execution_latency_ms,
                            "reason": strict_fill.failure_reason,
                        },
                    )

                    self._audit(
                        session,
                        request_id,
                        "paper_trade_opened",
                        {
                            "trade_id": trade.id,
                            "snapshot_id": snapshot.id,
                            "decision_reason": risk_eval.reason,
                            "signal_id": signal.id,
                            "expected_slippage_pct": expected_slippage,
                            "actual_slippage_pct": actual_slippage,
                            "fill_status": strict_fill.fill_status,
                            "snapshot_age_ms": strict_fill.snapshot_age_ms,
                        },
                    )

                    self._check_canonical_ledger_mismatch(session, token.id)

                telemetry = TelemetryEvent(
                    request_id=request_id,
                    event_type="pipeline_signal_processed",
                    strategy=candidate.strategy_name,
                    token=f"{candidate.currency}:{candidate.issuer}",
                    risk_decision=risk_eval.decision.value,
                    execution_result="executed" if candidate.side.upper() == "BUY" else "skipped",
                )
                log_event(self.logger, asdict(telemetry))
                log_event(
                    self.logger,
                    {
                        "request_id": request_id,
                        "event_type": "orderbook_stats",
                        "strategy": candidate.strategy_name,
                        "token": f"{candidate.currency}:{candidate.issuer}",
                        "raw_offer_count": snapshot_payload["raw_offer_count"],
                        "filtered_offer_count": snapshot_payload["filtered_offer_count"],
                        "rejected_orders": snapshot_payload["rejected_orders"],
                        "price_deviations": snapshot_payload["price_deviation_warnings"],
                        "slippage_pct": float(slippage["slippage_pct"]),
                        "fill_possible": bool(slippage["fill_possible"]),
                        "liquidity_bid_xrp": float(snapshot_payload["liquidity_bid_xrp"]),
                        "liquidity_ask_xrp": float(snapshot_payload["liquidity_ask_xrp"]),
                        "alpha_score": alpha_eval.score,
                        "alpha_decision": alpha_eval.decision,
                        "alpha_reasons": alpha_eval.reasons,
                    },
                )

        return {
            "request_id": request_id,
            "signals": signals_count,
            "paper_trades_opened": len(executed),
        }

    @staticmethod
    def _risk_approves_exit() -> bool:
        # Exit risk gate is explicit and deterministic in this phase.
        return True

    def _check_canonical_ledger_mismatch(self, session: Session, token_id: int | None) -> None:
        if token_id is None:
            return
        canonical = session.exec(select(Position).where(Position.token_id == token_id)).all()
        legacy = session.exec(select(PaperTradeOutcome).where(PaperTradeOutcome.token_id == token_id)).all()

        canonical_count = len(canonical)
        legacy_count = len(legacy)
        mismatch_type: str | None = None

        if canonical_count > legacy_count:
            mismatch_type = "canonical_gt_legacy"
        elif legacy_count > canonical_count:
            mismatch_type = "legacy_gt_canonical"
        else:
            canonical_statuses = sorted([str(p.status) for p in canonical])
            legacy_statuses = sorted([("CLOSED" if o.exit_time is not None else "OPEN") for o in legacy])

            canonical_entry_size = round(sum(float(p.entry_filled_size or 0.0) for p in canonical), 9)
            legacy_entry_size = round(sum(float(o.filled_size_xrp or 0.0) for o in legacy), 9)

            canonical_exit_size = round(sum(float(p.exit_filled_size or 0.0) for p in canonical), 9)
            legacy_closed_size = round(
                sum(float(o.filled_size_xrp or 0.0) for o in legacy if o.exit_time is not None),
                9,
            )

            canonical_outcomes = sorted([
                ("CLOSED" if p.status == "CLOSED" else "OPEN")
                for p in canonical
            ])
            legacy_outcomes = sorted([
                ("CLOSED" if o.exit_time is not None else "OPEN")
                for o in legacy
            ])

            if (
                canonical_statuses != legacy_statuses
                or canonical_entry_size != legacy_entry_size
                or canonical_exit_size != legacy_closed_size
                or canonical_outcomes != legacy_outcomes
            ):
                mismatch_type = "semantic_mismatch"

        if mismatch_type is not None:
            log_event(
                self.logger,
                {
                    "event_type": "canonical_ledger_mismatch",
                    "token_id": token_id,
                    "canonical_count": canonical_count,
                    "legacy_count": legacy_count,
                    "mismatch_type": mismatch_type,
                    "severity": "WARN",
                },
            )

    def _fetch_orderbook(self, token: WatchedToken) -> dict[str, object]:
        if token.is_xrp:
            return {"offers": []}

        taker_gets = {"currency": token.currency, "issuer": token.issuer}
        taker_pays = "1000000"
        ask_book = self.xrpl_client.get_book_offers(taker_gets=taker_gets, taker_pays=taker_pays)

        bid_book = self.xrpl_client.get_book_offers(
            taker_gets=taker_pays,
            taker_pays=taker_gets,
        )

        asks = [dict(offer, side="ask") for offer in ask_book.get("offers", [])]
        bids = [dict(offer, side="bid") for offer in bid_book.get("offers", [])]
        return {"offers": bids + asks}

    @staticmethod
    def _token_in_cooldown(session: Session, token_id: int, settings: "Settings") -> bool:  # type: ignore[name-defined]
        from datetime import timezone as _tz, timedelta as _td
        threshold = datetime.now(tz=_tz.utc) - _td(minutes=settings.ALPHA_COOLDOWN_MINUTES)
        recent = session.exec(
            select(AlphaCooldownRecord)
            .where(AlphaCooldownRecord.token_id == token_id)
            .where(AlphaCooldownRecord.rejected_at >= threshold)
            .order_by(AlphaCooldownRecord.rejected_at.desc())
        ).all()
        return len(recent) >= settings.ALPHA_COOLDOWN_FAILURES

    @staticmethod
    def _audit(session: Session, request_id: str, event_type: str, payload: dict[str, object]) -> None:
        session.add(AuditEvent(request_id=request_id, event_type=event_type, payload_json=json.dumps(payload, default=str)))
        session.commit()

    def _latency_delta(self):
        from datetime import timedelta
        return timedelta(milliseconds=self.settings.EXECUTION_LATENCY_MS)

    @staticmethod
    def _normalize_utc(ts: datetime) -> datetime:
        if ts.tzinfo is None:
            return ts.replace(tzinfo=timezone.utc)
        return ts.astimezone(timezone.utc)

    def exit_liquidity_check(
        self,
        session: Session,
        snapshot: MarketSnapshot,
        requested_token_size: float,
    ) -> tuple[bool, str | None, list[dict[str, float]], list[dict[str, float]], float, float]:
        levels = session.exec(
            select(MarketDepthLevel)
            .where(MarketDepthLevel.snapshot_id == snapshot.id)
            .order_by(MarketDepthLevel.side.asc(), MarketDepthLevel.level_index.asc())
        ).all()
        bids = [
            {"price": row.price_xrp_per_token, "token_amount": row.token_amount, "xrp_value": row.xrp_value}
            for row in levels
            if row.side == "bid"
        ]
        asks = [
            {"price": row.price_xrp_per_token, "token_amount": row.token_amount, "xrp_value": row.xrp_value}
            for row in levels
            if row.side == "ask"
        ]

        best_bid = float(bids[0]["price"]) if bids else 0.0
        best_ask = float(asks[0]["price"]) if asks else 0.0

        if requested_token_size <= 0:
            return False, "NO_REQUESTED_SIZE", bids, asks, best_bid, best_ask
        if not bids:
            return False, "NO_BIDS", bids, asks, best_bid, best_ask
        if best_bid <= 0 or best_ask <= 0 or best_bid >= best_ask:
            return False, "INVALID_ORDERBOOK", bids, asks, best_bid, best_ask
        return True, None, bids, asks, best_bid, best_ask

    def partial_exit_simulation(
        self,
        row: PaperTradeOutcome,
        snapshot: MarketSnapshot,
        bids: list[dict[str, float]],
        asks: list[dict[str, float]],
        best_bid: float,
        best_ask: float,
    ) -> ExecutionResult:
        requested_tokens = row.filled_size_xrp / row.entry_price if row.entry_price > 0 else 0.0
        return simulate_exit_sell(
            bids=bids,
            best_bid=best_bid,
            best_ask=best_ask,
            requested_token_size=requested_tokens,
            snapshot_time=self._normalize_utc(snapshot.created_at),
            signal_time=datetime.now(tz=timezone.utc),
            execution_latency_ms=self.settings.EXECUTION_LATENCY_MS,
            snapshot_to_decision_ms=self.settings.SNAPSHOT_TO_DECISION_MS,
            decision_to_submission_ms=self.settings.DECISION_TO_SUBMISSION_MS,
            submission_to_inclusion_ms=self.settings.SUBMISSION_TO_INCLUSION_MS,
            max_snapshot_age_ms=self.settings.MAX_SNAPSHOT_AGE_MS,
            liquidity_haircut_pct=self.settings.EXECUTION_QUEUE_HAIRCUT_PCT,
            latency_haircut_pct=self.settings.EXECUTION_LATENCY_HAIRCUT_PCT,
            contention_haircut_pct=self.settings.EXECUTION_CONTENTION_HAIRCUT_PCT,
            trustline_liquidity_discount_pct=self.settings.EXECUTION_TRUSTLINE_DISCOUNT_PCT,
            ledger_drift_pct=self.settings.EXECUTION_LEDGER_DRIFT_PCT,
            execution_window_snapshots=self.settings.EXECUTION_WINDOW_SNAPSHOTS,
            min_level_xrp=self.settings.EXECUTION_MIN_LEVEL_XRP,
            max_levels=self.settings.EXECUTION_MAX_LEVELS,
        )

    def _update_open_outcomes_for_token(self, session: Session, token_id: int, snapshot: MarketSnapshot) -> None:
        if snapshot.id is None:
            return

        now = datetime.now(tz=timezone.utc)
        horizon_seconds = float(self.settings.PERF_MONITOR_MINUTES * 60)
        rows = session.exec(
            select(PaperTradeOutcome)
            .where(PaperTradeOutcome.token_id == token_id)
            .where(PaperTradeOutcome.exit_time == None)
            .order_by(PaperTradeOutcome.id.asc())
        ).all()

        for row in rows:
            if row.entry_price <= 0:
                continue

            mark_bid = snapshot.best_bid
            if mark_bid is None or mark_bid <= 0:
                mark_bid = snapshot.price_xrp
            if mark_bid is None or mark_bid <= 0:
                continue

            move_pct = ((float(mark_bid) - row.entry_price) / row.entry_price) * 100.0
            row.max_adverse_excursion_pct = max(row.max_adverse_excursion_pct, max(0.0, -move_pct))
            row.max_favorable_excursion_pct = max(row.max_favorable_excursion_pct, max(0.0, move_pct))

            entry_time = row.entry_time
            if entry_time.tzinfo is None:
                entry_time = entry_time.replace(tzinfo=timezone.utc)
            elapsed_seconds = (now - entry_time).total_seconds()
            if elapsed_seconds >= horizon_seconds:
                ok, reason, bids, asks, best_bid, best_ask = self.exit_liquidity_check(
                    session,
                    snapshot,
                    requested_token_size=(row.filled_size_xrp / row.entry_price) if row.entry_price > 0 else 0.0,
                )
                if not ok:
                    row.exit_time = now
                    row.failure_reason = reason
                    row.reason_closed = "exit_failed"
                    session.add(row)
                    continue

                exit_result = self.partial_exit_simulation(row, snapshot, bids, asks, best_bid, best_ask)
                self._close_outcome(row, exit_result, reason="monitor_horizon_elapsed")

            session.add(row)

        session.commit()

    @staticmethod
    def _close_outcome(row: PaperTradeOutcome, exit_result: ExecutionResult, reason: str) -> None:
        row.exit_time = datetime.now(tz=timezone.utc)
        row.exit_price = float(exit_result.avg_exit_price) if exit_result.avg_exit_price is not None else None
        row.fill_status = exit_result.fill_status
        row.failure_reason = exit_result.failure_reason
        if row.entry_price > 0 and row.filled_size_xrp > 0 and row.exit_price is not None:
            row.pnl_xrp = row.filled_size_xrp * ((row.exit_price - row.entry_price) / row.entry_price)
        else:
            row.pnl_xrp = None
        row.reason_closed = reason

    @staticmethod
    def _store_depth_levels(session: Session, snapshot_id: int | None, parsed: dict[str, object]) -> None:
        if snapshot_id is None:
            return

        for side in ("bids", "asks"):
            cumulative = 0.0
            for idx, level in enumerate(parsed.get(side, [])[:8]):
                xrp_value = float(level.get("xrp_value", 0.0))
                cumulative += xrp_value
                session.add(
                    MarketDepthLevel(
                        snapshot_id=snapshot_id,
                        side="bid" if side == "bids" else "ask",
                        level_index=idx,
                        price_xrp_per_token=float(level.get("price", 0.0)),
                        token_amount=float(level.get("token_amount", 0.0)),
                        xrp_value=xrp_value,
                        cumulative_xrp=cumulative,
                    )
                )
        session.commit()

from __future__ import annotations

import streamlit as st
from sqlmodel import Session, select

from app.alpha.performance_engine import PerformanceEngine
from app.config import Settings
from app.db.models import (
    AlphaSignal,
    MarketDepthLevel,
    MarketSnapshot,
    PaperTrade,
    PaperTradeOutcome,
    RiskDecisionRecord,
    RiskEvent,
    Signal,
    WatchedToken,
)
from app.db.session import engine, init_db
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
        trades = session.exec(select(PaperTrade).order_by(PaperTrade.id.desc()).limit(50)).all()
        risk_decisions = session.exec(select(RiskDecisionRecord).order_by(RiskDecisionRecord.id.desc()).limit(50)).all()
        risk_events = session.exec(select(RiskEvent).order_by(RiskEvent.id.desc()).limit(50)).all()
        perf_engine = PerformanceEngine(settings)
        perf_summary = perf_engine.summary(session)
        alpha_breakdown = perf_engine.alpha_breakdown(session)

    total_pnl = sum(t.pnl_xrp for t in trades)
    st.metric("Total Paper PnL (XRP)", f"{total_pnl:.4f}")

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
    st.dataframe(outcome_rows, use_container_width=True)

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

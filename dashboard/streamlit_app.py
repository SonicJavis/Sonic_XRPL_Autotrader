from __future__ import annotations

import streamlit as st
from sqlmodel import Session, select

from app.config import Settings
from app.db.models import AlphaSignal, MarketDepthLevel, MarketSnapshot, PaperTrade, RiskDecisionRecord, RiskEvent, Signal, WatchedToken
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
        trades = session.exec(select(PaperTrade).order_by(PaperTrade.id.desc()).limit(50)).all()
        risk_decisions = session.exec(select(RiskDecisionRecord).order_by(RiskDecisionRecord.id.desc()).limit(50)).all()
        risk_events = session.exec(select(RiskEvent).order_by(RiskEvent.id.desc()).limit(50)).all()

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

    st.subheader("Risk Decisions")
    st.dataframe([r.model_dump() for r in risk_decisions], use_container_width=True)

    st.subheader("Risk Events")
    st.dataframe([r.model_dump() for r in risk_events], use_container_width=True)


if __name__ == "__main__":
    main()

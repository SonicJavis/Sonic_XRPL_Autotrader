from __future__ import annotations

import streamlit as st
from sqlmodel import Session, select

from app.config import Settings
from app.db.models import MarketSnapshot, PaperTrade, RiskEvent, Signal, WatchedToken
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
        signals = session.exec(select(Signal).order_by(Signal.id.desc()).limit(50)).all()
        trades = session.exec(select(PaperTrade).order_by(PaperTrade.id.desc()).limit(50)).all()
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
        good_structure = latest.get("spread_pct", 999) <= settings.MAX_SPREAD_PCT and latest.get(
            "liquidity_xrp", 0
        ) >= settings.MIN_LIQUIDITY_XRP and latest.get("bid_count", 0) >= 2 and latest.get("ask_count", 0) >= 2
        style = "green" if good_structure else "red"
        label = "GOOD STRUCTURE" if good_structure else "BAD TOKEN STRUCTURE"
        st.markdown(f"<h4 style='color:{style}'>{label}</h4>", unsafe_allow_html=True)

        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Price (XRP)", f"{latest.get('price_xrp', 0):.6f}")
        m2.metric("Spread %", f"{latest.get('spread_pct', 0):.3f}")
        m3.metric("Liquidity (XRP)", f"{latest.get('liquidity_xrp', 0):.2f}")
        m4.metric("Best Bid / Ask", f"{latest.get('best_bid', 0):.6f} / {latest.get('best_ask', 0):.6f}")
        m5.metric("Order Count", str(latest.get("tx_count", 0)))

    st.subheader("Latest Signals")
    st.dataframe([s.model_dump() for s in signals], use_container_width=True)

    st.subheader("Paper Trades")
    st.dataframe([t.model_dump() for t in trades], use_container_width=True)

    st.subheader("Risk Events")
    st.dataframe([r.model_dump() for r in risk_events], use_container_width=True)


if __name__ == "__main__":
    main()

from __future__ import annotations

import streamlit as st
from sqlmodel import Session, select

from app.config import Settings
from app.db.models import PaperTrade, RiskEvent, Signal, Token
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
        tokens = session.exec(select(Token).order_by(Token.id.desc()).limit(50)).all()
        signals = session.exec(select(Signal).order_by(Signal.id.desc()).limit(50)).all()
        trades = session.exec(select(PaperTrade).order_by(PaperTrade.id.desc()).limit(50)).all()
        risk_events = session.exec(select(RiskEvent).order_by(RiskEvent.id.desc()).limit(50)).all()

    total_pnl = sum(t.pnl_xrp for t in trades)
    st.metric("Total Paper PnL (XRP)", f"{total_pnl:.4f}")

    st.subheader("Registered Tokens")
    st.dataframe([t.model_dump() for t in tokens], use_container_width=True)

    st.subheader("Latest Signals")
    st.dataframe([s.model_dump() for s in signals], use_container_width=True)

    st.subheader("Paper Trades")
    st.dataframe([t.model_dump() for t in trades], use_container_width=True)

    st.subheader("Risk Events")
    st.dataframe([r.model_dump() for r in risk_events], use_container_width=True)


if __name__ == "__main__":
    main()

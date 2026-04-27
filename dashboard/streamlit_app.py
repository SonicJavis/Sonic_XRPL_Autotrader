"""Streamlit dashboard for Sonic XRPL Autotrader."""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure the project root is on the path when running via `streamlit run`.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import streamlit as st
from sqlalchemy import col
from sqlmodel import Session, select

from app.config import settings
from app.db.models import PaperTrade, Signal
from app.db.session import engine, create_db_and_tables
from app.risk.kill_switch import is_kill_switch_active

# ── Page config ──────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Sonic XRPL Autotrader",
    page_icon="⚡",
    layout="wide",
)

create_db_and_tables()

# ── Header ────────────────────────────────────────────────────────────────────

st.title("⚡ Sonic XRPL Autotrader — Dashboard")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Bot Mode", settings.bot_mode)

with col2:
    live_label = "🟢 Enabled" if settings.live_trading_enabled else "🔴 Disabled"
    st.metric("Live Trading", live_label)

with col3:
    ks_active = is_kill_switch_active()
    ks_label = "🛑 ACTIVE" if ks_active else "✅ Inactive"
    st.metric("Kill Switch", ks_label)

if ks_active:
    st.error("⚠️ Kill switch is ACTIVE — all new trades are blocked.")

st.divider()

# ── Signals ───────────────────────────────────────────────────────────────────

st.subheader("📡 Recent Signals")

with Session(engine) as session:
    signals = session.exec(
        select(Signal).order_by(col(Signal.created_at).desc()).limit(50)
    ).all()

if signals:
    df_signals = pd.DataFrame(
        [
            {
                "ID": s.id,
                "Strategy": s.strategy_name,
                "Currency": s.currency,
                "Direction": s.direction,
                "Price (XRP)": s.price_xrp,
                "Confidence": s.confidence,
                "Created At": s.created_at,
            }
            for s in signals
        ]
    )
    st.dataframe(df_signals, use_container_width=True)
else:
    st.info("No signals yet. Run a scan cycle to generate signals.")

st.divider()

# ── Paper Trades ──────────────────────────────────────────────────────────────

st.subheader("📊 Paper Trades")

with Session(engine) as session:
    trades = session.exec(
        select(PaperTrade).order_by(col(PaperTrade.opened_at).desc()).limit(50)
    ).all()

if trades:
    df_trades = pd.DataFrame(
        [
            {
                "ID": t.id,
                "Currency": t.currency,
                "Direction": t.direction,
                "Entry (XRP)": t.entry_price_xrp,
                "Exit (XRP)": t.exit_price_xrp,
                "Size (XRP)": t.size_xrp,
                "P&L (XRP)": t.pnl_xrp,
                "Status": t.status,
                "Opened At": t.opened_at,
                "Closed At": t.closed_at,
            }
            for t in trades
        ]
    )
    st.dataframe(df_trades, use_container_width=True)

    open_trades = [t for t in trades if t.status == "OPEN"]
    total_pnl = sum(t.pnl_xrp or 0.0 for t in trades if t.pnl_xrp is not None)

    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Open Trades", len(open_trades))
    col_b.metric("Closed Trades", len(trades) - len(open_trades))
    col_c.metric("Total P&L (XRP)", f"{total_pnl:.4f}")
else:
    st.info("No paper trades yet.")

st.divider()
st.caption("Sonic XRPL Autotrader — paper trading mode. Not financial advice.")

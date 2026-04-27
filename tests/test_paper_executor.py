"""Tests for the PaperExecutor."""

from __future__ import annotations

import pytest
from sqlmodel import Session, SQLModel, create_engine

from app.db.models import PaperTrade
from app.execution.paper import PaperExecutor
from app.strategies.base import SignalPayload


@pytest.fixture
def mem_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture
def buy_signal():
    return SignalPayload(
        strategy_name="test",
        currency="SONIC",
        issuer="rHb9CJAWyB4rj91VRWn96DkukG4bwdtyTh",
        direction="BUY",
        price_xrp=0.01,
        confidence=0.9,
    )


def test_open_trade(mem_session, buy_signal):
    executor = PaperExecutor(mem_session)
    trade = executor.open_trade(buy_signal)
    assert trade.id is not None
    assert trade.status == "OPEN"
    assert trade.entry_price_xrp == 0.01
    assert trade.pnl_xrp is None


def test_close_trade_tp(mem_session, buy_signal):
    executor = PaperExecutor(mem_session)
    trade = executor.open_trade(buy_signal)
    # 20 % gain → take profit
    closed = executor.close_trade(trade, exit_price_xrp=0.012, reason="CLOSED_TP")
    assert closed.status == "CLOSED_TP"
    assert closed.pnl_xrp is not None
    assert closed.pnl_xrp > 0


def test_close_trade_sl(mem_session, buy_signal):
    executor = PaperExecutor(mem_session)
    trade = executor.open_trade(buy_signal)
    # Price drops 10 % → stop loss
    closed = executor.close_trade(trade, exit_price_xrp=0.009, reason="CLOSED_SL")
    assert closed.status == "CLOSED_SL"
    assert closed.pnl_xrp < 0


def test_tick_triggers_tp(mem_session, buy_signal):
    executor = PaperExecutor(mem_session)
    trade = executor.open_trade(buy_signal)
    # TP is 20 % above entry
    tp_price = buy_signal.price_xrp * 1.25
    updated = executor.tick(trade, tp_price)
    assert updated.status == "CLOSED_TP"


def test_tick_triggers_sl(mem_session, buy_signal):
    executor = PaperExecutor(mem_session)
    trade = executor.open_trade(buy_signal)
    # SL is 10 % below entry
    sl_price = buy_signal.price_xrp * 0.85
    updated = executor.tick(trade, sl_price)
    assert updated.status == "CLOSED_SL"


def test_tick_no_trigger(mem_session, buy_signal):
    executor = PaperExecutor(mem_session)
    trade = executor.open_trade(buy_signal)
    updated = executor.tick(trade, buy_signal.price_xrp * 1.05)
    assert updated.status == "OPEN"


def test_double_close_is_noop(mem_session, buy_signal):
    executor = PaperExecutor(mem_session)
    trade = executor.open_trade(buy_signal)
    closed = executor.close_trade(trade, 0.012, reason="CLOSED_TP")
    # Calling close again should be a no-op
    again = executor.close_trade(closed, 0.011, reason="CLOSED_MANUAL")
    assert again.status == "CLOSED_TP"

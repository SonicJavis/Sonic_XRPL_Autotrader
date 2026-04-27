"""Tests for risk rules and kill switch."""

from __future__ import annotations

from pathlib import Path

import pytest
from sqlmodel import Session, SQLModel, create_engine

from app.db.models import PaperTrade
from app.risk.kill_switch import assert_no_kill_switch, is_kill_switch_active
from app.risk.rules import RiskDenied, check_open_positions, check_position_size, run_all_checks


# ── In-memory DB fixture ──────────────────────────────────────────────────────

@pytest.fixture
def mem_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


# ── Position size ─────────────────────────────────────────────────────────────

def test_position_size_ok():
    check_position_size(4.0)  # under the 5 XRP default


def test_position_size_denied():
    with pytest.raises(RiskDenied):
        check_position_size(100.0)


# ── Open positions ────────────────────────────────────────────────────────────

def test_open_positions_ok(mem_session):
    check_open_positions(mem_session)


def test_open_positions_denied(mem_session):
    # Add 3 open trades (default max)
    for _ in range(3):
        trade = PaperTrade(
            request_id="test",
            currency="SONIC",
            issuer="rXXX",
            direction="BUY",
            entry_price_xrp=0.01,
            size_xrp=5.0,
            stop_loss_pct=0.10,
            take_profit_pct=0.20,
            status="OPEN",
        )
        mem_session.add(trade)
    mem_session.commit()

    with pytest.raises(RiskDenied):
        check_open_positions(mem_session)


# ── Kill switch ───────────────────────────────────────────────────────────────

def test_kill_switch_inactive(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert is_kill_switch_active() is False


def test_kill_switch_active(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "KILL_SWITCH").touch()
    assert is_kill_switch_active() is True


def test_assert_no_kill_switch_blocks(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "KILL_SWITCH").touch()
    with pytest.raises(RuntimeError, match="KILL_SWITCH"):
        assert_no_kill_switch()

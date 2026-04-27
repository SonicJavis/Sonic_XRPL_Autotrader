"""Tests for config.py."""

import pytest

from app.config import Settings


def test_default_bot_mode():
    s = Settings()
    assert s.bot_mode == "PAPER_TRADING"


def test_live_trading_disabled_by_default():
    s = Settings()
    assert s.live_trading_enabled is False
    assert s.is_paper_trading is True
    assert s.is_live_trading is False


def test_invalid_bot_mode_raises():
    with pytest.raises(Exception):
        Settings(bot_mode="INVALID_MODE")


def test_live_trading_gate():
    s = Settings(bot_mode="LIVE_TRADING", live_trading_enabled=True)
    assert s.is_live_trading is True
    assert s.is_paper_trading is False


def test_live_trading_requires_flag():
    # Even if bot_mode is LIVE_TRADING, the enabled flag blocks it
    s = Settings(bot_mode="LIVE_TRADING", live_trading_enabled=False)
    assert s.is_live_trading is False
    assert s.is_paper_trading is True

"""Tests for runtime modes."""

from __future__ import annotations

import os
import pytest
from sonic_xrpl.core.modes import (
    RuntimeMode,
    DEFAULT_MODE,
    ModeContext,
    get_current_mode,
)


def test_default_mode_is_intelligence_only():
    """Default mode must be INTELLIGENCE_ONLY."""
    assert DEFAULT_MODE == RuntimeMode.INTELLIGENCE_ONLY


def test_get_current_mode_default(monkeypatch):
    """get_current_mode() returns INTELLIGENCE_ONLY when env var is unset."""
    monkeypatch.delenv("SONIC_RUNTIME_MODE", raising=False)
    assert get_current_mode() == RuntimeMode.INTELLIGENCE_ONLY


def test_get_current_mode_from_env(monkeypatch):
    """get_current_mode() reads SONIC_RUNTIME_MODE env var."""
    monkeypatch.setenv("SONIC_RUNTIME_MODE", "simulation")
    assert get_current_mode() == RuntimeMode.SIMULATION


def test_get_current_mode_invalid_env(monkeypatch):
    """Invalid SONIC_RUNTIME_MODE falls back to INTELLIGENCE_ONLY."""
    monkeypatch.setenv("SONIC_RUNTIME_MODE", "not_a_real_mode")
    assert get_current_mode() == RuntimeMode.INTELLIGENCE_ONLY


def test_mode_context_defaults_to_intelligence_only(monkeypatch):
    """ModeContext without argument uses INTELLIGENCE_ONLY."""
    monkeypatch.delenv("SONIC_RUNTIME_MODE", raising=False)
    ctx = ModeContext()
    assert ctx.mode == RuntimeMode.INTELLIGENCE_ONLY


def test_mode_context_intelligence_cannot_create_intent():
    """INTELLIGENCE_ONLY mode cannot create intent."""
    ctx = ModeContext(RuntimeMode.INTELLIGENCE_ONLY)
    assert not ctx.can_create_intent()


def test_mode_context_simulation_can_create_intent():
    """SIMULATION mode can create intent."""
    ctx = ModeContext(RuntimeMode.SIMULATION)
    assert ctx.can_create_intent()


def test_mode_context_paper_can_create_intent():
    """PAPER mode can create intent."""
    ctx = ModeContext(RuntimeMode.PAPER)
    assert ctx.can_create_intent()


def test_mode_context_cannot_submit_any_mode():
    """No mode can submit in Phase 45."""
    for mode in RuntimeMode:
        ctx = ModeContext(mode)
        assert not ctx.can_submit(), f"Expected submit blocked for {mode}"

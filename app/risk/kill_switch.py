"""Kill-switch — blocks all new trades when KILL_SWITCH file is present.

Exits are always allowed regardless of kill-switch state.
"""

from __future__ import annotations

from pathlib import Path

from app.telemetry import get_logger

logger = get_logger("risk.kill_switch")

_KILL_SWITCH_PATH = Path("KILL_SWITCH")


def is_kill_switch_active() -> bool:
    """Return True if the KILL_SWITCH sentinel file exists."""
    active = _KILL_SWITCH_PATH.exists()
    if active:
        logger.warning("KILL SWITCH IS ACTIVE — all new trades are blocked")
    return active


def assert_no_kill_switch(request_id: str = "") -> None:
    """Raise RuntimeError if the kill switch is active.

    Exits / close operations should NOT call this — the kill switch
    only blocks new entry trades.
    """
    if is_kill_switch_active():
        logger.error(
            "Trade blocked by kill switch",
            request_id=request_id,
            kill_switch_path=str(_KILL_SWITCH_PATH.resolve()),
        )
        raise RuntimeError(
            "KILL_SWITCH file detected. All new trades are blocked. "
            "Remove the KILL_SWITCH file to resume trading."
        )

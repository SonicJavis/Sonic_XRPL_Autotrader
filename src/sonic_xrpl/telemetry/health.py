"""System health aggregation."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from sonic_xrpl.core.config import load_config
from sonic_xrpl.core.killswitch import PersistentKillSwitch
from sonic_xrpl.core.modes import RuntimeMode, get_current_mode
from sonic_xrpl.protocol.capability_matrix import get_enabled_capabilities


@dataclass
class SystemHealth:
    """Aggregated health snapshot of the V2 system."""

    mode: RuntimeMode
    enabled_capabilities: list[str]
    provider_count: int = 0
    live_trading_blocked: bool = True
    killswitch_active: bool = False
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    notes: list[str] = field(default_factory=list)


def get_system_health() -> SystemHealth:
    """Return a current system health snapshot."""
    mode = get_current_mode()
    cfg = load_config()
    killswitch = PersistentKillSwitch(cfg.killswitch_db_path)
    state = killswitch.get_state()
    killswitch.close()
    return SystemHealth(
        mode=mode,
        enabled_capabilities=get_enabled_capabilities(),
        live_trading_blocked=True,
        killswitch_active=state.is_active,
        notes=[
            "Phase 45 - V2 Foundation Architecture",
            f"Mode: {mode.value}",
            "Live trading: BLOCKED",
            f"Persistent killswitch: {'ACTIVE' if state.is_active else 'OFF'}",
        ],
    )

"""V2 configuration with safe offline defaults."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from sonic_xrpl.core.modes import RuntimeMode, get_current_mode
from security.secrets_loader import get_secret


@dataclass
class V2Config:
    """Central configuration for the V2 system."""

    mode: RuntimeMode = field(default_factory=get_current_mode)
    network: str = "mainnet"
    log_level: str = "INFO"
    dry_run: bool = True
    audit_dir: Path = field(default_factory=lambda: Path("docs/audit"))
    research_dir: Path = field(default_factory=lambda: Path("docs/research"))
    storage_path: Path = field(default_factory=lambda: Path("data/v2.db"))


def load_config() -> V2Config:
    """Load V2Config from environment variables with safe offline defaults."""
    return V2Config(
        mode=get_current_mode(),
        network=get_secret("SONIC_NETWORK", "mainnet"),
        log_level=get_secret("SONIC_LOG_LEVEL", "INFO"),
        dry_run=get_secret("SONIC_DRY_RUN", "true").lower() != "false",
        audit_dir=Path(get_secret("SONIC_AUDIT_DIR", "docs/audit")),
        research_dir=Path(get_secret("SONIC_RESEARCH_DIR", "docs/research")),
        storage_path=Path(get_secret("SONIC_STORAGE_PATH", "data/v2.db")),
    )

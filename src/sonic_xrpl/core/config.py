"""V2 configuration with safe offline defaults."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from sonic_xrpl.core.modes import RuntimeMode, get_current_mode


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
        network=os.environ.get("SONIC_NETWORK", "mainnet"),
        log_level=os.environ.get("SONIC_LOG_LEVEL", "INFO"),
        dry_run=os.environ.get("SONIC_DRY_RUN", "true").lower() != "false",
        audit_dir=Path(os.environ.get("SONIC_AUDIT_DIR", "docs/audit")),
        research_dir=Path(os.environ.get("SONIC_RESEARCH_DIR", "docs/research")),
        storage_path=Path(os.environ.get("SONIC_STORAGE_PATH", "data/v2.db")),
    )

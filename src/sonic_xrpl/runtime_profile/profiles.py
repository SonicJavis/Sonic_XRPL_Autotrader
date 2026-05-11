from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from app.config import Settings
from app.config.runtime_mode import build_runtime_profile
from sonic_xrpl.core.config import load_config
from sonic_xrpl.runtime_profile.ids import stable_id
from sonic_xrpl.runtime_profile.models import DETERMINISTIC_CREATED_AT, RuntimeProfile

PROFILE_NAMES = {"offline", "paper", "shadow", "research", "unknown"}
DEFAULT_ENV_KEYS = (
    "SONIC_RUNTIME_MODE",
    "SONIC_DRY_RUN",
    "EXECUTION_ENABLED",
    "LIVE_TRADING_ENABLED",
    "SONIC_STORAGE_PATH",
)


def _as_bool(value: str | bool | None, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _profile_name_from_env(env: dict[str, str]) -> str:
    mode = str(env.get("SONIC_RUNTIME_MODE", "")).strip().lower()
    if mode in PROFILE_NAMES:
        return mode
    if mode in {"intelligence_only", "simulation", "live_readiness", "live"}:
        return "research"
    if not mode:
        return "unknown"
    return "unknown"


def _profile_capabilities(profile_name: str) -> dict[str, bool]:
    defaults = {
        "allows_network_reads": False,
        "allows_runtime_writes": False,
        "allows_execution": False,
        "allows_signing": False,
        "allows_submission": False,
        "allows_wallet_material": False,
        "allows_dashboard_mutation": False,
        "allows_calibration_mutation": False,
        "requires_human_review": True,
        "paper_only": True,
        "dry_run": True,
        "live_execution_allowed": False,
    }
    if profile_name == "paper":
        return {**defaults, "allows_network_reads": True}
    if profile_name == "shadow":
        return {**defaults, "allows_network_reads": True}
    if profile_name == "research":
        return {**defaults, "allows_network_reads": True, "paper_only": False}
    if profile_name == "offline":
        return defaults
    return defaults


def _build_env_snapshot(explicit_env: dict[str, str] | None = None) -> dict[str, str]:
    env = explicit_env if explicit_env is not None else dict(os.environ)
    snapshot: dict[str, str] = {}
    for key in DEFAULT_ENV_KEYS:
        snapshot[key] = str(env.get(key, ""))
    return snapshot


def _infer_source_refs() -> tuple[str, ...]:
    refs = [
        "app/config/__init__.py",
        "app/config/runtime_mode.py",
        "src/sonic_xrpl/core/config.py",
        "deploy/paper-runtime.env",
        "docker-compose.yml",
    ]
    return tuple(refs)


def _runtime_policies(profile_name: str, capabilities: dict[str, bool]) -> tuple[str, str]:
    if profile_name in {"paper", "shadow", "research"} and capabilities["allows_network_reads"]:
        network_policy = "network_reads_allowed_without_live_submission"
    elif profile_name == "offline":
        network_policy = "offline_only"
    else:
        network_policy = "unknown_profile_network_policy"
    runtime_write_policy = "runtime_mutation_blocked"
    return network_policy, runtime_write_policy


def build_runtime_profile_snapshot(
    *,
    env: dict[str, str] | None = None,
    created_at: str = DETERMINISTIC_CREATED_AT,
    source: str = "phase57_runtime_profile",
) -> RuntimeProfile:
    env_snapshot = _build_env_snapshot(env)
    profile_name = _profile_name_from_env(env_snapshot)
    caps = _profile_capabilities(profile_name)

    execution_enabled = _as_bool(env_snapshot.get("EXECUTION_ENABLED"), default=False)
    live_trading_enabled = _as_bool(env_snapshot.get("LIVE_TRADING_ENABLED"), default=False)
    dry_run = _as_bool(env_snapshot.get("SONIC_DRY_RUN"), default=True)
    network_policy, runtime_write_policy = _runtime_policies(profile_name, caps)

    limitations: list[str] = []
    warnings: list[str] = []

    if profile_name == "unknown":
        warnings.append("runtime_mode_unknown")
    if profile_name == "paper" and not dry_run:
        warnings.append("paper_profile_without_dry_run")
    if execution_enabled or live_trading_enabled:
        warnings.append("unsafe_execution_flags_present")
    if not env_snapshot.get("SONIC_STORAGE_PATH"):
        limitations.append("storage_path_missing")

    # Reference current app/v2 config surface for conformance visibility only.
    try:
        app_settings = Settings()
        app_profile = build_runtime_profile(app_settings)
        if app_profile.execution_enabled:
            warnings.append("app_runtime_profile_execution_enabled")
    except Exception:
        limitations.append("app_runtime_profile_unavailable")
    try:
        _ = load_config()
    except Exception:
        limitations.append("v2_config_unavailable")

    safety_statement = (
        "Phase 57 runtime profile is advisory/read-only. "
        "Live execution remains blocked. No signing, submission, wallet material, "
        "dashboard mutation, or calibration mutation is allowed."
    )
    profile_id = stable_id(
        "rp57",
        profile_name,
        env_snapshot.get("SONIC_RUNTIME_MODE", ""),
        env_snapshot.get("SONIC_DRY_RUN", ""),
        env_snapshot.get("EXECUTION_ENABLED", ""),
        env_snapshot.get("LIVE_TRADING_ENABLED", ""),
    )
    return RuntimeProfile(
        profile_id=profile_id,
        profile_name=profile_name,
        created_at=created_at,
        source=source,
        source_refs=_infer_source_refs(),
        paper_only=caps["paper_only"],
        dry_run=dry_run and caps["dry_run"],
        live_execution_allowed=False,
        execution_enabled=execution_enabled,
        signing_allowed=False,
        submission_allowed=False,
        wallet_material_allowed=False,
        dashboard_mutation_allowed=False,
        calibration_mutation_allowed=False,
        human_review_required=True,
        network_read_policy=network_policy,
        runtime_write_policy=runtime_write_policy,
        safety_statement=safety_statement,
        limitations=tuple(dict.fromkeys(limitations)),
        warnings=tuple(dict.fromkeys(warnings)),
        allows_network_reads=caps["allows_network_reads"],
        allows_runtime_writes=False,
        allows_execution=False,
        allows_signing=False,
        allows_submission=False,
        allows_wallet_material=False,
        allows_dashboard_mutation=False,
        allows_calibration_mutation=False,
        requires_human_review=True,
        env_snapshot=env_snapshot,
    )


def load_env_file(path: str | Path) -> dict[str, str]:
    env: dict[str, str] = {}
    file_path = Path(path)
    if not file_path.exists():
        return env
    for line in file_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        env[key.strip()] = value.strip()
    return env

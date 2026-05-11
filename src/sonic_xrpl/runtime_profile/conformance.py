from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from app.config import Settings
from sonic_xrpl.core.config import load_config
from sonic_xrpl.runtime_profile.ids import stable_id
from sonic_xrpl.runtime_profile.models import (
    DETERMINISTIC_CREATED_AT,
    FAIL,
    PASS,
    REVIEW,
    ConformanceCheck,
    RuntimeProfile,
    RuntimeProfileConformance,
)
from sonic_xrpl.runtime_profile.profiles import build_runtime_profile_snapshot, load_env_file


def _as_bool(value: str | bool | None, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _check(check_id: str, status: str, message: str, evidence: list[str]) -> ConformanceCheck:
    return ConformanceCheck(
        check_id=check_id,
        status=status,
        message=message,
        evidence=tuple(evidence),
    )


def _live_trading_disabled(profile: RuntimeProfile) -> ConformanceCheck:
    if _as_bool(profile.env_snapshot.get("LIVE_TRADING_ENABLED"), False):
        return _check("live_trading_disabled", FAIL, "LIVE_TRADING_ENABLED=true", ["env:LIVE_TRADING_ENABLED"])
    return _check("live_trading_disabled", PASS, "Live trading remains disabled", ["env:LIVE_TRADING_ENABLED=false"])


def _execution_disabled(profile: RuntimeProfile) -> ConformanceCheck:
    if _as_bool(profile.env_snapshot.get("EXECUTION_ENABLED"), False):
        return _check("execution_disabled", FAIL, "EXECUTION_ENABLED=true", ["env:EXECUTION_ENABLED"])
    return _check("execution_disabled", PASS, "Execution remains disabled", ["env:EXECUTION_ENABLED=false"])


def _dry_run_enabled_for_paper(profile: RuntimeProfile) -> ConformanceCheck:
    if profile.profile_name != "paper":
        return _check("dry_run_enabled_for_paper", REVIEW, "Profile is not paper; dry-run paper check not strict", [f"profile:{profile.profile_name}"])
    if not _as_bool(profile.env_snapshot.get("SONIC_DRY_RUN"), False):
        return _check("dry_run_enabled_for_paper", FAIL, "Paper profile requires SONIC_DRY_RUN=true", ["env:SONIC_DRY_RUN"])
    return _check("dry_run_enabled_for_paper", PASS, "Paper profile is dry-run", ["env:SONIC_DRY_RUN=true"])


def _no_wallet_material_allowed(profile: RuntimeProfile) -> ConformanceCheck:
    if profile.wallet_material_allowed or profile.allows_wallet_material:
        return _check("no_wallet_material_allowed", FAIL, "Wallet material is allowed by profile", ["profile:wallet_material_allowed=true"])
    return _check("no_wallet_material_allowed", PASS, "Wallet material remains blocked", ["profile:wallet_material_allowed=false"])


def _dashboard_read_only(profile: RuntimeProfile) -> ConformanceCheck:
    if profile.dashboard_mutation_allowed or profile.allows_dashboard_mutation:
        return _check("dashboard_read_only", FAIL, "Dashboard mutation is allowed", ["profile:dashboard_mutation_allowed=true"])
    return _check("dashboard_read_only", PASS, "Dashboard remains read-only", ["profile:dashboard_mutation_allowed=false"])


def _calibration_non_mutating(profile: RuntimeProfile) -> ConformanceCheck:
    if profile.calibration_mutation_allowed or profile.allows_calibration_mutation:
        return _check("calibration_non_mutating", FAIL, "Calibration mutation is allowed", ["profile:calibration_mutation_allowed=true"])
    return _check("calibration_non_mutating", PASS, "Calibration mutation remains blocked", ["profile:calibration_mutation_allowed=false"])


def _app_v2_profile_alignment() -> ConformanceCheck:
    evidence: list[str] = []
    try:
        app_settings = Settings()
        app_exec = bool(app_settings.EXECUTION_ENABLED)
        app_live = bool(app_settings.LIVE_TRADING_ENABLED)
        evidence.append(f"app:EXECUTION_ENABLED={str(app_exec).lower()}")
        evidence.append(f"app:LIVE_TRADING_ENABLED={str(app_live).lower()}")
    except Exception:
        return _check("app_v2_profile_alignment", REVIEW, "App settings unavailable", ["app:unavailable"])

    try:
        v2_cfg = load_config()
        evidence.append(f"v2:mode={v2_cfg.mode.value}")
        evidence.append(f"v2:dry_run={str(v2_cfg.dry_run).lower()}")
    except Exception:
        return _check("app_v2_profile_alignment", REVIEW, "V2 config unavailable", evidence + ["v2:unavailable"])

    if app_exec or app_live:
        return _check("app_v2_profile_alignment", FAIL, "App runtime enables execution/live trading", evidence)
    return _check("app_v2_profile_alignment", PASS, "App and V2 align on fail-closed execution flags", evidence)


def _docker_profile_alignment(docker_env_path: Path = Path("deploy/paper-runtime.env")) -> ConformanceCheck:
    if docker_env_path.exists():
        env = load_env_file(docker_env_path)
        evidence = [f"docker:{docker_env_path}"]
    else:
        # Container/runtime fallback: evaluate explicit env evidence when env file is not shipped.
        env = dict(os.environ)
        evidence = [f"docker:{docker_env_path}:missing", "docker:env_fallback"]

    live = _as_bool(env.get("LIVE_TRADING_ENABLED"), False)
    execution = _as_bool(env.get("EXECUTION_ENABLED"), False)
    dry_run = _as_bool(env.get("SONIC_DRY_RUN"), False)
    mode = str(env.get("SONIC_RUNTIME_MODE", "")).strip().lower()

    evidence.extend(
        [
            f"LIVE_TRADING_ENABLED={str(live).lower()}",
            f"EXECUTION_ENABLED={str(execution).lower()}",
            f"SONIC_DRY_RUN={str(dry_run).lower()}",
            f"SONIC_RUNTIME_MODE={mode or 'missing'}",
        ]
    )
    if live or execution:
        return _check("docker_profile_alignment", FAIL, "Docker profile enables live/execution flags", evidence)
    if mode != "paper" or not dry_run:
        return _check("docker_profile_alignment", REVIEW, "Docker profile missing strict paper/dry-run values", evidence)
    return _check("docker_profile_alignment", PASS, "Docker profile aligns with paper-only fail-closed defaults", evidence)


def evaluate_runtime_profile_conformance(
    *,
    env: dict[str, str] | None = None,
    created_at: str = DETERMINISTIC_CREATED_AT,
) -> RuntimeProfileConformance:
    profile = build_runtime_profile_snapshot(env=env if env is not None else dict(os.environ), created_at=created_at)
    checks = (
        _live_trading_disabled(profile),
        _execution_disabled(profile),
        _dry_run_enabled_for_paper(profile),
        _no_wallet_material_allowed(profile),
        _dashboard_read_only(profile),
        _calibration_non_mutating(profile),
        _app_v2_profile_alignment(),
        _docker_profile_alignment(),
    )
    statuses = {check.status for check in checks}
    if FAIL in statuses:
        overall = FAIL
    elif REVIEW in statuses:
        overall = REVIEW
    else:
        overall = PASS

    drift_findings: list[str] = []
    blockers: list[str] = []
    warnings: list[str] = []
    for check in checks:
        if check.status == FAIL:
            blockers.append(f"{check.check_id}:{check.message}")
            drift_findings.append(f"{check.check_id}:unsafe")
        elif check.status == REVIEW:
            warnings.append(f"{check.check_id}:{check.message}")
            drift_findings.append(f"{check.check_id}:incomplete_evidence")

    conformance_id = stable_id(
        "rpc57",
        profile.profile_id,
        overall,
        tuple(check.status for check in checks),
    )
    return RuntimeProfileConformance(
        conformance_id=conformance_id,
        created_at=created_at,
        profile_name=profile.profile_name,
        status=overall,
        checks=checks,
        drift_findings=tuple(drift_findings),
        blockers=tuple(blockers),
        warnings=tuple(warnings),
        source_refs=profile.source_refs,
        paper_only=True,
        live_execution_allowed=False,
        runtime_mutation_allowed=False,
    )

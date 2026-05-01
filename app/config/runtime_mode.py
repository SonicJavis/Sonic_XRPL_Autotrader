from __future__ import annotations

from dataclasses import dataclass

from app.config import Settings


VALID_ENV_MODES = {"LOCAL_DEV", "STAGING", "PRODUCTION"}


@dataclass(frozen=True, slots=True)
class RuntimeSecurityProfile:
    mode: str
    auth_required: bool
    allowed_origins: tuple[str, ...]
    debug: bool
    execution_enabled: bool
    replay_enabled: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "mode": self.mode,
            "auth_required": self.auth_required,
            "allowed_origins": list(self.allowed_origins),
            "debug": self.debug,
            "execution_enabled": False,
            "replay_enabled": self.replay_enabled,
            "validated_data_only": True,
            "is_executable": False,
        }


def build_runtime_profile(settings: Settings) -> RuntimeSecurityProfile:
    mode = str(settings.ENV_MODE or "LOCAL_DEV").upper()
    if mode not in VALID_ENV_MODES:
        mode = "LOCAL_DEV"
    origins = _parse_origins(settings.ALLOWED_ORIGINS)
    return RuntimeSecurityProfile(
        mode=mode,
        auth_required=mode in {"STAGING", "PRODUCTION"},
        allowed_origins=origins,
        debug=bool(settings.DEBUG),
        execution_enabled=False,
        replay_enabled=str(settings.XRPL_INGESTION_MODE).lower() == "replay"
        or str(settings.XRPL_SHADOW_SOURCE).lower() == "replay",
    )


def validate_runtime_or_raise(settings: Settings) -> RuntimeSecurityProfile:
    if str(settings.ENV_MODE or "").upper() not in VALID_ENV_MODES:
        raise RuntimeError("Unsafe runtime: ENV_MODE must be LOCAL_DEV, STAGING, or PRODUCTION")
    profile = build_runtime_profile(settings)
    if bool(settings.EXECUTION_ENABLED) or bool(settings.LIVE_TRADING_ENABLED):
        raise RuntimeError("Unsafe runtime: execution flags must remain disabled")
    if profile.mode == "PRODUCTION":
        if profile.debug:
            raise RuntimeError("Unsafe production runtime: DEBUG must be false")
        token = settings.API_AUTH_TOKEN.get_secret_value() if settings.API_AUTH_TOKEN else ""
        if not token:
            raise RuntimeError("Unsafe production runtime: API_AUTH_TOKEN is required")
        if not profile.allowed_origins or "*" in profile.allowed_origins:
            raise RuntimeError("Unsafe production runtime: wildcard CORS is forbidden")
        if profile.replay_enabled:
            raise RuntimeError("Unsafe production runtime: replay sources are disabled")
    return profile


def _parse_origins(raw: str) -> tuple[str, ...]:
    return tuple(sorted({item.strip() for item in str(raw or "").split(",") if item.strip()}))

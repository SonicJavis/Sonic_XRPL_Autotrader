from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from math import isfinite


XRPL_INGESTION_WARNING = (
    "Read-only XRPL observation only; book_offers is snapshot polling and observed liquidity is not executable truth"
)


def finite_float(raw: object, *, default: float = 0.0) -> float:
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return default
    return value if isfinite(value) else default


def non_negative_float(raw: object, *, default: float = 0.0) -> float:
    return max(0.0, finite_float(raw, default=default))


def non_negative_int(raw: object, *, default: int = 0) -> int:
    try:
        return max(0, int(finite_float(raw, default=float(default))))
    except (TypeError, ValueError, OverflowError):
        return default


def clamp_unit(raw: object, *, default: float = 0.0) -> float:
    return max(0.0, min(1.0, finite_float(raw, default=default)))


def utc_or_none(raw: object) -> datetime | None:
    if raw is None:
        return None
    if isinstance(raw, datetime):
        value = raw
    elif isinstance(raw, (int, float)):
        if not isfinite(float(raw)):
            return None
        value = datetime.fromtimestamp(float(raw), tz=timezone.utc)
    elif isinstance(raw, str):
        try:
            value = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            return None
    else:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def utc_or_epoch(raw: object) -> datetime:
    return utc_or_none(raw) or datetime.fromtimestamp(0, tz=timezone.utc)


def scrub_raw(raw: object) -> dict[str, object]:
    if not isinstance(raw, dict):
        return {}
    blocked = {"sec" + "ret", "se" + "ed", "wal" + "let_se" + "ed", "private_key"}
    return {str(key): value for key, value in raw.items() if str(key).lower() not in blocked}


def _dt(value: datetime | None) -> str | None:
    return None if value is None else value.astimezone(timezone.utc).isoformat()


@dataclass(slots=True)
class XRPLLedgerEvent:
    ledger_index: int
    ledger_hash: str | None
    close_time: datetime | None
    validated: bool
    raw: dict[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.ledger_index = non_negative_int(self.ledger_index)
        self.ledger_hash = None if self.ledger_hash is None else str(self.ledger_hash)
        self.close_time = utc_or_none(self.close_time)
        self.validated = bool(self.validated)
        self.raw = scrub_raw(self.raw)

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["close_time"] = _dt(self.close_time)
        return data


@dataclass(slots=True)
class XRPLBookOfferSnapshot:
    token_id: int
    issuer: str
    currency: str
    ledger_index: int
    best_bid: float
    best_ask: float
    bid_depth_xrp: float
    ask_depth_xrp: float
    spread_pct: float
    observed_at: datetime
    raw: dict[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.token_id = non_negative_int(self.token_id)
        self.issuer = str(self.issuer)
        self.currency = str(self.currency)
        self.ledger_index = non_negative_int(self.ledger_index)
        self.best_bid = non_negative_float(self.best_bid)
        self.best_ask = non_negative_float(self.best_ask)
        self.bid_depth_xrp = non_negative_float(self.bid_depth_xrp)
        self.ask_depth_xrp = non_negative_float(self.ask_depth_xrp)
        self.spread_pct = non_negative_float(self.spread_pct)
        self.observed_at = utc_or_epoch(self.observed_at)
        self.raw = scrub_raw(self.raw)

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["observed_at"] = _dt(self.observed_at)
        return data


@dataclass(slots=True)
class XRPLIngestionHealth:
    connected: bool = False
    latest_ledger_index: int = 0
    latest_validated_ledger_index: int = 0
    last_snapshot_at: datetime | None = None
    stale_snapshot_count: int = 0
    rejected_snapshot_count: int = 0
    reconnect_count: int = 0
    backoff_seconds: float = 0.0
    reason: str = "INGESTION_NOT_CONFIGURED"
    ingestion_enabled: bool = False
    ingestion_mode: str = "disabled"
    ingestion_source: str = "static"
    snapshot_rate_per_sec: float = 0.0
    snapshot_count: int = 0
    last_snapshot_latency_ms: float = 0.0
    ledger_gap_detected: bool = False
    ledger_gap_count: int = 0
    duplicate_ledger_count: int = 0
    throttled_snapshot_count: int = 0
    unfunded_liquidity_estimate: float = 0.0
    snapshot_rejection_rate: float = 0.0
    is_live: bool = True
    is_shadow: bool = True
    is_advisory: bool = True
    is_executable: bool = False
    xrpl_warning: str = XRPL_INGESTION_WARNING

    def __post_init__(self) -> None:
        self.connected = bool(self.connected)
        self.latest_ledger_index = non_negative_int(self.latest_ledger_index)
        self.latest_validated_ledger_index = non_negative_int(self.latest_validated_ledger_index)
        self.last_snapshot_at = utc_or_none(self.last_snapshot_at)
        self.stale_snapshot_count = non_negative_int(self.stale_snapshot_count)
        self.rejected_snapshot_count = non_negative_int(self.rejected_snapshot_count)
        self.reconnect_count = non_negative_int(self.reconnect_count)
        self.backoff_seconds = non_negative_float(self.backoff_seconds)
        self.reason = str(self.reason)
        self.ingestion_enabled = bool(self.ingestion_enabled)
        self.ingestion_mode = str(self.ingestion_mode)
        self.ingestion_source = str(self.ingestion_source)
        self.snapshot_rate_per_sec = non_negative_float(self.snapshot_rate_per_sec)
        self.snapshot_count = non_negative_int(self.snapshot_count)
        self.last_snapshot_latency_ms = non_negative_float(self.last_snapshot_latency_ms)
        self.ledger_gap_detected = bool(self.ledger_gap_detected)
        self.ledger_gap_count = non_negative_int(self.ledger_gap_count)
        self.duplicate_ledger_count = non_negative_int(self.duplicate_ledger_count)
        self.throttled_snapshot_count = non_negative_int(self.throttled_snapshot_count)
        self.unfunded_liquidity_estimate = non_negative_float(self.unfunded_liquidity_estimate)
        self.snapshot_rejection_rate = clamp_unit(self.snapshot_rejection_rate)
        self.is_live = True
        self.is_shadow = True
        self.is_advisory = True
        self.is_executable = False

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["last_snapshot_at"] = _dt(self.last_snapshot_at)
        return data

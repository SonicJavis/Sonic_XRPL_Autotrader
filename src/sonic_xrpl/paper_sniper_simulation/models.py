from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from sonic_xrpl.firstledger_intelligence.models import FirstLedgerIntelligenceResult


class SimulationDecision(str, Enum):
    SIMULATED = "SIMULATED"
    SIMULATION_REJECTED = "SIMULATION_REJECTED"


class FillAssumptionLabel(str, Enum):
    FILLED = "FILLED"
    PARTIAL_FILL = "PARTIAL_FILL"
    NO_FILL = "NO_FILL"
    REJECTED = "REJECTED"


@dataclass(frozen=True)
class PaperSniperScenario:
    candidate_id: str
    allow_watch_entry: bool = False
    allow_missing_holder_simulation: bool = False
    stale_policy: str = "reduce_confidence"
    entry_price_xrp: float | None = None
    exit_price_xrp: float | None = None
    slippage_bps_assumption: int = 50
    latency_seconds_assumption: int = 4
    ledger_window_seconds_assumption: int = 10
    liquidity_available_pct_assumption: float | None = 1.0
    outcome_window: str = "5m"
    notes: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class FillAssumption:
    label: FillAssumptionLabel
    fill_ratio: float
    no_fill_reason: str
    partial_fill_reason: str
    slippage_bps_assumption: int
    latency_seconds_assumption: int
    ledger_window_seconds_assumption: int
    liquidity_available_pct_assumption: float | None
    assumption_only: bool = True


@dataclass(frozen=True)
class PaperOutcomeSummary:
    outcome_window: str
    assumed_entry_price_xrp: float | None
    assumed_exit_price_xrp: float | None
    assumed_return_bps: float | None
    assumed_pnl_xrp: float | None
    outcome_is_assumption: bool = True
    real_pnl: bool = False


@dataclass(frozen=True)
class PaperSniperSimulationResult:
    candidate_id: str
    issuer: str
    symbol: str
    intelligence_verdict: str
    simulation_decision: SimulationDecision
    fill_assumption: FillAssumption
    outcome: PaperOutcomeSummary
    rejection_reasons: tuple[str, ...]
    risk_notes: tuple[str, ...]
    provenance_notes: tuple[str, ...]
    limitations: tuple[str, ...]
    paper_only: bool = True
    review_only: bool = True
    live_execution_allowed: bool = False
    transaction_created: bool = False
    order_created: bool = False


@dataclass(frozen=True)
class PaperSniperSimulationReport:
    report_id: str
    generated_at: str
    total_candidates: int
    simulated_candidates: int
    rejected_candidates: int
    no_fill_candidates: int
    partial_fill_candidates: int
    by_decision: dict[str, int]
    results: tuple[PaperSniperSimulationResult, ...]
    paper_only: bool = True
    review_only: bool = True
    live_execution_allowed: bool = False


@dataclass(frozen=True)
class PaperSniperBatch:
    intelligence_fixture: str
    intelligence_results: tuple[FirstLedgerIntelligenceResult, ...]
    scenarios: tuple[PaperSniperScenario, ...]


def jsonable(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if hasattr(value, "__dataclass_fields__"):
        return {
            key: jsonable(getattr(value, key))
            for key in value.__dataclass_fields__
        }
    if isinstance(value, dict):
        return {str(key): jsonable(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [jsonable(item) for item in value]
    if isinstance(value, list):
        return [jsonable(item) for item in value]
    return value

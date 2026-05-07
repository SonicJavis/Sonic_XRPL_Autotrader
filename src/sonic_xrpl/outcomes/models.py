from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class OutcomeLabel(str, Enum):
    WIN = "WIN"
    LOSS = "LOSS"
    FLAT = "FLAT"
    NO_OBSERVATION = "NO_OBSERVATION"


@dataclass(frozen=True)
class PaperOutcomeObservation:
    observation_id: str
    candidate_id: str
    signal_id: str
    window: str
    observed_at: str
    entry_price_xrp: float | None
    exit_price_xrp: float | None
    baseline_exit_price_xrp: float | None
    liquidity_score: int | None
    evidence_quality: str
    source_fixture: str
    limitations: tuple[str, ...] = field(default_factory=tuple)
    paper_only: bool = True
    live_execution_allowed: bool = False


@dataclass(frozen=True)
class PaperOutcomeAttribution:
    attribution_id: str
    candidate_id: str
    signal_id: str
    signal_type: str
    window: str
    outcome_label: OutcomeLabel
    observed_return_bps: float | None
    baseline_return_bps: float | None
    excess_return_bps: float | None
    confidence_score_at_signal: int
    risk_score_at_signal: int
    attribution_reason_codes: tuple[str, ...]
    limitations: tuple[str, ...] = field(default_factory=tuple)
    paper_only: bool = True
    live_execution_allowed: bool = False


@dataclass(frozen=True)
class SignalFeedbackBucket:
    signal_type: str
    count: int
    wins: int
    losses: int
    flats: int
    missing_observations: int
    average_observed_return_bps: float | None
    average_excess_return_bps: float | None


@dataclass(frozen=True)
class SignalFeedbackSummary:
    feedback_id: str
    generated_at: str
    total_attributed: int
    wins: int
    losses: int
    flats: int
    missing_observations: int
    average_observed_return_bps: float | None
    average_excess_return_bps: float | None
    by_signal_type: dict[str, SignalFeedbackBucket]
    recommendations: tuple[str, ...]
    limitations: tuple[str, ...] = field(default_factory=tuple)
    paper_only: bool = True
    live_execution_allowed: bool = False

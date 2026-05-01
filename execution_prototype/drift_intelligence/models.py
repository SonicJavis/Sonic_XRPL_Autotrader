from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

@dataclass(frozen=True, slots=True)
class DriftTrend:
    drift_flag: str
    total_occurrences: int
    occurrences_per_run: List[int]
    normalized_rate_per_run: List[float]
    trend_direction: str # increasing | stable | decreasing | INSUFFICIENT_TREND_DATA
    slope_score: float
    confidence: str # low | medium | high
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "drift_flag": self.drift_flag,
            "total_occurrences": self.total_occurrences,
            "occurrences_per_run": self.occurrences_per_run,
            "normalized_rate_per_run": self.normalized_rate_per_run,
            "trend_direction": self.trend_direction,
            "slope_score": self.slope_score,
            "confidence": self.confidence
        }

@dataclass(frozen=True, slots=True)
class ConfidenceDecay:
    metric: str
    previous_value: float
    current_value: float
    decay_rate: float
    decay_flag: bool
    metadata_dependency: bool
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric": self.metric,
            "previous_value": self.previous_value,
            "current_value": self.current_value,
            "decay_rate": self.decay_rate,
            "decay_flag": self.decay_flag,
            "metadata_dependency": self.metadata_dependency
        }

@dataclass(frozen=True, slots=True)
class ReplayRecord:
    reconciliation_id: str
    replay_hash: str
    deterministic_match: bool
    deviation_type: str # non_deterministic_output | missing_input_dependency | metadata_dependency_shift | none
    notes: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "reconciliation_id": self.reconciliation_id,
            "replay_hash": self.replay_hash,
            "deterministic_match": self.deterministic_match,
            "deviation_type": self.deviation_type,
            "notes": self.notes
        }

@dataclass(frozen=True, slots=True)
class EarlyWarning:
    warning_id: str
    type: str # drift_acceleration | metadata_collapse | validation_gap | false_confidence | matching_integrity
    severity: str # low | medium | high | critical
    description: str
    evidence: str
    recommended_human_action: str
    prohibited_auto_action: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "warning_id": self.warning_id,
            "type": self.type,
            "severity": self.severity,
            "description": self.description,
            "evidence": self.evidence,
            "recommended_human_action": self.recommended_human_action,
            "prohibited_auto_action": self.prohibited_auto_action
        }

@dataclass(frozen=True, slots=True)
class DriftSummary:
    schema_version: str
    generated_at: str
    total_runs_analyzed: int
    start_run_hash: str
    end_run_hash: str
    active_warnings_count: int
    system_degrading: bool
    safety_statement: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "generated_at": self.generated_at,
            "total_runs_analyzed": self.total_runs_analyzed,
            "start_run_hash": self.start_run_hash,
            "end_run_hash": self.end_run_hash,
            "active_warnings_count": self.active_warnings_count,
            "system_degrading": self.system_degrading,
            "safety_statement": self.safety_statement
        }

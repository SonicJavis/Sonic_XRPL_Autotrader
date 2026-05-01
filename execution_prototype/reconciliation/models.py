from dataclasses import dataclass, field
from typing import Optional, List

@dataclass(frozen=True, slots=True)
class SimulationRecord:
    simulation_id: str
    intent_id: str
    expected_tx_type: str
    expected_status: str
    source_path: str
    raw_hash: str
    created_at: str
    session_id: Optional[str] = None
    expected_fee_drops: Optional[int] = None
    expected_validation_ledger: Optional[int] = None
    expected_fill_amount: Optional[str] = None
    expected_fill_pct: Optional[float] = None
    expected_avg_price: Optional[float] = None
    expected_slippage: Optional[float] = None

@dataclass(frozen=True, slots=True)
class LifecycleRecord:
    session_id: str
    actual_status: str
    source_path: str
    raw_hash: str
    intent_id: Optional[str] = None
    payload_uuid: Optional[str] = None
    tx_hash: Optional[str] = None
    created_at: Optional[str] = None
    signed_at: Optional[str] = None
    submitted_at: Optional[str] = None
    validated_at: Optional[str] = None
    actual_fee_drops: Optional[int] = None
    actual_validation_ledger: Optional[int] = None
    actual_result_code: Optional[str] = None
    actual_validated: Optional[bool] = None
    actual_delivered_amount: Optional[str] = None
    actual_slippage: Optional[float] = None
    has_metadata: bool = False

@dataclass(frozen=True, slots=True)
class ReconciliationRecord:
    reconciliation_id: str
    schema_version: str
    simulation_id: str
    compared_at: str
    match_status: str
    expected_status: str
    actual_status: str
    status_match: bool
    source_simulation_hash: str
    source_lifecycle_hash: str
    drift_flags: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)
    intent_id: Optional[str] = None
    session_id: Optional[str] = None
    tx_hash: Optional[str] = None
    fee_expected_drops: Optional[int] = None
    fee_actual_drops: Optional[int] = None
    fee_delta_drops: Optional[int] = None
    validation_ledger_expected: Optional[int] = None
    validation_ledger_actual: Optional[int] = None
    validation_ledger_delta: Optional[int] = None
    expected_fill_amount: Optional[str] = None
    actual_delivered_amount: Optional[str] = None
    fill_delta: Optional[float] = None
    expected_slippage: Optional[float] = None
    actual_slippage: Optional[float] = None
    slippage_delta: Optional[float] = None

    def to_dict(self) -> dict:
        return {
            "reconciliation_id": self.reconciliation_id,
            "schema_version": self.schema_version,
            "simulation_id": self.simulation_id,
            "intent_id": self.intent_id,
            "session_id": self.session_id,
            "tx_hash": self.tx_hash,
            "compared_at": self.compared_at,
            "match_status": self.match_status,
            "fee_expected_drops": self.fee_expected_drops,
            "fee_actual_drops": self.fee_actual_drops,
            "fee_delta_drops": self.fee_delta_drops,
            "validation_ledger_expected": self.validation_ledger_expected,
            "validation_ledger_actual": self.validation_ledger_actual,
            "validation_ledger_delta": self.validation_ledger_delta,
            "expected_status": self.expected_status,
            "actual_status": self.actual_status,
            "status_match": self.status_match,
            "expected_fill_amount": self.expected_fill_amount,
            "actual_delivered_amount": self.actual_delivered_amount,
            "fill_delta": self.fill_delta,
            "expected_slippage": self.expected_slippage,
            "actual_slippage": self.actual_slippage,
            "slippage_delta": self.slippage_delta,
            "drift_flags": self.drift_flags,
            "limitations": self.limitations,
            "notes": self.notes,
            "source_simulation_hash": self.source_simulation_hash,
            "source_lifecycle_hash": self.source_lifecycle_hash,
        }

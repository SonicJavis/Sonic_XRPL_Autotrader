from dataclasses import dataclass, field
from typing import List, Dict, Any

@dataclass(frozen=True, slots=True)
class CalibrationObservation:
    observation_id: str
    schema_version: str
    drift_flag: str
    count: int
    affected_records: List[str]
    metadata_backed_count: int
    non_metadata_count: int
    confidence: str
    evidence_summary: str
    limitations: List[str]
    source_report_hash: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "observation_id": self.observation_id,
            "schema_version": self.schema_version,
            "drift_flag": self.drift_flag,
            "count": self.count,
            "affected_records": self.affected_records,
            "metadata_backed_count": self.metadata_backed_count,
            "non_metadata_count": self.non_metadata_count,
            "confidence": self.confidence,
            "evidence_summary": self.evidence_summary,
            "limitations": self.limitations,
            "source_report_hash": self.source_report_hash
        }

@dataclass(frozen=True, slots=True)
class CalibrationRecommendation:
    recommendation_id: str
    schema_version: str
    category: str
    severity: str
    title: str
    recommendation_text: str
    evidence_record_ids: List[str]
    required_human_action: str
    prohibited_auto_action: str
    confidence: str
    limitations: List[str]
    source_observation_ids: List[str]
    source_report_hash: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "recommendation_id": self.recommendation_id,
            "schema_version": self.schema_version,
            "category": self.category,
            "severity": self.severity,
            "title": self.title,
            "recommendation_text": self.recommendation_text,
            "evidence_record_ids": self.evidence_record_ids,
            "required_human_action": self.required_human_action,
            "prohibited_auto_action": self.prohibited_auto_action,
            "confidence": self.confidence,
            "limitations": self.limitations,
            "source_observation_ids": self.source_observation_ids,
            "source_report_hash": self.source_report_hash
        }

@dataclass(frozen=True, slots=True)
class CalibrationSummary:
    schema_version: str
    generated_at: str
    phase30_report_path: str
    phase30_report_hash: str
    total_observations: int
    total_recommendations: int
    recommendation_counts_by_category: Dict[str, int]
    recommendation_counts_by_severity: Dict[str, int]
    confidence_counts: Dict[str, int]
    major_limitations: List[str]
    safety_statement: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "generated_at": self.generated_at,
            "phase30_report_path": self.phase30_report_path,
            "phase30_report_hash": self.phase30_report_hash,
            "total_observations": self.total_observations,
            "total_recommendations": self.total_recommendations,
            "recommendation_counts_by_category": self.recommendation_counts_by_category,
            "recommendation_counts_by_severity": self.recommendation_counts_by_severity,
            "confidence_counts": self.confidence_counts,
            "major_limitations": self.major_limitations,
            "safety_statement": self.safety_statement
        }

import hashlib
from typing import List
from execution_prototype.drift_intelligence.models import EarlyWarning, DriftTrend, ConfidenceDecay

def _generate_warning_id(w_type: str, severity: str, desc: str) -> str:
    basis = f"{w_type}|{severity}|{desc}"
    return hashlib.sha256(basis.encode("utf-8")).hexdigest()[:16]

def detect_early_warnings(trends: List[DriftTrend], decays: List[ConfidenceDecay]) -> List[EarlyWarning]:
    warnings = []
    
    # 1. Drift Acceleration
    increasing_drifts = [t for t in trends if t.trend_direction == "increasing" and t.slope_score > 0.1]
    if increasing_drifts:
        flags = [t.drift_flag for t in increasing_drifts]
        warnings.append(EarlyWarning(
            warning_id=_generate_warning_id("drift_acceleration", "high", f"Increasing drift in {','.join(flags)}"),
            type="drift_acceleration",
            severity="high",
            description=f"Mismatch rates are accelerating across runs for flags: {', '.join(flags)}",
            evidence=f"{len(increasing_drifts)} flags show slope > 0.1",
            recommended_human_action="Review underlying simulator assumptions for accelerating drift flags immediately.",
            prohibited_auto_action="Do not automatically retune parameters based on accelerating drift."
        ))
        
    # 2. Metadata Collapse
    meta_trend = next((t for t in trends if t.drift_flag == "MISSING_METADATA"), None)
    if meta_trend and meta_trend.trend_direction == "increasing":
        warnings.append(EarlyWarning(
            warning_id=_generate_warning_id("metadata_collapse", "critical", "Increasing MISSING_METADATA"),
            type="metadata_collapse",
            severity="critical",
            description="The proportion of records missing XRPL metadata is increasing.",
            evidence=f"MISSING_METADATA slope: {meta_trend.slope_score:.3f}",
            recommended_human_action="Investigate and repair ledger extraction/metadata ingestion immediately.",
            prohibited_auto_action="Do not rely on incomplete data for future reconciliations."
        ))
        
    # 3. Validation Gap Risk
    val_trend = next((t for t in trends if t.drift_flag == "TX_NOT_VALIDATED"), None)
    if val_trend and val_trend.trend_direction == "increasing":
        warnings.append(EarlyWarning(
            warning_id=_generate_warning_id("validation_gap", "high", "Increasing TX_NOT_VALIDATED"),
            type="validation_gap",
            severity="high",
            description="Increasing number of transactions are missing final ledger validation.",
            evidence=f"TX_NOT_VALIDATED slope: {val_trend.slope_score:.3f}",
            recommended_human_action="Ensure waiting periods are sufficient to capture validated outcomes.",
            prohibited_auto_action="Do not treat unvalidated transactions as tesSUCCESS."
        ))
        
    # 4. False Confidence Risk
    # Detected if any trend claims high confidence but metadata dependency is high (from decays)
    high_conf_trends = [t for t in trends if t.confidence == "high" and t.drift_flag not in ["MISSING_METADATA"]]
    meta_decay = next((d for d in decays if d.metric == "metadata_completeness"), None)
    if high_conf_trends and meta_decay and meta_decay.metadata_dependency:
        warnings.append(EarlyWarning(
            warning_id=_generate_warning_id("false_confidence", "critical", "High confidence with metadata dependency"),
            type="false_confidence",
            severity="critical",
            description="Phase 31 is asserting high confidence despite severe metadata absence.",
            evidence="Metadata dependency flag is true alongside high-confidence drift trends.",
            recommended_human_action="Review Phase 31 confidence boundaries. Downgrade trust in current reports.",
            prohibited_auto_action="Do not increase parameter trust based on these reports."
        ))
        
    # 5. Matching Integrity Risk
    amb_trend = next((t for t in trends if t.drift_flag == "AMBIGUOUS_MATCH"), None)
    if amb_trend and amb_trend.trend_direction == "increasing":
        warnings.append(EarlyWarning(
            warning_id=_generate_warning_id("matching_integrity", "medium", "Increasing AMBIGUOUS_MATCH"),
            type="matching_integrity",
            severity="medium",
            description="The reconciliation engine is failing to uniquely map intent IDs to ledger events at an increasing rate.",
            evidence=f"AMBIGUOUS_MATCH slope: {amb_trend.slope_score:.3f}",
            recommended_human_action="Improve deterministic payload tagging in simulated intents.",
            prohibited_auto_action="Do not implement fallback or fuzzy matching."
        ))
        
    return warnings

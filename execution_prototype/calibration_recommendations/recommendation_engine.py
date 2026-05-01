import hashlib
from typing import List, Optional
from execution_prototype.calibration_recommendations.models import CalibrationObservation, CalibrationRecommendation

SCHEMA_VERSION = "1.0.0"

def generate_recommendation_id(category: str, title: str, evidence_ids: List[str], report_hash: str) -> str:
    sorted_ev = sorted(evidence_ids)
    basis = f"{SCHEMA_VERSION}{category}{title}{''.join(sorted_ev)}{report_hash}"
    return hashlib.sha256(basis.encode("utf-8")).hexdigest()[:16]

def _build_rec(
    obs: CalibrationObservation,
    category: str,
    severity: str,
    title: str,
    text: str,
    human_action: str,
    auto_action: str
) -> CalibrationRecommendation:
    rec_id = generate_recommendation_id(category, title, obs.affected_records, obs.source_report_hash)
    return CalibrationRecommendation(
        recommendation_id=rec_id,
        schema_version=SCHEMA_VERSION,
        category=category,
        severity=severity,
        title=title,
        recommendation_text=text,
        evidence_record_ids=obs.affected_records,
        required_human_action=human_action,
        prohibited_auto_action=auto_action,
        confidence=obs.confidence,
        limitations=obs.limitations,
        source_observation_ids=[obs.observation_id],
        source_report_hash=obs.source_report_hash
    )

def generate_recommendations(observations: List[CalibrationObservation]) -> List[CalibrationRecommendation]:
    recs = []
    
    for obs in observations:
        flag = obs.drift_flag
        
        if flag == "FEE_MISMATCH":
            recs.append(_build_rec(
                obs,
                category="fee_model",
                severity="review_required" if obs.confidence == "high" else "caution",
                title="Review Fee Model Assumptions",
                text="Review simulator fee assumptions against actual validated fee drops.",
                human_action="Manually inspect fee deltas and decide whether model assumptions need a future reviewed change.",
                auto_action="Do not change fee estimates automatically."
            ))
            
        elif flag in ["VALIDATION_LEDGER_MISMATCH", "LATENCY_DRIFT"]:
            recs.append(_build_rec(
                obs,
                category="ledger_timing",
                severity="caution",
                title="Review Ledger Timing",
                text="Review ledger timing assumptions and validation window handling.",
                human_action="Manually compare expected ledger vs actual validated ledger deltas.",
                auto_action="Do not change ledger timing parameters automatically."
            ))
            
        elif flag == "FILL_MISMATCH":
            if obs.metadata_backed_count > 0:
                recs.append(_build_rec(
                    obs,
                    category="fill_model",
                    severity="review_required",
                    title="Review Fill Assumptions",
                    text="Review fill model against metadata-backed reality.",
                    human_action="Inspect actual delivered amounts / balance changes before deciding if fill assumptions need a future reviewed update.",
                    auto_action="Do not alter fill model from this recommendation."
                ))
            else:
                recs.append(_build_rec(
                    obs,
                    category="metadata_collection",
                    severity="info",
                    title="Improve Metadata Collection for Fills",
                    text="Fill mismatch detected without metadata backing. Needs better metadata capture.",
                    human_action="Add or improve manual/verified metadata recording in future phases.",
                    auto_action="Do not infer missing outcome data."
                ))
                
        elif flag == "SLIPPAGE_MISMATCH":
            if obs.metadata_backed_count > 0:
                recs.append(_build_rec(
                    obs,
                    category="slippage_model",
                    severity="review_required",
                    title="Review Slippage Assumptions",
                    text="Review slippage assumptions against actual metadata-backed values.",
                    human_action="Inspect expected vs actual slippage deltas and underlying transaction metadata.",
                    auto_action="Do not adjust slippage tolerance or assumptions automatically."
                ))
            # SLIPPAGE_MISMATCH without metadata does not produce a slippage recommendation.
            
        elif flag in ["INSUFFICIENT_REALITY_DATA", "MISSING_METADATA"]:
            recs.append(_build_rec(
                obs,
                category="metadata_collection",
                severity="caution",
                title="Missing Reality Data",
                text="Improve lifecycle capture to include validated XRPL metadata.",
                human_action="Add or improve manual/verified metadata recording in future phases.",
                auto_action="Do not infer missing outcome data."
            ))
            
        elif flag == "TES_SUCCESS_BUT_OUTCOME_UNKNOWN":
            recs.append(_build_rec(
                obs,
                category="metadata_collection",
                severity="caution",
                title="tesSUCCESS Requires Validation",
                text="Require ledger metadata verification after tesSUCCESS.",
                human_action="Verify tx hash against validated ledger metadata before treating the record as outcome-known.",
                auto_action="Do not treat tesSUCCESS as proof of expected trading outcome."
            ))
            
        elif flag == "AMBIGUOUS_MATCH":
            recs.append(_build_rec(
                obs,
                category="matching_quality",
                severity="caution",
                title="Ambiguous Match Detected",
                text="Improve session_id / intent_id linkage so Phase 30 can reconcile without guessing.",
                human_action="Inspect why multiple candidates matched and improve deterministic identifiers in future data capture.",
                auto_action="Do not select first/best/nearest match."
            ))
            
        elif flag == "TX_NOT_VALIDATED":
            recs.append(_build_rec(
                obs,
                category="validation_process",
                severity="caution",
                title="Unvalidated Transactions Recorded",
                text="Improve transaction validation confirmation workflow.",
                human_action="Ensure future lifecycle records include explicit validated ledger confirmation.",
                auto_action="Do not treat unvalidated submitted transactions as success or failure."
            ))
            
        elif flag == "STATUS_MISMATCH":
            recs.append(_build_rec(
                obs,
                category="data_quality",
                severity="info",
                title="Review Status Mismatch",
                text="Review expected vs actual status mapping.",
                human_action="Inspect mismatch records and determine whether mismatch reflects model error, lifecycle incompleteness, or missing metadata.",
                auto_action="Do not remap statuses automatically."
            ))
            
        elif flag == "LIQUIDITY_OVERESTIMATION":
            if obs.metadata_backed_count > 0:
                recs.append(_build_rec(
                    obs,
                    category="fill_model",
                    severity="review_required",
                    title="Review Liquidity Overestimation",
                    text="Review liquidity modelling against metadata evidence.",
                    human_action="Inspect actual fill/balance-change evidence before considering any future model change.",
                    auto_action="Do not reduce/increase liquidity assumptions automatically."
                ))
            else:
                recs.append(_build_rec(
                    obs,
                    category="metadata_collection",
                    severity="info",
                    title="Liquidity Overestimation Lacks Metadata",
                    text="Liquidity issues detected but missing XRPL metadata validation.",
                    human_action="Add or improve manual/verified metadata recording in future phases.",
                    auto_action="Do not infer missing outcome data."
                ))
                
    return recs

from typing import List, Dict, Any
from execution_prototype.drift_intelligence.models import DriftTrend

TRACKED_FLAGS = [
    "FEE_MISMATCH",
    "FILL_MISMATCH",
    "SLIPPAGE_MISMATCH",
    "MISSING_METADATA",
    "AMBIGUOUS_MATCH",
    "TX_NOT_VALIDATED",
    "TES_SUCCESS_BUT_OUTCOME_UNKNOWN",
    "LIQUIDITY_OVERESTIMATION"
]

def calculate_slope(rates: List[float]) -> float:
    # Deterministic linear regression slope: sum((x - x_mean)*(y - y_mean)) / sum((x - x_mean)^2)
    n = len(rates)
    if n < 2:
        return 0.0
    
    x = list(range(n))
    x_mean = sum(x) / n
    y_mean = sum(rates) / n
    
    numerator = sum((x[i] - x_mean) * (rates[i] - y_mean) for i in range(n))
    denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
    
    if denominator == 0:
        return 0.0
    return numerator / denominator

def analyze_trends(runs: List[Dict[str, Any]]) -> List[DriftTrend]:
    trends = []
    
    for flag in TRACKED_FLAGS:
        occurrences_per_run = []
        normalized_rate_per_run = []
        
        for run in runs:
            records = run.get("reconciliation_records", [])
            total_records = len(records)
            
            if total_records == 0:
                occurrences_per_run.append(0)
                normalized_rate_per_run.append(0.0)
                continue
                
            count = 0
            for rec in records:
                if flag in rec.get("drift_flags", []):
                    count += 1
                    
            occurrences_per_run.append(count)
            normalized_rate_per_run.append(count / total_records)
            
        total_occurrences = sum(occurrences_per_run)
        
        if len(runs) < 3:
            trend_direction = "INSUFFICIENT_TREND_DATA"
            slope_score = 0.0
            confidence = "low"
        else:
            slope_score = calculate_slope(normalized_rate_per_run)
            if slope_score > 0.05:
                trend_direction = "increasing"
            elif slope_score < -0.05:
                trend_direction = "decreasing"
            else:
                trend_direction = "stable"
                
            # Basic confidence definition
            if total_occurrences >= 10 and max(occurrences_per_run) >= 3:
                confidence = "high"
            elif total_occurrences >= 3:
                confidence = "medium"
            else:
                confidence = "low"
                
        trends.append(DriftTrend(
            drift_flag=flag,
            total_occurrences=total_occurrences,
            occurrences_per_run=occurrences_per_run,
            normalized_rate_per_run=normalized_rate_per_run,
            trend_direction=trend_direction,
            slope_score=slope_score,
            confidence=confidence
        ))
        
    return trends

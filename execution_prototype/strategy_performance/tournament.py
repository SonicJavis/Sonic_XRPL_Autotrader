from typing import List, Dict, Any, Optional
import hashlib
from execution_prototype.strategy_performance.models import StrategyBacktestResult, StrategyTournamentResult

def _generate_tournament_id(results: List[StrategyBacktestResult]) -> str:
    basis = "|".join(sorted(r.result_id for r in results))
    return hashlib.sha256(basis.encode("utf-8")).hexdigest()[:16]

def run_tournament(results: List[StrategyBacktestResult]) -> StrategyTournamentResult:
    ranked = sorted(results, key=lambda x: x.risk_adjusted_score, reverse=True)
    
    strongest_conditions = []
    weakest_conditions = []
    repeated_failures = []
    protocol_opps = set()
    
    for r in ranked:
        if r.amm_backed_success_rate and r.amm_backed_success_rate > 70:
            strongest_conditions.append(f"{r.strategy_id} excels with AMM")
        if r.offer_only_failure_rate and r.offer_only_failure_rate > 70:
            repeated_failures.append(f"{r.strategy_id} fails on OfferOnly")
        for p in r.protocol_feature_notes:
            protocol_opps.add(p)
            
    winner_id = ranked[0].strategy_id if ranked else None
    
    return StrategyTournamentResult(
        tournament_id=_generate_tournament_id(results),
        ranked_strategies=[r.to_dict() for r in ranked],
        winner_strategy_id=winner_id,
        strongest_conditions=strongest_conditions,
        weakest_conditions=weakest_conditions,
        repeated_failures=repeated_failures,
        protocol_feature_opportunities=list(protocol_opps),
        human_review_required=True,
        prohibited_auto_action="Live trading, parameter tuning, self-mutation"
    )

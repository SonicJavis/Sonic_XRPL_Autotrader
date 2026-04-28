from __future__ import annotations


def build_xrpl_risk_flags(
    *,
    confidence_score: float,
    confidence_floor_threshold: float,
    possible_unfunded_liquidity: bool = False,
    pathfinding_risk: bool = False,
    inclusion_uncertainty: bool = False,
    depth_illusion_risk: bool = False,
) -> dict[str, bool]:
    # Low confidence always forces all XRPL risk flags to true.
    if confidence_score < confidence_floor_threshold:
        return {
            "possible_unfunded_liquidity": True,
            "pathfinding_risk": True,
            "inclusion_uncertainty": True,
            "depth_illusion_risk": True,
        }

    return {
        "possible_unfunded_liquidity": bool(possible_unfunded_liquidity),
        "pathfinding_risk": bool(pathfinding_risk),
        "inclusion_uncertainty": bool(inclusion_uncertainty),
        "depth_illusion_risk": bool(depth_illusion_risk),
    }

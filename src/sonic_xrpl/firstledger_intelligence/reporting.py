from __future__ import annotations

import json
from dataclasses import asdict

from sonic_xrpl.firstledger_intelligence.models import FirstLedgerIntelligenceResult


def render_intelligence_report(results: list[FirstLedgerIntelligenceResult]) -> list[dict]:
    payload = []
    for item in results:
        row = asdict(item)
        row["verdict"] = item.verdict.value
        payload.append(row)
    return payload


def render_intelligence_markdown(results: list[FirstLedgerIntelligenceResult]) -> str:
    lines = [
        "# Phase 59 FirstLedger Intelligence Report",
        "",
        "Paper-only, non-executing intelligence output.",
        "",
    ]
    if not results:
        lines.append("No candidates found.")
        return "\n".join(lines)

    for item in results:
        lines.extend(
            [
                f"## {item.candidate_id}",
                "",
                f"- Verdict: `{item.verdict.value}`",
                f"- Confidence: {item.confidence.score}/100 ({item.confidence.band})",
                f"- Paper only: `{item.paper_only}`",
                f"- Review only: `{item.review_only}`",
                f"- Live execution allowed: `{item.live_execution_allowed}`",
                f"- Missing evidence: {', '.join(item.missing_evidence) or 'none'}",
                "- Reasons:",
            ]
        )
        for reason in item.reasons:
            lines.append(f"  - {reason}")
        lines.append("- Risk factors:")
        lines.append(f"  - issuer_concentration_risk={item.risk_features.issuer_concentration_risk}")
        lines.append(f"  - holder_concentration_risk={item.risk_features.holder_concentration_risk}")
        lines.append(f"  - freeze_clawback_risk={item.risk_features.freeze_clawback_risk}")
        lines.append(f"  - source_conflict={item.risk_features.source_conflict}")
        lines.append("")

    return "\n".join(lines)


def report_to_json_text(results: list[FirstLedgerIntelligenceResult]) -> str:
    return json.dumps(render_intelligence_report(results), indent=2, ensure_ascii=True)

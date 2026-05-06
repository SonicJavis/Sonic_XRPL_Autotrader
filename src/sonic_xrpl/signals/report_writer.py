"""Report writer for Phase 49 FirstLedger candidate signals."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from sonic_xrpl.signals.firstledger_candidate import EMPTY_STATE
from sonic_xrpl.signals.models import CandidateRiskSignal


def _signal_to_dict(signal: CandidateRiskSignal) -> dict[str, Any]:
    data = asdict(signal)
    data["signal_type"] = signal.signal_type.value
    return data


def write_signal_report(signals: list[CandidateRiskSignal], output_dir: str | Path) -> tuple[Path, Path]:
    """Write deterministic JSON and Markdown reports."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    json_path = out / "firstledger_signals.json"
    md_path = out / "firstledger_signals.md"
    json_path.write_text(json.dumps([_signal_to_dict(signal) for signal in signals], indent=2, ensure_ascii=True))

    lines = ["# Phase 49 FirstLedger Signal Report", "", "Offline advisory signals only. Live execution is not allowed.", ""]
    if not signals:
        lines.append(EMPTY_STATE)
    else:
        for signal in signals:
            lines += [
                f"## {signal.candidate_id}",
                "",
                f"- Signal: `{signal.signal_type.value}`",
                f"- Confidence: {signal.confidence_score}/100",
                f"- Risk: {signal.risk_score}/100",
                f"- Live execution allowed: `{signal.live_execution_allowed}`",
                f"- Missing evidence: {', '.join(signal.missing_required_evidence) or 'none'}",
                "- Reasons:",
            ]
            lines.extend(f"  - {reason}" for reason in signal.reasons)
            if signal.limitations:
                lines.append("- Limitations:")
                lines.extend(f"  - {limitation}" for limitation in signal.limitations)
            lines.append("")
    md_path.write_text("\n".join(lines))
    return json_path, md_path

from __future__ import annotations

import json
from pathlib import Path
from dataclasses import asdict
from typing import Tuple, List

from sonic_xrpl.review.models import SignalReviewItem, PaperDecision, PaperTradeIntent, ReviewQueue


def _to_json(obj) -> dict:
    try:
        return asdict(obj)
    except Exception:
        return obj.__dict__  # fallback


def write_review_report(queue: ReviewQueue, review_items: List[SignalReviewItem], paper_decisions: List[PaperDecision], paper_intents: List[PaperTradeIntent], output_dir: Path) -> Tuple[str, str]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / f"phase50_signal_review_{queue.queue_id}.json"
    md_path = output_dir / f"phase50_signal_review_summary_{queue.queue_id}.md"

    payload = {
        "queue_id": queue.queue_id,
        "generated_at": queue.generated_at,
        "source_fixture": queue.source_fixture,
        "items": [_to_json(i) for i in review_items],
        "decisions": [_to_json(d) for d in paper_decisions],
        "intents": [_to_json(p) for p in paper_intents],
        "limitations": list(queue.limitations),
    }

    json_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")

    lines = ["# Phase 50 Signal Review Summary", "", f"Queue ID: {queue.queue_id}", f"Generated: {queue.generated_at}", ""]
    lines.append("## Items")
    for it in review_items:
        lines.append(f"- {it.review_id}: {it.classification} (candidate {it.candidate_id})")
    lines.append("")
    lines.append("## Decisions")
    for d in paper_decisions:
        lines.append(f"- {d.decision_id}: {d.decision} for candidate {d.candidate_id}")
    lines.append("")
    lines.append("## Intents (paper-only)")
    for intent in paper_intents:
        lines.append(f"- {intent.intent_id}: side={intent.side}, notional={intent.notional_xrp}")
    md_path.write_text("\n".join(lines), encoding="utf-8")

    return str(json_path), str(md_path)

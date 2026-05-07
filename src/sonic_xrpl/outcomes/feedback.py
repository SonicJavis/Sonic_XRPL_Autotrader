from __future__ import annotations

from collections import defaultdict

from sonic_xrpl.outcomes.models import OutcomeLabel, PaperOutcomeAttribution, SignalFeedbackBucket, SignalFeedbackSummary
from sonic_xrpl.signals.evidence import stable_id

_GENERATED_AT = "1970-01-01T00:00:00+00:00"


def _average(values: list[float]) -> float | None:
    if not values:
        return None
    return round(sum(values) / len(values), 2)


def _bucket(signal_type: str, items: list[PaperOutcomeAttribution]) -> SignalFeedbackBucket:
    observed = [item.observed_return_bps for item in items if item.observed_return_bps is not None]
    excess = [item.excess_return_bps for item in items if item.excess_return_bps is not None]
    return SignalFeedbackBucket(
        signal_type=signal_type,
        count=len(items),
        wins=sum(1 for item in items if item.outcome_label == OutcomeLabel.WIN),
        losses=sum(1 for item in items if item.outcome_label == OutcomeLabel.LOSS),
        flats=sum(1 for item in items if item.outcome_label == OutcomeLabel.FLAT),
        missing_observations=sum(1 for item in items if item.outcome_label == OutcomeLabel.NO_OBSERVATION),
        average_observed_return_bps=_average(observed),
        average_excess_return_bps=_average(excess),
    )


def _recommendations(summary_items: list[PaperOutcomeAttribution]) -> tuple[str, ...]:
    if not summary_items:
        return ("Collect paper outcome observations before changing signal scoring.",)
    missing = sum(1 for item in summary_items if item.outcome_label == OutcomeLabel.NO_OBSERVATION)
    losses = sum(1 for item in summary_items if item.outcome_label == OutcomeLabel.LOSS)
    wins = sum(1 for item in summary_items if item.outcome_label == OutcomeLabel.WIN)
    recs: list[str] = []
    if missing:
        recs.append("Improve paper observation coverage before tightening signal thresholds.")
    if losses > wins:
        recs.append("Review evidence thresholds for signal classes with negative paper outcomes.")
    if wins and losses == 0:
        recs.append("Keep collecting paper outcomes; current fixture set is not enough for production calibration.")
    if not recs:
        recs.append("Maintain deterministic paper review and add more source-backed observations.")
    return tuple(recs)


def build_signal_feedback(
    attributions: list[PaperOutcomeAttribution],
    *,
    generated_at: str = _GENERATED_AT,
) -> SignalFeedbackSummary:
    """Aggregate paper-only attribution results into signal feedback."""
    by_type: dict[str, list[PaperOutcomeAttribution]] = defaultdict(list)
    for item in attributions:
        by_type[item.signal_type].append(item)

    buckets = {signal_type: _bucket(signal_type, items) for signal_type, items in sorted(by_type.items())}
    observed = [item.observed_return_bps for item in attributions if item.observed_return_bps is not None]
    excess = [item.excess_return_bps for item in attributions if item.excess_return_bps is not None]
    limitations = tuple(
        dict.fromkeys(
            limitation
            for item in attributions
            for limitation in item.limitations
        )
    )

    return SignalFeedbackSummary(
        feedback_id=stable_id("fb", generated_at, len(attributions), tuple(sorted(buckets))),
        generated_at=generated_at,
        total_attributed=len(attributions),
        wins=sum(1 for item in attributions if item.outcome_label == OutcomeLabel.WIN),
        losses=sum(1 for item in attributions if item.outcome_label == OutcomeLabel.LOSS),
        flats=sum(1 for item in attributions if item.outcome_label == OutcomeLabel.FLAT),
        missing_observations=sum(1 for item in attributions if item.outcome_label == OutcomeLabel.NO_OBSERVATION),
        average_observed_return_bps=_average(observed),
        average_excess_return_bps=_average(excess),
        by_signal_type=buckets,
        recommendations=_recommendations(attributions),
        limitations=limitations,
        paper_only=True,
        live_execution_allowed=False,
    )

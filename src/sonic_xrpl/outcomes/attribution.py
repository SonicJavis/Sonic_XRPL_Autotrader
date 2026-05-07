from __future__ import annotations

from sonic_xrpl.outcomes.models import OutcomeLabel, PaperOutcomeAttribution, PaperOutcomeObservation
from sonic_xrpl.signals.evidence import stable_id
from sonic_xrpl.signals.models import CandidateRiskSignal


def _return_bps(entry: float | None, exit_value: float | None) -> float | None:
    if entry is None or exit_value is None or entry <= 0:
        return None
    return round(((exit_value - entry) / entry) * 10000, 2)


def _label_from_return(value: float | None, *, win_bps: float, loss_bps: float) -> OutcomeLabel:
    if value is None:
        return OutcomeLabel.NO_OBSERVATION
    if value >= win_bps:
        return OutcomeLabel.WIN
    if value <= -abs(loss_bps):
        return OutcomeLabel.LOSS
    return OutcomeLabel.FLAT


def _index_observations(observations: list[PaperOutcomeObservation]) -> dict[tuple[str, str], PaperOutcomeObservation]:
    indexed: dict[tuple[str, str], PaperOutcomeObservation] = {}
    for observation in observations:
        if observation.signal_id:
            indexed[("signal", observation.signal_id)] = observation
        indexed.setdefault(("candidate", observation.candidate_id), observation)
    return indexed


def _match_observation(
    signal: CandidateRiskSignal,
    indexed: dict[tuple[str, str], PaperOutcomeObservation],
) -> PaperOutcomeObservation | None:
    return indexed.get(("signal", signal.signal_id)) or indexed.get(("candidate", signal.candidate_id))


def build_outcome_attributions(
    signals: list[CandidateRiskSignal],
    observations: list[PaperOutcomeObservation],
    *,
    win_bps: float = 100.0,
    loss_bps: float = 100.0,
) -> list[PaperOutcomeAttribution]:
    """Attribute deterministic paper observations back to existing signal records."""
    indexed = _index_observations(observations)
    attributions: list[PaperOutcomeAttribution] = []

    for signal in sorted(signals, key=lambda item: item.candidate_id):
        observation = _match_observation(signal, indexed)
        observed_return = None
        baseline_return = None
        excess_return = None
        window = "unobserved"
        limitations = list(signal.limitations)
        reason_codes = [signal.signal_type.value]

        if observation is None:
            limitations.append("paper_outcome_observation_missing")
            reason_codes.append("NO_MATCHING_OUTCOME_OBSERVATION")
        else:
            observed_return = _return_bps(observation.entry_price_xrp, observation.exit_price_xrp)
            baseline_return = _return_bps(observation.entry_price_xrp, observation.baseline_exit_price_xrp)
            if observed_return is not None and baseline_return is not None:
                excess_return = round(observed_return - baseline_return, 2)
            window = observation.window
            limitations.extend(observation.limitations)
            reason_codes.append(f"OUTCOME_WINDOW:{observation.window}")
            reason_codes.append(f"EVIDENCE_QUALITY:{observation.evidence_quality}")

        label = _label_from_return(observed_return, win_bps=win_bps, loss_bps=loss_bps)
        attributions.append(
            PaperOutcomeAttribution(
                attribution_id=stable_id("attr", signal.signal_id, signal.candidate_id, window),
                candidate_id=signal.candidate_id,
                signal_id=signal.signal_id,
                signal_type=signal.signal_type.value,
                window=window,
                outcome_label=label,
                observed_return_bps=observed_return,
                baseline_return_bps=baseline_return,
                excess_return_bps=excess_return,
                confidence_score_at_signal=signal.confidence_score,
                risk_score_at_signal=signal.risk_score,
                attribution_reason_codes=tuple(reason_codes),
                limitations=tuple(dict.fromkeys(limitations)),
                paper_only=True,
                live_execution_allowed=False,
            )
        )

    return attributions

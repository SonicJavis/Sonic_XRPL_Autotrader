from __future__ import annotations

import json
from pathlib import Path

from sonic_xrpl.outcome_corpus.models import OutcomeCorpus, OutcomeCorpusReport, jsonable


SAFETY_STATEMENT = (
    "Phase 52 outcome corpus reports are offline, paper-only artifacts. "
    "Live execution remains blocked and live_execution_allowed=false."
)
NEXT_RECOMMENDED_ACTION = (
    "Use this corpus to plan Phase 53 calibration review coverage; do not mutate scoring thresholds automatically."
)


def write_outcome_corpus_report(
    corpus: OutcomeCorpus,
    output_dir: str | Path = "reports/phase52",
) -> OutcomeCorpusReport:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    corpus_json = output / "outcome_corpus.json"
    corpus_md = output / "outcome_corpus.md"
    quality_json = output / "outcome_corpus_quality.json"
    quality_md = output / "outcome_corpus_quality.md"

    corpus_json.write_text(json.dumps(jsonable(corpus), indent=2, sort_keys=True), encoding="utf-8")
    quality_json.write_text(json.dumps(jsonable(corpus.quality_summary), indent=2, sort_keys=True), encoding="utf-8")

    corpus_lines = [
        "# Phase 52 Outcome Replay Corpus",
        "",
        f"Corpus ID: `{corpus.corpus_id}`",
        f"Generated at: `{corpus.generated_at}`",
        f"Paper only: `{str(corpus.paper_only).lower()}`",
        f"Live execution allowed: `{str(corpus.live_execution_allowed).lower()}`",
        "",
        "## Summary",
        f"- Total cases: {corpus.total_cases}",
        f"- Source-backed cases: {corpus.source_backed_cases}",
        f"- Synthetic cases: {corpus.synthetic_cases}",
        f"- Limited cases: {corpus.limited_cases}",
        f"- Quality grade: {corpus.quality_summary.quality_grade}",
        "",
        "## Replay Cases",
    ]
    if not corpus.replay_cases:
        corpus_lines.append("- No usable observation cases.")
    for case in corpus.replay_cases:
        corpus_lines.append(
            f"- `{case.candidate_id}`: windows={','.join(case.windows_present) or 'none'} "
            f"missing={','.join(case.windows_missing) or 'none'} "
            f"source_backed={str(case.source_backed).lower()} synthetic={str(case.synthetic).lower()}"
        )
    corpus_lines.extend(["", "## Safety", SAFETY_STATEMENT, "", "## Next Step", NEXT_RECOMMENDED_ACTION])
    corpus_md.write_text("\n".join(corpus_lines) + "\n", encoding="utf-8")

    quality = corpus.quality_summary
    quality_lines = [
        "# Phase 52 Outcome Corpus Quality",
        "",
        f"Quality grade: `{quality.quality_grade}`",
        f"Recommendation: {quality.recommendation}",
        "",
        "## Counts",
        f"- Total cases: {quality.total_cases}",
        f"- Complete cases: {quality.complete_cases}",
        f"- Partial cases: {quality.partial_cases}",
        f"- Missing observation cases: {quality.missing_observation_cases}",
        f"- Source-backed cases: {quality.source_backed_cases}",
        f"- Synthetic cases: {quality.synthetic_cases}",
        f"- Average windows present: {quality.average_windows_present}",
        "",
        "## Limitations",
    ]
    if not quality.limitation_counts:
        quality_lines.append("- None.")
    for limitation, count in quality.limitation_counts.items():
        quality_lines.append(f"- `{limitation}`: {count}")
    quality_lines.extend(["", "## Safety", SAFETY_STATEMENT])
    quality_md.write_text("\n".join(quality_lines) + "\n", encoding="utf-8")

    generated = {
        "corpus_json": str(corpus_json),
        "corpus_markdown": str(corpus_md),
        "quality_json": str(quality_json),
        "quality_markdown": str(quality_md),
    }
    limitations = tuple(corpus.quality_summary.limitation_counts)
    return OutcomeCorpusReport(
        corpus=corpus,
        generated_files=generated,
        safety_statement=SAFETY_STATEMENT,
        limitations=limitations,
        next_recommended_action=NEXT_RECOMMENDED_ACTION,
    )


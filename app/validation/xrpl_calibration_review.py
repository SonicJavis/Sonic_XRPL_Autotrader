from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from hashlib import sha256
from io import StringIO
from math import isfinite
from typing import Iterable, Mapping

from app.db.models import CalibrationReviewRecord
from app.validation.xrpl_calibration_recommendations import (
    RECOMMENDATION_SCHEMA_VERSION,
    compute_recommendation_id,
    validate_recommendation_payload,
)


REVIEW_SCHEMA_VERSION = "1.0"
EXPORT_SCHEMA_VERSION = "1.0"
REVIEW_DECISIONS = {"accepted", "rejected", "deferred", "noted"}
REVIEW_WARNING = (
    "Manual consideration only; review records are append-only and do not change calibration settings"
)

CSV_REVIEW_FIELDS = (
    "review_id",
    "recommendation_id",
    "schema_version",
    "decision",
    "reviewer_id",
    "reviewed_at",
    "token_id",
    "issuer",
    "attribution",
    "regime",
)

_REVIEW_NOTE_BLOCKLIST = {
    "actual",
    "apply",
    "confirmed",
    "correct",
    "execute",
    "guaranteed",
    "real",
    "truth",
}


def build_review_record(
    *,
    recommendation: Mapping[str, object],
    decision: str,
    review_notes: str,
    reviewer_id: str | None,
    reviewed_at: datetime,
) -> CalibrationReviewRecord:
    validated = validate_recommendation_payload(recommendation)
    safe_decision = str(decision).strip().lower()
    if safe_decision not in REVIEW_DECISIONS:
        raise ValueError("decision must be accepted, rejected, deferred, or noted")
    safe_notes = _safe_notes(review_notes)
    safe_reviewer = None if reviewer_id is None else str(reviewer_id).strip()[:120]
    return CalibrationReviewRecord(
        recommendation_id=str(validated["recommendation_id"]),
        recommendation_snapshot_json=json.dumps(validated, sort_keys=True, separators=(",", ":")),
        schema_version=REVIEW_SCHEMA_VERSION,
        decision=safe_decision,
        review_notes=safe_notes,
        reviewer_id=safe_reviewer,
        reviewed_at=_utc(reviewed_at),
        is_shadow=True,
        is_advisory=True,
        is_executable=False,
        is_truth=False,
    )


def review_to_dict(row: CalibrationReviewRecord) -> dict[str, object]:
    recommendation = _safe_json_dict(row.recommendation_snapshot_json)
    scope = recommendation.get("scope") if isinstance(recommendation.get("scope"), dict) else {}
    return {
        "review_id": _review_id(row),
        "recommendation_id": str(row.recommendation_id),
        "schema_version": str(row.schema_version or REVIEW_SCHEMA_VERSION),
        "decision": str(row.decision),
        "review_notes": str(row.review_notes or ""),
        "reviewer_id": row.reviewer_id,
        "reviewed_at": _utc(row.reviewed_at).isoformat(),
        "recommendation": recommendation,
        "attribution": str(scope.get("attribution", "")),
        "regime": str(scope.get("regime", "")),
        "token_id": int(_finite(scope.get("token_id", 0))),
        "issuer": str(scope.get("issuer", "")),
        "is_shadow": True,
        "is_advisory": True,
        "is_executable": False,
        "is_truth": False,
    }


def filter_review_rows(
    rows: Iterable[CalibrationReviewRecord],
    *,
    decision: str | None = None,
    recommendation_id: str | None = None,
    attribution: str | None = None,
    regime: str | None = None,
    token_id: int | None = None,
    issuer: str | None = None,
) -> list[CalibrationReviewRecord]:
    filtered: list[CalibrationReviewRecord] = []
    for row in rows:
        body = review_to_dict(row)
        if decision and body["decision"] != decision:
            continue
        if recommendation_id and body["recommendation_id"] != recommendation_id:
            continue
        if attribution and body["attribution"] != attribution:
            continue
        if regime and body["regime"] != regime:
            continue
        if token_id is not None and int(body["token_id"]) != int(token_id):
            continue
        if issuer and body["issuer"] != issuer:
            continue
        filtered.append(row)
    return sorted(filtered, key=lambda item: (_utc(item.reviewed_at), int(item.id or 0)), reverse=True)


def build_audit_export_bundle(
    *,
    recommendations: Iterable[Mapping[str, object]],
    reviews: Iterable[CalibrationReviewRecord],
    generated_at: datetime | None = None,
    deterministic: bool = False,
) -> dict[str, object]:
    generated = datetime(1970, 1, 1, tzinfo=timezone.utc) if deterministic else _utc(generated_at or datetime.now(timezone.utc))
    recommendation_rows = sorted(
        [validate_recommendation_payload(row) for row in recommendations],
        key=lambda item: str(item["recommendation_id"]),
    )
    review_rows = [review_to_dict(row) for row in reviews]
    review_rows = sorted(review_rows, key=lambda item: (str(item["reviewed_at"]), str(item["review_id"])), reverse=True)
    integrity = build_audit_integrity(recommendation_rows, review_rows)
    bundle: dict[str, object] = {
        "export_schema_version": EXPORT_SCHEMA_VERSION,
        "source_schema_version": RECOMMENDATION_SCHEMA_VERSION,
        "generated_at": generated.isoformat(),
        "recommendations": recommendation_rows,
        "review_records": review_rows,
        "csv_review_summary": build_review_csv(review_rows),
        "snapshot_bundle": {
            "recommendation_count": len(recommendation_rows),
            "review_count": len(review_rows),
            "review_decision_counts": _decision_counts(review_rows),
            "integrity": integrity,
        },
        "is_shadow": True,
        "is_advisory": True,
        "is_executable": False,
        "is_truth": False,
        "xrpl_warning": REVIEW_WARNING,
    }
    bundle["export_hash"] = _bundle_hash(bundle)
    return bundle


def build_review_csv(review_rows: Iterable[Mapping[str, object]]) -> str:
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=list(CSV_REVIEW_FIELDS), lineterminator="\n")
    writer.writeheader()
    for row in review_rows:
        writer.writerow({field: row.get(field, "") for field in CSV_REVIEW_FIELDS})
    return output.getvalue()


def build_audit_integrity(
    recommendations: Iterable[Mapping[str, object]],
    review_rows: Iterable[Mapping[str, object]],
) -> dict[str, object]:
    recommendation_ids = {str(row.get("recommendation_id", "")) for row in recommendations}
    rows = list(review_rows)
    seen_review_signatures: set[tuple[str, str, str, str, str]] = set()
    duplicates: list[str] = []
    orphans: list[str] = []
    incompatible = 0
    ordered_ids: list[int] = []
    for row in rows:
        review_id = str(row.get("review_id", ""))
        recommendation_id = str(row.get("recommendation_id", ""))
        if recommendation_id not in recommendation_ids:
            orphans.append(review_id)
        if row.get("schema_version") != REVIEW_SCHEMA_VERSION:
            incompatible += 1
        ordered_ids.append(_review_id_number(review_id))
    for row in sorted(rows, key=lambda item: _review_id_number(str(item.get("review_id", "")))):
        review_id = str(row.get("review_id", ""))
        recommendation_id = str(row.get("recommendation_id", ""))
        signature = (
            recommendation_id,
            str(row.get("decision", "")),
            str(row.get("review_notes", "")),
            str(row.get("reviewer_id", "")),
            str(row.get("reviewed_at", "")),
        )
        if signature in seen_review_signatures:
            duplicates.append(review_id)
        seen_review_signatures.add(signature)
    return {
        "orphan_review_ids": sorted(orphans),
        "duplicate_review_ids": sorted(duplicates),
        "schema_version_compatible": incompatible == 0,
        "incompatible_schema_count": incompatible,
        "append_only_sequence_valid": ordered_ids == sorted(ordered_ids, reverse=True),
        "is_shadow": True,
        "is_advisory": True,
        "is_executable": False,
        "is_truth": False,
    }


def _bundle_hash(bundle: Mapping[str, object]) -> str:
    payload = {key: value for key, value in bundle.items() if key != "export_hash"}
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return f"export_{sha256(encoded).hexdigest()[:32]}"


def _decision_counts(review_rows: Iterable[Mapping[str, object]]) -> dict[str, int]:
    counts = {decision: 0 for decision in sorted(REVIEW_DECISIONS)}
    for row in review_rows:
        decision = str(row.get("decision", ""))
        if decision in counts:
            counts[decision] += 1
    return counts


def _safe_json_dict(raw: object) -> dict[str, object]:
    try:
        parsed = json.loads(str(raw or "{}"))
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _safe_notes(raw: object) -> str:
    text = str(raw or "").strip()[:1000]
    tokens = {token.strip(".,;:!?()[]{}\"'").lower() for token in text.split()}
    blocked = sorted(_REVIEW_NOTE_BLOCKLIST.intersection(tokens))
    if blocked:
        raise ValueError(f"review_notes contain unsupported certainty or control wording: {blocked}")
    return text


def _review_id(row: CalibrationReviewRecord) -> str:
    return f"review_{int(row.id or 0):012d}"


def _review_id_number(raw: str) -> int:
    try:
        return int(str(raw).split("_")[-1])
    except ValueError:
        return 0


def _utc(raw: datetime) -> datetime:
    value = raw if raw.tzinfo is not None else raw.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _finite(raw: object) -> float:
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return 0.0
    return value if isfinite(value) else 0.0

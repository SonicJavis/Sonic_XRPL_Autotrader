from __future__ import annotations

from sonic_xrpl.calibration_implementation_plan.models import CalibrationImplementationItem, DryRunPatchPreview
from sonic_xrpl.signals.evidence import stable_id


def build_patch_preview(item: CalibrationImplementationItem) -> DryRunPatchPreview:
    diff_text = (
        "DRY RUN ONLY - no file was changed.\n"
        f"Target: {item.target_namespace}.{item.target_parameter}\n"
        f"Before: {item.current_value:.2f}\n"
        f"After: {item.proposed_value:.2f}\n"
        f"Delta: {item.exact_delta:+.2f}\n"
        "Manual implementation required in a future phase.\n"
        "Runtime mutation allowed: false\n"
        "Auto apply allowed: false\n"
        "Live execution allowed: false\n"
        f"Rollback: {item.rollback_note}\n"
    )
    return DryRunPatchPreview(
        patch_id=stable_id("drp", item.implementation_item_id, item.change_request_id),
        target_file_hint=item.target_file_hint,
        target_config_key_hint=item.target_config_key_hint,
        before_value=item.current_value,
        after_value=item.proposed_value,
        diff_text=diff_text,
        apply_allowed=False,
        runtime_mutation_allowed=False,
    )


def render_dry_run_preview(items: tuple[CalibrationImplementationItem, ...]) -> str:
    lines = [
        "=== Phase 56 Calibration Implementation Dry Run ===",
        "DRY RUN ONLY",
        "No file was changed.",
        "Live execution: BLOCKED",
        "",
    ]
    if not items:
        lines.append("No implementation items were generated.")
        return "\n".join(lines)

    for item in items:
        lines.append(
            f"- {item.implementation_item_id}: {item.target_namespace}.{item.target_parameter} "
            f"{item.current_value:.2f} -> {item.proposed_value:.2f} (delta={item.exact_delta:+.2f})"
        )
        lines.append("  DRY RUN ONLY - no file was changed.")
    return "\n".join(lines)

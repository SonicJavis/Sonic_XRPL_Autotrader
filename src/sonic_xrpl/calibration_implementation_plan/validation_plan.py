from __future__ import annotations

from sonic_xrpl.calibration_implementation_plan.models import ImplementationValidationPlan


def build_validation_plan() -> ImplementationValidationPlan:
    return ImplementationValidationPlan(
        required_commands=(
            ".\\.venv\\Scripts\\python.exe -m pytest tests\\unit\\test_phase56_implementation_plan_models.py",
            ".\\.venv\\Scripts\\python.exe -m pytest tests\\unit\\test_phase56_implementation_plan_loader.py",
            ".\\.venv\\Scripts\\python.exe -m pytest tests\\unit\\test_phase56_implementation_planner.py",
            ".\\.venv\\Scripts\\python.exe -m pytest tests\\unit\\test_phase56_dry_run_patch.py",
            ".\\.venv\\Scripts\\python.exe -m pytest tests\\unit\\test_phase56_validation_and_rollback_plan.py",
            ".\\.venv\\Scripts\\python.exe -m pytest tests\\unit\\test_phase56_report_writer.py",
            ".\\.venv\\Scripts\\python.exe -m pytest tests\\smoke\\test_phase56_implementation_plan_cli.py",
            ".\\.venv\\Scripts\\python.exe -m pytest tests\\safety\\test_phase56_implementation_plan_safety.py",
            ".\\.venv\\Scripts\\python.exe scripts\\safety_grep.py",
            ".\\.venv\\Scripts\\python.exe scripts\\audit_validator.py",
            ".\\.venv\\Scripts\\python.exe scripts\\dependency_audit.py --write-report --strict",
            "git diff --check",
        ),
        required_tests=(
            "phase56_unit_models",
            "phase56_unit_loader",
            "phase56_unit_planner",
            "phase56_unit_dry_run_patch",
            "phase56_unit_validation_rollback",
            "phase56_unit_report_writer",
            "phase56_smoke_cli",
            "phase56_safety",
        ),
        safety_checks=(
            "paper_only=True",
            "offline_only=True",
            "dry_run_only=True",
            "auto_apply_allowed=False",
            "live_execution_allowed=False",
            "runtime_mutation_allowed=False",
            "requires_human_implementation=True",
        ),
        docs_checks=(
            "docs/PHASE56_APPROVED_CALIBRATION_IMPLEMENTATION_PLAN.md",
            "docs/research/PHASE56_APPROVED_CALIBRATION_IMPLEMENTATION_PLAN_RESEARCH.md",
            "docs/PHASE_LEDGER.md",
            "docs/ROADMAP.md",
            "docs/SAFETY_MODEL.md",
            "docs/V2_ARCHITECTURE.md",
            "docs/PROJECT_BLUEPRINT.md",
            "src/sonic_xrpl/audit/docs_check.py",
        ),
        acceptance_criteria=(
            "No runtime calibration values are mutated.",
            "All outputs are deterministic and offline-only.",
            "Dry-run previews clearly state no file was changed.",
            "Any unsupported or unsafe request is blocked with explicit reason.",
        ),
    )

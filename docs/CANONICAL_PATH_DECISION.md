# Canonical Path Decision

## Decision

Canonical future runtime surface: `src/sonic_xrpl/`.

Current state remains unchanged until migration steps and safety gates are
complete:

- `app/` remains the current runnable legacy API/paper runtime.
- `execution_prototype/` remains historical/reference-only except named tests
  and bridge adapters.
- `src/sonic_xrpl/` remains the V2 governance/offline architecture and is the
  selected target for runtime convergence.

## Evidence Basis

Facts:

- `app/main.py` is the current runnable API (`README.md`, `ARCHITECTURE.md`).
- `src/sonic_xrpl/` contains Phase 45+ governance and safety architecture
  (`docs/PROJECT_BLUEPRINT.md`, `docs/V2_ARCHITECTURE.md`).
- Safety gates are enforced in both runtime surfaces:
  `app/execution/execution_guard.py` and `src/sonic_xrpl/execution/live_guard.py`.

Inference resolved by decision:

- `src/sonic_xrpl/` is not only likely future target; it is now the canonical
  future runtime target.

## Migration Plan (Three Surfaces to One)

Target end state: one canonical runtime under `src/sonic_xrpl/` with legacy
surfaces frozen or adapter-wrapped.

1. Freeze and classification lock (already complete in PR 1-PR 5).
2. Runtime contract extraction from `app/` into explicit compatibility boundary.
3. Canonical API entrypoint added under `src/sonic_xrpl/` with parity-only
   behavior.
4. `app/` converted to thin compatibility shell or archived once parity and
   safety gates pass.
5. `execution_prototype/` retained as reference/tests only; no runtime authority.

## Exact File Migration Order

Order is mandatory to preserve fail-closed behavior.

1. Entrypoint and routing boundary:
   - `app/main.py`
   - `app/api/`
   - new `src/sonic_xrpl/api/` (future)
2. Execution/paper orchestration parity:
   - `app/execution/pipeline.py`
   - `app/execution/paper.py`
   - map into `src/sonic_xrpl/execution/` integration layer (future)
3. Configuration parity:
   - `app/config/__init__.py`
   - align with `src/sonic_xrpl/core/config.py`
4. Telemetry/storage parity:
   - `app/telemetry/`
   - `app/db/`
   - align with `src/sonic_xrpl/telemetry/` and `src/sonic_xrpl/storage/`
5. Legacy compatibility reduction:
   - `app/` retained only as shell or archived after safety and parity acceptance
   - `execution_prototype/` unchanged except documented reference/test usage

## Safety Gates Per Step

Every step above must pass, with no exceptions:

1. `python -m pytest tests/test_execution_guard.py`
2. `python -m pytest tests/unit/test_live_guard.py`
3. `python -m pytest tests/safety/test_safety_scan.py`
4. `python scripts/safety_grep.py`
5. `python scripts/audit_validator.py`
6. `PYTHONPATH=src python -m sonic_xrpl.cli.main audit`
7. `PYTHONPATH=src python -m sonic_xrpl.cli.main safety-scan`
8. `git diff --check`

Blocked unless all pass:

- Any signing/submission/autofill/wallet code.
- Any change that weakens `ExecutionGuard` or `live_guard`.
- Any runtime mutation of calibration outputs.

## Effort Estimate

- Overall: high.
- Rationale:
  - Cross-surface parity work (`app/` to `src/sonic_xrpl/`) is multi-module.
  - Requires staged compatibility plus repeated safety regression cycles.
  - Must preserve current fail-closed and paper-only behavior at all times.

## Phase Scope Note

Phase 56 evidence exists in the repository and is retained. This decision
applies to architecture convergence planning and does not authorize live/sniper
execution work.

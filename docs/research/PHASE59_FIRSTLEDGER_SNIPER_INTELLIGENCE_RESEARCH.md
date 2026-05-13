# Phase 59 Research - FirstLedger Source-Backed Sniper Intelligence

## Official sources reviewed

- XRPL docs:
  - Amendments model and activation
  - Token freeze behavior (individual/global/no-freeze)
  - Clawback transaction semantics and amendment dependency
- XRPL Standards references:
  - XLS clawback-related proposals
- XRPLF/rippled release notes for current protocol/runtime context
- GitHub security references for CI and supply-chain controls

## Repository-grounded design constraints

- Keep V2 canonical future runtime under `src/sonic_xrpl/`.
- Keep current runtime behavior fail-closed and paper-only.
- Do not add live ingestion, execution, signing, submission, or wallet handling.
- Preserve Phase 49 interpretation that signal labels are non-executing.
- Require deterministic fixture-backed behavior and explicit provenance.

## Unsafe patterns explicitly rejected

- Any repository pattern that combines token discovery directly with order submit.
- Any design that stores wallet seeds/private keys for automation.
- Any "sniper bot" pattern with hidden network calls or obfuscated install scripts.
- Any confidence/risk classifier that silently fabricates missing launch evidence.
- Any runtime path that treats synthetic-only evidence as positive qualification.

## Safe patterns adopted

- Source-backed evidence required for positive paper-only qualification.
- Fail-closed handling for malformed records and conflicting provenance.
- Explicit missing-evidence reporting instead of heuristic fill-ins.
- Clear separation of fact, inference, and limitations in report outputs.
- Deterministic fixture-only input and stable output ordering.

## Resulting Phase 59 approach

Phase 59 implements a conservative intelligence layer with:

- non-executing verdicts
- deterministic confidence/risk output
- explicit paper-only and live-blocked markers
- no network/runtime mutation behavior

This keeps product-intelligence progress moving while preserving all existing
safety boundaries before any future live-readiness phase.

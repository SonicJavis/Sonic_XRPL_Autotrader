# Phase 60 Research - Paper-Only Sniper Simulation Harness

## Official sources reviewed

- XRPL ledger-close timing and close-time resolution docs.
- XRPL transaction finality and reliable submission docs (future-risk context).
- XRPL DEX/CLOB and AMM concept docs.
- XRPL freeze/clawback control docs.
- xrpl-py official docs (library capability/scope awareness).
- xrpl.js official docs (future-risk context for signing/submission surfaces).
- FirstLedger public docs (risk-context review only).
- Xaman developer docs (future manual-approval context only).
- GitHub code security docs for dependency review, CodeQL, and push protection.

## Repository-grounded design constraints

- Keep canonical runtime evolution under `src/sonic_xrpl/`.
- Keep all Phase 60 behavior deterministic and fixture-backed.
- Keep simulation outputs advisory and paper-only.
- Do not add live network access, execution coupling, signing, submission, or
  wallet handling.

## Unsafe patterns rejected

- Discovery-to-execution coupling.
- Wallet seed/private-key import and automated signing.
- Simulation outputs phrased as real PnL or investment advice.
- Implicit assumptions treated as verified facts.
- Hidden/remote data pulls in simulation path.

## Safe patterns adopted

- Explicit fill/no-fill/partial-fill labels as assumptions.
- Explicit rejection reasons for unsupported/unsafe inputs.
- Explicit stale/missing/conflict handling with fail-closed defaults.
- Deterministic fixture-only inputs and stable sorting.
- Explicit paper-only/live-blocked flags in all simulation outputs.

## Resulting Phase 60 approach

Phase 60 implements a paper-only simulation harness that answers:
"What would have happened under explicit assumptions?"

It does not answer:
"What should we execute live?"

Execution remains blocked.

# Phase 62 Research Notes - Xaman Testnet Payload Schema Review

## Official-source review focus

- Xaman payload lifecycle references for future-risk context.
- XRPL transaction lifecycle and reliable submission references for verification sequencing context.
- Security review references for callback authenticity and replay-protection controls.

## Safety findings applied

1. Payload schema and callback verification must be separated from execution authorization.
2. Testnet-only gating must be explicit; mainnet remains blocked by default.
3. Replay protection needs nonce + TTL + callback replay cache + account-txn-id correlation.
4. Human approval remains mandatory before any future implementation phase.

## Rejected unsafe patterns

- SDK/API wiring in a design-only phase.
- hidden signing or submission helpers.
- automatic progression from review to execution.
- wallet-seed/private-key material handling.
- mainnet enablement in schema-review phase.

## Why this Phase 62 approach is safe

- Pure spec dataclasses/functions only.
- Deterministic fixtures and offline tests.
- Explicit fail-closed markers for attempted unsafe actions.
- No network/runtime mutation or transaction execution paths.

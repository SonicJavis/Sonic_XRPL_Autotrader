# Phase 65 Research - Xaman Approval State Machine Design Spec

## Official sources reviewed

- Xaman status updates and webhook model:
  https://docs.xaman.dev/concepts/payloads-sign-requests/status-updates
  https://docs.xaman.dev/concepts/payloads-sign-requests/status-updates/webhooks
- Xaman webhook signature verification guidance:
  https://docs.xaman.dev/concepts/payloads-sign-requests/status-updates/webhooks/signature-verification
- Xaman payload verification lifecycle context:
  https://docs.xaman.dev/concepts/payloads-sign-requests/verify-transactions
- GitHub webhook security best practices and delivery uniqueness guidance:
  https://docs.github.com/webhooks/using-webhooks/best-practices-for-using-webhooks
  https://docs.github.com/en/webhooks/using-webhooks/validating-webhook-deliveries

## Unsafe patterns rejected

- Runtime state machine execution loops.
- Auto-approval paths.
- Callback/webhook runtime handlers.
- Persistence or database implementation in this phase.
- Any payload/API/signing/submission/wallet execution coupling.

## Adopted constraints

- Pure state/transition specification with deterministic fixtures and report
  outputs only.
- Explicit invalid-transition blocking for unsafe states/actions.
- Explicit fail-closed safety flags preventing runtime/persistence/execution.

## Why this is safe for current repository state

- No runtime state machine implementation added.
- No persistence/DB writes/migrations added.
- No callback runtime or API surface added.
- No payload/signing/submission/wallet/testnet/live execution added.
- Outputs remain spec/docs/tests/fixture/reporting only.

# Phase 64 Research - Xaman Audit Trail + Idempotency Store Design Spec

## Official sources reviewed

- Xaman webhooks overview (limited callback body + follow-up retrieval model):
  https://docs.xaman.dev/concepts/payloads-sign-requests/status-updates/webhooks
- Xaman webhook signature verification guidance:
  https://docs.xaman.dev/concepts/payloads-sign-requests/status-updates/webhooks/signature-verification
- Xaman payload verification lifecycle context:
  https://docs.xaman.dev/concepts/payloads-sign-requests/verify-transactions
- XRPL reliable transaction submission (idempotency/verifiability principles):
  https://xrpl.org/docs/concepts/transactions/reliable-transaction-submission/
- GitHub webhook security best practices (signature and unique delivery IDs):
  https://docs.github.com/webhooks/using-webhooks/best-practices-for-using-webhooks
- GitHub CodeQL guidance:
  https://docs.github.com/en/code-security/code-scanning/introduction-to-code-scanning/about-code-scanning-with-codeql
- GitHub dependency-review action guidance:
  https://docs.github.com/en/code-security/how-tos/secure-your-supply-chain/manage-your-dependency-security/configuring-the-dependency-review-action

## Unsafe patterns rejected

- Callback/webhook runtime implementation in Phase 64.
- Persistence/database implementation in Phase 64.
- Any Xaman SDK/API integration or payload workflow implementation.
- Any signing/submission/autofill/wallet material handling.
- Any coupling between callback-spec outputs and testnet/live execution.

## Adopted constraints

- Pure spec dataclasses and deterministic fixture evaluation only.
- Fail-closed blocked markers for persistence/runtime/API/payload/execution.
- Explicit audit and idempotency checklist/report outputs.
- Explicit blocker register for future implementation phases.

## Why this is safe now

- No runtime callback surface added.
- No persistence implementation or DB writes added.
- No network/API/SDK dependencies added.
- No signing/submission/autofill/wallet/testnet/live execution changes added.
- Outputs are docs/spec models/fixtures/tests/reporting only.

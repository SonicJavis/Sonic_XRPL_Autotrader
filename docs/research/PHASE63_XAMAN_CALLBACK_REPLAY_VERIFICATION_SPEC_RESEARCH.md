# Phase 63 Research - Xaman Callback Authenticity + Replay Verification Spec

## Official sources reviewed

- Xaman webhook status update docs: callback body is limited and full payload
  retrieval is a separate API/SDK step.
  - https://docs.xaman.dev/concepts/payloads-sign-requests/status-updates/webhooks
- Xaman webhook signature verification docs: signature verification is required
  to verify callback origin/integrity.
  - https://docs.xaman.dev/concepts/payloads-sign-requests/status-updates/webhooks/signature-verification
- Xaman secure payment verification lifecycle context.
  - https://docs.xaman.dev/concepts/payloads-sign-requests/verify-transactions
- XRPL transaction common fields (including sequencing/account-txn anchoring
  concepts useful for design constraints).
  - https://xrpl.org/transaction-common-fields.html
- XRPL reliable transaction submission best practices (idempotency and
  verifiability principles as future-risk context).
  - https://xrpl.org/docs/concepts/transactions/reliable-transaction-submission/
- GitHub webhook security best practices (signature verification, TLS,
  idempotent processing patterns).
  - https://docs.github.com/webhooks/using-webhooks/best-practices-for-using-webhooks
- GitHub CodeQL overview for repository security analysis posture.
  - https://docs.github.com/en/code-security/code-scanning/introduction-to-code-scanning/about-code-scanning-with-codeql
- GitHub dependency/supply-chain review action documentation.
  - https://docs.github.com/en/code-security/how-tos/secure-your-supply-chain/manage-your-dependency-security/configuring-the-dependency-review-action

## Unsafe patterns explicitly rejected

- Implementing callback handlers in this phase.
- Implementing webhook runtime verification logic in this phase.
- Adding API routes/listeners/pollers/background callback workers.
- Adding Xaman SDK/API calls or payload creation.
- Coupling callback-design outputs to execution/signing/submission logic.
- Adding wallet material handling or secrets flows.

## Adopted Phase 63 design constraints

- Spec-only deterministic contracts with fail-closed markers.
- Explicit authenticity + nonce/TTL/replay + idempotency requirements.
- Explicit duplicate callback and ordering requirements.
- Explicit candidate/paper-simulation/operator-consent linkage requirements.
- Explicit blocker register for future callback-runtime/testnet/live phases.

## Why this is safe for current repository state

- No runtime callback surface was added.
- No network/API/SDK dependency was introduced.
- No signing/submission/autofill/wallet or execution hooks were introduced.
- All outputs are fixtures/tests/docs/spec reports only.
- Live and testnet execution remain blocked.

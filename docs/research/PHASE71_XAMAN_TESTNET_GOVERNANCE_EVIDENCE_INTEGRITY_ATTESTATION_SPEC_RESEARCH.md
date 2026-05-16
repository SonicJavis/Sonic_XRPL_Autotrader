# Phase 71 Research — Xaman Governance Evidence Integrity + Attestation Spec

## Official Sources Reviewed
- Xaman payload/sign-request concepts:
  - https://docs.xaman.dev/concepts/payloads-sign-requests
- Xaman webhook status concepts:
  - https://docs.xaman.dev/concepts/payloads-sign-requests/status-updates/webhooks
- XRPL reliable transaction submission (future-risk context only):
  - https://xrpl.org/docs/concepts/transactions/reliable-transaction-submission/
- GitHub governance/security controls:
  - https://docs.github.com/articles/about-code-owners
  - https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches
  - https://docs.github.com/code-security/secret-scanning/introduction/about-secret-scanning

## Best Practices Adopted
- Deterministic, fixture-backed evidence records and attestation outcomes.
- Explicit fail-closed blocked markers for prohibited payload/testnet/live
  approval language and wallet-material ambiguity.
- Explicit owner/reviewer linkage and sign-off domain traceability.
- Clear separation between governance evidence specs and runtime behavior.

## Unsafe Patterns Rejected
- Runtime attestation services and callback/webhook handlers.
- Xaman payload creation or API/SDK calls.
- Signing/submission/autofill and wallet material handling.
- Testnet/live execution enablement language.

## Safety Rationale
Phase 71 remains a prerequisite governance-evidence control layer and does not
authorize any execution path.

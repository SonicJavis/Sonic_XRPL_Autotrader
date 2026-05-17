# Phase 75 Research - Xaman Testnet Governance Final Readiness Bundle Spec

## Date

2026-05-17

## Sources reviewed

### Repo and PR history

- GitHub merged PR history for Phase 58A through Phase 74, including PR #82 for Phase 74.
- Phase 70-74 spec docs, research docs, implementation modules, fixtures, reports, CLI patterns, and audit scripts.

### Official external sources

- XRPL reliable transaction submission: <https://xrpl.org/docs/concepts/transactions/reliable-transaction-submission/>
- XRPL Standards repository: <https://github.com/XRPLF/XRPL-Standards>
- rippled releases: <https://github.com/XRPLF/rippled/releases>
- Clio releases: <https://github.com/XRPLF/clio/releases>
- xrpl-py transaction docs: <https://xrpl-py.readthedocs.io/en/v2.2.0/source/xrpl.transaction.html>
- Xaman payload concepts: <https://docs.xaman.dev/concepts/payloads-sign-requests>
- Xaman payload lifecycle: <https://docs.xaman.dev/concepts/payloads-sign-requests/lifecycle>
- GitHub CODEOWNERS: <https://docs.github.com/articles/about-codeowners>
- GitHub protected branches: <https://docs.github.com/en/enterprise-cloud@latest/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches>
- GitHub push protection: <https://docs.github.com/en/code-security/secret-scanning/introduction/about-push-protection>
- GitHub supply-chain security: <https://docs.github.com/en/code-security/supply-chain-security/understanding-your-software-supply-chain>
- GitHub dependency security: <https://docs.github.com/en/code-security/how-tos/secure-your-supply-chain/secure-your-dependencies>

## Best practices found

- Final readiness packages should preserve unresolved evidence and limitations rather than flattening them into a single optimistic state.
- Cross-phase artifact traceability is stronger when every prerequisite is represented explicitly and absent artifacts are treated as incomplete, not inferred.
- Supply-chain, secret-scanning, CODEOWNERS, and protected-branch controls are supporting evidence, not substitutes for application-level fail-closed readiness.
- Payload creation, transaction signing, submission, autofill, wallet handling, testnet execution, and live execution remain categorically outside a spec-only readiness bundle.

## Tools and patterns considered

- Deterministic fixture-backed final bundle builder.
- Explicit artifact reference model with local source paths and declared hashes.
- Fail-closed final classifications with a separate limitation register.
- Traceability from Phase 70-74 artifacts into one reportable final bundle.

## Suspicious or rejected sources

- Generic crypto/trading repositories were rejected as unsafe exemplars because they often conflate review readiness with execution readiness.
- External code examples were not copied; only concepts from official documentation and mature governance patterns were retained.
- Runtime readiness services, schedulers, callbacks, notifications, payload APIs, and wallet workflows were rejected as out of scope.

## Security implications

- A final bundle can create dangerous false confidence if missing artifacts, revoked waivers, expired waivers, overdue SLAs, or unresolved safety findings are hidden.
- Xaman payload lifecycle documentation and xrpl-py transaction APIs show that payload/signing/submission surfaces are materially closer to execution than governance artifacts and must stay outside this phase.
- GitHub dependency and push-protection controls reduce exposure, but do not justify weakening the application boundary.

## Why the chosen design is safe for this repo

Phase 75 composes local governance evidence without adding any runtime service, transaction surface, network call, or safety bypass. It keeps the final answer conservative: only `SPEC_REVIEW_READY` for a complete spec packet, never execution-ready.

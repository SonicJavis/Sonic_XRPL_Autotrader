# Phase 78 Research - Xaman Testnet Governance Review Export Approval Packet Spec

## Date

2026-05-17

## Sources reviewed

### Repo and PR history

- GitHub merged PR history for Phase 58A through Phase 77, including PR #85 for Phase 77.
- Phase 70-77 docs, research docs, implementation modules, fixtures, reports, CLI patterns, and audit scripts.

### Official external sources

- XRPL reliable transaction submission: <https://xrpl.org/docs/concepts/transactions/reliable-transaction-submission/>
- XRPL Standards repository: <https://github.com/XRPLF/XRPL-Standards>
- rippled releases: <https://github.com/XRPLF/rippled/releases>
- Clio releases: <https://github.com/XRPLF/clio/releases>
- xrpl-py transaction docs: <https://xrpl-py.readthedocs.io/en/stable/source/xrpl.transaction.html>
- xrpl.js client docs: <https://js.xrpl.org/classes/Client.html>
- xrpl.js supply-chain advisory history: <https://github.com/advisories/GHSA-33qr-m49q-rxfx>
- Xaman payload concepts: <https://docs.xaman.dev/concepts/payloads-sign-requests>
- Xaman payload lifecycle: <https://docs.xaman.dev/concepts/payloads-sign-requests/lifecycle>
- GitHub CODEOWNERS: <https://docs.github.com/articles/about-code-owners>
- GitHub protected branches: <https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches>
- GitHub push protection: <https://docs.github.com/en/code-security/secret-scanning/introduction/about-push-protection>
- GitHub supply-chain security: <https://docs.github.com/en/code-security/supply-chain-security/understanding-your-software-supply-chain>
- GitHub dependency review guidance: <https://docs.github.com/en/code-security/how-tos/secure-your-supply-chain/secure-your-dependencies>
- GitHub Actions security hardening: <https://docs.github.com/en/actions/security-for-github-actions/security-guides/security-hardening-for-github-actions>

## Best practices found

- Approval-facing packets should preserve acknowledgement scope, reviewer role, evidence linkage, and explicit non-authorization language.
- Acknowledgement is not authorization: it should be bounded to review purpose and preserve unresolved limitations.
- Rejected acknowledgements, blocked audits, and hidden blockers must fail closed rather than being summarized away.
- Approval packets should compose earlier evidence without creating a runtime workflow or delivery surface.

## Tools and patterns considered

- Deterministic fixture-backed approval packet builder.
- Reviewer acknowledgement records with explicit non-authorization statements.
- Approval limitation register plus cross-phase traceability map.
- Synthetic blocked/review-required fixtures for acknowledgement gaps and unsafe wording.

## Suspicious or rejected sources

- Generic crypto/trading repositories were rejected as unsafe exemplars because they often confuse reviewer approval with wallet or execution enablement.
- External code examples were not copied; only concepts from official docs and mature governance patterns were retained.
- Runtime approval services, downloadable archives, API/UI routes, callbacks, and wallet workflows were rejected as out of scope.

## Security implications

- The word ?approval? can create dangerous ambiguity unless every packet states what is not authorized.
- Acknowledgement records can mask unresolved debt if they are not tied to reviewer role, artifact, limitation, and evidence.
- Payload/signing/submission/testnet/live wording remains categorically unsafe for this phase.

## Why the chosen design is safe for this repo

Phase 78 composes local synthetic review artifacts only. It adds no runtime approval service, no downloadable archive, no API/UI route, no transaction surface, and no safety bypass. The strongest positive state remains `APPROVAL_PACKET_SPEC_REVIEW_READY`, never execution-ready.

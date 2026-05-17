# Phase 74 Research - Xaman Testnet Governance Exception Waiver Register Spec

## Date

2026-05-17

## Sources reviewed

### Repo and PR history

- GitHub merged PR history for Phase 58A through Phase 73, including PR #81 for Phase 73.
- `docs/PHASE70_XAMAN_TESTNET_GOVERNANCE_SIGNOFF_MATRIX_SPEC.md`
- `docs/PHASE71_XAMAN_TESTNET_GOVERNANCE_EVIDENCE_INTEGRITY_ATTESTATION_SPEC.md`
- `docs/PHASE72_XAMAN_TESTNET_GOVERNANCE_EVIDENCE_REVIEW_WORKFLOW_SPEC.md`
- `docs/PHASE73_XAMAN_TESTNET_GOVERNANCE_ESCALATION_RESOLUTION_SLA_SPEC.md`
- Existing Phase 70-73 implementation modules, fixtures, tests, CLI patterns, and audit scripts.

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
- GitHub dependency security: <https://docs.github.com/en/code-security/how-tos/secure-your-supply-chain/secure-your-dependencies>
- GitHub Actions security hardening: <https://docs.github.com/en/actions/security-for-github-actions/security-guides/security-hardening-for-github-actions>
- OWASP Vulnerability Management Guide exception expiry guidance: <https://owasp.org/www-project-vulnerability-management-guide/OWASP-Vuln-Mgm-Guide-Jun01-2020.pdf>

## Best practices found

- Keep governance controls deterministic, reviewable, and separate from runtime execution paths.
- Treat signing, submission, autofill, wallet material, and payload creation as execution-adjacent surfaces requiring categorical blocking in this repo.
- Require named ownership, explicit evidence, compensating controls, expiry, revocation, and replacement linkage for exceptions.
- Require time-bounded exceptions; non-compliance exceptions should expire rather than linger indefinitely.
- Use review gates, protected branches, CODEOWNERS, secret scanning, dependency review, and least-privilege CI as reinforcing controls rather than as reasons to relax application safety.
- Treat dependency waivers as high-sensitivity because official advisory history documents compromised `xrpl.js` releases that exfiltrated private keys.

## Tools and patterns considered

- Deterministic fixture-backed local register builder.
- Explicit terminal statuses (`REVOKED`, `EXPIRED`, `SUPERSEDED`, `BLOCKED`).
- Traceability map linking waiver records to Phase 70-73 governance artifacts.
- Synthetic blocker fixtures for unsafe target classes.
- Expiry/revocation policy strings kept as spec contracts, not executable timers.

## Suspicious or rejected sources

- Generic crypto/sniper trading repositories were rejected as unsafe exemplars because they commonly collapse governance, wallet handling, and execution into the same surface.
- External code examples were not copied; only concepts from official docs and mature governance patterns were retained.
- Runtime waiver engines, schedulers, notifications, callbacks, payload APIs, and wallet workflows were rejected as out of scope and unsafe for this phase.

## Security implications

- Waivers can become a bypass channel if they are not bounded, owned, evidenced, revocable, and traceable.
- Critical ambiguity around Xaman payloads, wallet material, testnet/live execution, signing, submission, autofill, runtime mutation, or guard weakening must be categorically blocked rather than waived.
- Dependency-risk waivers and safety-review waivers remain review-required until separately resolved; they cannot manufacture readiness.

## Why the chosen design is safe for this repo

Phase 74 extends the existing deterministic governance stack without introducing any runtime service, network path, transaction surface, or safety bypass. It adds structure around exceptions while preserving the project?s fail-closed boundary and the long-standing separation between specification, simulation, paper records, governance, and any future live execution work.

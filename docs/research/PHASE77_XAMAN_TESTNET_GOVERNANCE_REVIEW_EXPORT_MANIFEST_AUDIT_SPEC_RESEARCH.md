# Phase 77 Research - Xaman Testnet Governance Review Export Manifest Audit Spec

## Date

2026-05-17

## Sources reviewed

### Repo and PR history

- GitHub merged PR history for Phase 58A through Phase 76, including PR #84 for Phase 76.
- Phase 70-76 docs, research docs, implementation modules, fixtures, reports, CLI patterns, and audit scripts.

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

- Manifest audits should compare declared and observed integrity fields rather than trusting package metadata by default.
- Reviewer summaries, limitation registers, and traceability maps need independent coverage checks so that hidden blockers are not lost in presentation layers.
- Required artifact references should fail closed when absent, duplicated, undeclared, or inconsistent.
- Governance audit results must remain distinct from execution authorization.

## Tools and patterns considered

- Deterministic fixture-backed manifest audit builder.
- Declared-versus-observed hash reconciliation.
- Audit finding register plus audit limitation register.
- Cross-phase traceability audit map and explicit hidden-blocker fixtures.

## Suspicious or rejected sources

- Generic crypto/trading repositories were rejected as unsafe exemplars because they commonly conflate manifests, artifacts, wallets, and execution.
- External code examples were not copied; only concepts from official docs and mature audit patterns were retained.
- Runtime manifest audit services, downloadable archives, API/UI routes, callbacks, and wallet workflows were rejected as out of scope.

## Security implications

- A manifest can be syntactically complete while semantically deceptive if expired waivers, revoked waivers, overdue SLAs, or unsafe waiver attempts are hidden.
- Declared hashes without observed reconciliation are assertions, not evidence.
- Export-audit functionality must not become a new runtime or distribution surface.

## Why the chosen design is safe for this repo

Phase 77 audits local synthetic review-export fixtures only. It adds no runtime audit service, no downloadable archive, no API/UI route, no transaction surface, and no safety bypass. The strongest possible positive result remains `AUDIT_SPEC_REVIEW_READY`, never execution-ready.

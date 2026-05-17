# Phase 76 Research - Xaman Testnet Governance Final Readiness Review Export Spec

## Date

2026-05-17

## Sources reviewed

### Repo and PR history

- GitHub merged PR history for Phase 58A through Phase 75, including PR #83 for Phase 75.
- Phase 70-75 spec docs, research docs, implementation modules, fixtures, reports, CLI patterns, and audit scripts.

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
- GitHub dependency review and secure dependencies guidance: <https://docs.github.com/en/code-security/how-tos/secure-your-supply-chain/secure-your-dependencies>
- GitHub Actions security hardening: <https://docs.github.com/en/actions/security-for-github-actions/security-guides/security-hardening-for-github-actions>

## Best practices found

- Review packets should preserve provenance, checksum references, redaction state, limitations, and reviewer-facing summaries separately rather than collapsing them into one optimistic result.
- Missing required artifacts, reference-only evidence, and redacted evidence should remain explicit review limitations.
- Export packaging must not be confused with runtime distribution or execution authorization.
- Protected branches, CODEOWNERS, dependency review, push protection, and provenance controls reinforce review integrity but do not replace application fail-closed checks.

## Tools and patterns considered

- Deterministic fixture-backed export package builder.
- Explicit export artifact records with inclusion and redaction states.
- Manifest plus checksum references, reviewer summaries, limitation register, and cross-phase traceability map.
- Export-specific fail-closed blockers for runtime export/download/API/UI ambiguity.

## Suspicious or rejected sources

- Generic crypto/trading repositories were rejected as unsafe exemplars because they often blur export, governance, wallet handling, and execution surfaces.
- External code examples were not copied; only concepts from official docs and mature review-packet patterns were retained.
- Runtime export/download services, downloadable archives, API/UI export endpoints, payload APIs, callbacks, and wallet workflows were rejected as out of scope.

## Security implications

- A review export can create false confidence if redaction, provenance, or missing-artifact state is hidden.
- Packaging must not become an exfiltration path for secrets or wallet material; this phase handles synthetic fixtures only and relies on existing scanners rather than inventing a new secret-processing surface.
- Runtime export/download/API/UI affordances are deliberately blocked because they would turn a spec packet into an operational service boundary.

## Why the chosen design is safe for this repo

Phase 76 packages local synthetic governance evidence only. It adds no network path, no downloadable archive, no API/UI route, no runtime export service, no transaction surface, and no safety bypass. The strongest possible positive result remains `EXPORT_SPEC_REVIEW_READY`, never execution-ready.

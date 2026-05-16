# Phase 72 Research - Xaman Testnet Governance Evidence Review Workflow Spec

## Date

2026-05-16

## Official sources reviewed

- Xaman payloads/sign requests:
  <https://docs.xaman.dev/concepts/payloads-sign-requests>
- Xaman payload lifecycle:
  <https://docs.xaman.dev/concepts/payloads-sign-requests/lifecycle>
- XRPL reliable transaction submission:
  <https://xrpl.org/docs/concepts/transactions/reliable-transaction-submission/>
- GitHub CODEOWNERS:
  <https://docs.github.com/articles/about-code-owners>
- GitHub protected branches:
  <https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches>
- GitHub Actions security hardening:
  <https://docs.github.com/en/actions/how-tos/security-for-github-actions/security-guides/security-hardening-for-github-actions>
- GitHub push protection:
  <https://docs.github.com/en/code-security/secret-scanning/introduction/about-push-protection>
- SLSA provenance reference:
  <https://slsa.dev/spec/v1.0-rc2/provenance>

## Repo evidence reviewed

- `docs/PHASE70_XAMAN_TESTNET_GOVERNANCE_SIGNOFF_MATRIX_SPEC.md`
- `docs/PHASE71_XAMAN_TESTNET_GOVERNANCE_EVIDENCE_INTEGRITY_ATTESTATION_SPEC.md`
- `src/sonic_xrpl/xaman_governance_signoff_matrix_spec/`
- `src/sonic_xrpl/xaman_governance_evidence_attestation_spec/`
- `src/sonic_xrpl/cli/main.py`
- `src/sonic_xrpl/audit/docs_check.py`
- `scripts/safety_grep.py`
- `scripts/audit_validator.py`
- `scripts/dependency_audit.py`
- `scripts/migration_safe_check.py`
- `scripts/guard_critical_changes.py`

## Best practices carried forward

- Deterministic fixture-backed review outputs only.
- Conservative readiness states with explicit blocked/review-required paths.
- Explicit role/stage/handoff/escalation traceability.
- No hidden transition to runtime execution language.
- Explicit no-live/no-testnet/no-payload confirmations in report outputs.

## Unsafe patterns rejected

- Runtime workflow service/engine implementation.
- Callback or webhook handlers.
- API routes or UI workflow endpoints.
- Xaman payload creation or API/SDK use.
- Signing/submission/autofill or wallet material handling.
- DB writes/persistence and background workers.
- Any status wording implying testnet/live approval.

## Why this design is safe for this repository

Phase 72 extends the existing Phase 70/71 governance stack using the same
offline deterministic pattern and hard safety flags. It strengthens governance
review sequencing without introducing runtime behavior, transaction surfaces, or
networked execution paths.

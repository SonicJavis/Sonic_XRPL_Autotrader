Security Audit and Hardening Plan
================================

This repository represents a risk-sensitive domain (<project context> economic trading agent).
We will pursue a pragmatic, minimally invasive hardening approach:

- Baseline: Verify there are no hard-coded secrets or credentials in the codebase.
- Environment-based secrets: All secrets must be sourced from environment/config at runtime.
- Network security: Prefer TLS for all external endpoints; ensure URLs are not hard-coded with insecure schemes.
- Dependency hygiene: Track vulnerable dependencies and align to supported, patched versions.
- Code quality gates: Add lightweight, repeatable checks to catch secrets leaks early.

What we will touch in this pass
- Add a small secret-scanning utility and a security doc.
- Wire up minimal usage guidance and a non-blocking smoke test to ensure the scanner can run.
- Do not alter trading logic, data models, or live execution paths.

Next steps
- Run the secret scanner across the repository and address any findings.
- If secrets are found, move them to environment-based configuration, replacing literals with config.get_secret("KEY").
- Add a pre-commit hook (optional) to run the scanner on commit and fail if secrets are detected.

Notes
- This is a safety-oriented audit. If any vulnerability is discovered that affects runtime behavior, we will discuss and approve changes before applying them to production-like paths.

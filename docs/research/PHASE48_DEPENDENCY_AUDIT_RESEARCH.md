# Phase 48 — Dependency Audit Research

**Date checked**: 2026-05-03  
**Status**: Research-only context for Phase 48 implementation  
**Phase objective**: Add a safe dependency and supply-chain audit layer

---

## 1. xrpl.js Compromised Versions

### Source
- **URL**: https://xrpl.org/blog/2025/vulnerabilitydisclosurereport-bug-apr2025
- **GitHub Advisory**: https://github.com/advisories/GHSA-x788-gr4m-h5p3 (NPM package `xrpl`)

### Key Point
In April 2025, the `xrpl` npm package was compromised via a malicious supply-chain attack. Affected versions exfiltrated secret key material (private keys / wallet seeds) to an attacker-controlled endpoint.

### Compromised Versions
| Version | Status |
|---------|--------|
| `4.2.1` | COMPROMISED — exfiltrates key material |
| `4.2.2` | COMPROMISED — exfiltrates key material |
| `4.2.3` | COMPROMISED — exfiltrates key material |
| `4.2.4` | COMPROMISED — exfiltrates key material |
| `2.14.2` | COMPROMISED — exfiltrates key material |

### Patched Versions
| Version | Status |
|---------|--------|
| `4.2.5` | SAFE — malicious code removed |
| `2.14.3` | SAFE — malicious code removed |
| `4.3.x+` | SAFE |
| `2.14.4+` | SAFE |

### Architecture Impact
The Sonic XRPL Autotrader repository currently has **no `package.json`** (Node.js is not a runtime dependency). However, the audit script must detect compromised versions in any future Node dependency files that may be introduced. Detection logic already exists in `src/sonic_xrpl/audit/dependency_check.py`; Phase 48 surfaces it via a standalone script.

### Status
**Implemented** — Detection of compromised xrpl.js versions in `scripts/dependency_audit.py` and existing `src/sonic_xrpl/audit/dependency_check.py`. Node audit returns `not_applicable` when no Node files exist.

---

## 2. Python Dependency Context

### xrpl-py Version

- **URL**: https://pypi.org/project/xrpl-py/
- **Date checked**: 2026-05-03

| Channel | Version |
|---------|---------|
| Stable | `4.5.0` |
| Pre-release | `4.6.0b0` |

### Current Repository Constraint
`pyproject.toml` specifies `xrpl-py>=2.6.0`. The installed version in the CI environment will resolve to the latest compatible release. This is a **broad lower-bound** that allows any stable version.

### Key Point
No known CVEs or compromise events affect `xrpl-py` (the Python library). The April 2025 compromise was specific to the `xrpl` npm package, not the Python counterpart.

### Architecture Impact
- `pip-audit` will check the installed `xrpl-py` and all other Python dependencies against the OSV/PyPI Advisory database.
- No upgrade is forced in this phase — only auditing and reporting.

### Status
**Monitored** — `pip-audit` included as dev dependency; runs in CI dependency-audit job.

---

## 3. pip-audit

### Source
- **URL**: https://pypi.org/project/pip-audit/
- **GitHub**: https://github.com/pypa/pip-audit

### Key Point
`pip-audit` is the recommended PyPA tool for checking installed packages against known vulnerability databases (OSV + PyPI Advisory DB). It requires network access to query the vulnerability DB during a scan.

### Policy for Phase 48
- `pip-audit` is added as a dev dependency: `pip-audit>=2.7.0`
- If network is unavailable during audit, the script reports a **warning** (exit code 2), not a hard failure.
- A hard failure (exit code 1) is only reported if known bad packages are positively identified.
- `--skip-pip-audit` flag bypasses pip-audit entirely for offline/restricted environments.

### Status
**Implemented** — `pip-audit>=2.7.0` added to `[project.optional-dependencies].dev` in `pyproject.toml`.

---

## 4. rippled Release Notes

### Source
- **URL**: https://xrpl.org/blog/2026/rippled-3.1.2
- **Date checked**: 2026-05-03

### Key Points
- `rippled` 3.1.2 is the current stable release (as of research date).
- It is a security/continuity release — operators should upgrade as affected servers may crash.
- A new GPG signing key requirement is noted in release notes.
- `rippled` 3.1.1 disabled the `Batch` and `fixBatchInnerSigs` amendments due to a severe bug (unauthorized inner transaction execution).

### Architecture Impact
- The Sonic XRPL Autotrader does **not** run a `rippled` node.
- Provider layer reads are currently fixture-backed (offline). No live rippled calls in Phase 48.
- The Batch amendment vulnerability is research-only context. No impact on this phase.

### Status
**Research-only** — No implementation change. Documented for awareness.

---

## 5. XRPL Known Amendments Status

### Source
- **URL**: https://xrpl.org/resources/known-amendments
- **Date checked**: 2026-05-03

### Key Points
- Enabled amendments include: AMMClawback, Clawback, Credentials, MPTokensV1.
- Batch and fixBatchInnerSigs: disabled/marked unsupported due to the Feb 2026 vulnerability.
- LendingProtocol: open for voting.
- Obsolete amendments are separately listed and must not be marked enabled.

### Architecture Impact
- Already enforced by `src/sonic_xrpl/protocol/capability_matrix.py` and the V2 audit validator.
- No change required in Phase 48.

### Status
**Monitored** — No change. Capability matrix enforces correctness.

---

## 6. account_tx / Clio / Metadata Context

### Source
- **URL**: https://xrpl.org/docs/references/http-websocket-apis/public-api-methods/account-methods/account_tx
- **URL**: https://xrpl.org/docs/references/protocol/transactions/metadata

### Key Points
- `account_tx` returns validated transactions; `tx_type` filtering is Clio-only (Clio v2.0+).
- Payments should use `delivered_amount` rather than `Amount`.
- `AffectedNodes` describes created/modified/deleted ledger entries in metadata.
- Clio is a read/historical provider only — never a submission endpoint.

### Architecture Impact
- All these constraints are already encoded in Phase 46/47 fixture provider and metadata parser.
- No change required in Phase 48.

### Status
**Research-only** — Documented for completeness.

---

## 7. CI/Security Tooling

### Recommended GitHub Actions Versions (currently used)
| Action | Version Used | Latest Stable |
|--------|-------------|---------------|
| `actions/checkout` | v4 | v4 ✅ |
| `actions/setup-python` | v5 | v5 ✅ |
| `actions/upload-artifact` | v4 | v4 ✅ |

### pip-audit in CI
- Recommended: run `python -m pip_audit` after installing dev dependencies.
- Network access is available in standard GitHub-hosted runners (`ubuntu-latest`).
- If pip-audit finds vulnerabilities, CI should fail (exit 1) unless explicitly ignored.
- Audit report artifacts should be uploaded for visibility.

### Status
**Implemented** — `dependency-audit` CI job added to `.github/workflows/ci.yml`.

---

## 8. Summary of Findings

| Finding | Severity | Action |
|---------|----------|--------|
| xrpl.js 4.2.1–4.2.4 and 2.14.2 are compromised | Critical | Detect and fail audit if found |
| No `package.json` in this repo (no Node) | N/A | Report `not_applicable` |
| xrpl-py at `>=2.6.0` constraint | Low risk | Monitor; no unsafe versions known |
| pip check passes with no broken deps | Pass | Continue monitoring |
| pip-audit not installed by default | Warning | Add as dev dep; warn if unavailable |
| rippled 3.1.2 security release | Informational | Not operator — no action needed |
| Batch amendment disabled/vulnerable | Informational | Already excluded from capability matrix |

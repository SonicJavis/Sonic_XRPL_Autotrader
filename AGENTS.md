# Sonic XRPL Autotrader Agent Instructions

## Purpose

Agents help maintain and improve Sonic XRPL Autotrader through phase-based work, audits, reconciliation checks, simulation validation, tests, documentation, and carefully scoped implementation. This project is safety-critical: agent work must preserve the separation between intelligence, simulation, paper records, lifecycle/reconciliation, and any future live execution boundary.

## Default Operating Mode

- Read-only audit mode by default.
- Only make code changes when a phase prompt explicitly authorizes them.
- Prefer small, reviewable changes.
- Preserve simulation/live separation.
- Do not silently alter trading behaviour.

## Hard Safety Boundaries

- Never request, store, print, or commit wallet seeds, private keys, mnemonics, or secrets.
- Never add auto-signing or live transaction submission unless explicitly required by a named phase.
- Never change live-network execution paths during audit/docs phases.
- Never weaken simulation, reconciliation, validation, or safety checks.
- Never enable ECC hooks, MCP servers, installers, or autonomous loops without explicit approval.
- Never modify global user/tool config.
- Never run destructive git commands unless explicitly requested.

## Phase Work Standard

Every phase must produce:

- objective completed
- files changed
- commands run
- validation results
- safety/risk notes
- rollback notes
- next recommended step

## Validation Standard

Use practical validation for this repo:

- Check `git status --short` before and after.
- Run targeted tests for touched modules.
- Run broader `pytest` when feasible.
- Run CLI smoke checks when CLI files are touched.
- Run security grep before recommending commit.
- Update docs/reports when behaviour changes.

## Security Grep

PowerShell-friendly commands:

```powershell
rg -n "seed|secret|private key|mnemonic|familySeed|wallet|sign|submitAndWait|autofill|classicAddress|api_key|token|password" .
rg -n "curl|wget|Invoke-WebRequest|iwr|irm|Start-Process|Remove-Item|rm -rf|ssh|scp|nc " .
rg -n "ANTHROPIC_BASE_URL|enableAllProjectMcpServers|allowedTools|autoApprove|dangerously|bypass" .
```

If `rg` is unavailable, use `git grep` or PowerShell `Select-String` and document the fallback.

## ECC Reference Policy

- `.ecc-source` is local reference material only.
- Agents may inspect it for ideas relevant to testing, audits, documentation, and security review.
- Agents must not execute ECC installers.
- Agents must not copy ECC hooks or MCP configs.
- Agents must not modify global config.
- Only adapt small, useful, project-local patterns that improve Sonic XRPL Autotrader.

## Commit Hygiene

- Never commit `.ecc-source/`.
- Never commit secrets.
- Avoid committing generated artifacts unless the phase requires them.
- Keep docs/audit workflow commits separate from runtime trading code commits where practical.

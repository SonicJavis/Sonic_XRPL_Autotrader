# Sonic XRPL Autotrader Agent Workflow

## What Agents Should Help With

- repo audits
- phase reconstruction
- reconciliation validation
- simulation-only execution checks
- test creation and test repair
- safety review
- documentation updates
- CLI smoke checks
- report generation

## What Needs Explicit Approval

- live execution changes
- wallet/signing changes
- dependency changes
- CI/CD changes
- enabling hooks/MCPs
- external installers
- changes to generated artifacts

## Forbidden By Default

- real wallet seed/private key handling
- auto-signing
- live trading
- global config changes
- ECC hook/MCP adoption
- destructive git operations
- hidden autonomous loops

## Standard Phase Prompt Template

```text
Phase:
Objective:
Scope:
Allowed files:
Forbidden files/actions:
Allowed commands:
Required validation:
Required report:
```

## Pre-Commit Checklist

- git status checked
- no `.ecc-source/` staged
- no secrets
- targeted tests passed
- security grep reviewed
- rollback notes included
- final summary written

## ECC Usage

- ECC remains ignored in `.ecc-source/`.
- ECC is reference-only.
- Do not install/enable/copy hooks/MCPs.
- Adapt only small project-local ideas that directly improve Sonic XRPL Autotrader.

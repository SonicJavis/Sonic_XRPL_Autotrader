# ECC Adoption Audit

Date: 2026-05-03  
Project: `D:\Codex Projects\Sonic_XRPL_Autotrader`  
ECC source: `D:\Codex Projects\Sonic_XRPL_Autotrader\.ecc-source`  
ECC commit inspected: `841beea fix: handle dotted reserved snapshot names`

## Executive Summary

Recommendation: **partial adopt, reference-first**.

The cloned `everything-claude-code` repository is a broad agent operating toolkit with useful review, testing, documentation, and security patterns. It is also automation-heavy: installers mutate Claude/Cursor/OpenCode/Codex configuration, hooks execute Node commands on agent events, MCP configs launch `npx`/`uvx` servers and connect to external HTTP MCP endpoints, and some profiles encourage multi-agent/continuous-learning flows.

For this XRPL project, the safe path is **not** to install ECC globally or enable hooks/MCPs. Use ECC as a read-only reference library and selectively copy/adapt small prompt/checklist fragments only after review. Do not adopt ECC installers, bundled hooks, broad MCP configs, autonomous loop tools, or write-enabled agent configs without a separate security review.

## What Was Inspected

Read-only commands used:

- `git status --short`
- `git -C .ecc-source status --short`
- `git -C .ecc-source log --oneline -3`
- `Get-ChildItem`
- `git -C .ecc-source ls-files`
- `Get-Content`
- `Select-String`

No ECC install scripts were executed. No hooks, MCP servers, package installs, or ECC tests were run.

Important local state:

- The main project already had `artifacts/audit_validator_report.json` modified before this audit.
- `.ecc-source/` is currently untracked in the main project.
- This report is the only project file intentionally created by the audit.

Inspected surfaces:

- Root files: `README.md`, `AGENTS.md`, `CLAUDE.md`, `RULES.md`, `SECURITY.md`, `package.json`, `.mcp.json`, `.env.example`
- Installers: `install.sh`, `install.ps1`, `scripts/install-apply.js`, `scripts/install-plan.js`
- Agent definitions: `agents/`, `.agents/skills/*/agents/openai.yaml`, `.codex/agents/`, `.opencode/prompts/agents/`, `.kiro/agents/`
- Skills: `skills/`, `.agents/skills/`, `.claude/skills/`, `.cursor/skills/`, `.kiro/skills/`
- Rules: `rules/`, `.cursor/rules/`, `.claude/rules/`
- Hooks: `hooks/hooks.json`, `.cursor/hooks.json`, `.cursor/hooks/*.js`, `.kiro/hooks/*.hook`, `scripts/hooks/*`
- MCP configs: `.mcp.json`, `mcp-configs/mcp-servers.json`, `.codex/config.toml`
- Codex/Claude/Cursor/OpenCode configs: `.codex/`, `.claude/`, `.cursor/`, `.opencode/`, plugin metadata folders
- Security tooling references: `security-review`, `security-scan`, `harness-audit`, security rules, security reviewer agents, workflow security validators

## Available Components

### Agents

Top-level `agents/` contains 49 markdown agents, including:

- `architect.md`
- `code-explorer.md`
- `code-reviewer.md`
- `database-reviewer.md`
- `docs-lookup.md`
- `doc-updater.md`
- `e2e-runner.md`
- `harness-optimizer.md`
- `performance-optimizer.md`
- `planner.md`
- `python-reviewer.md`
- `refactor-cleaner.md`
- `security-reviewer.md`
- `silent-failure-hunter.md`
- `tdd-guide.md`

Additional agent configs exist for Codex, Cursor/OpenCode, Kiro, and `.agents/skills/*/agents/openai.yaml`.

### Skills

The root `skills/` directory includes many general and domain skills. Most relevant for this project:

- `python-patterns`
- `python-testing`
- `backend-patterns`
- `api-design`
- `tdd-workflow`
- `verification-loop`
- `security-review`
- `security-scan`
- `llm-trading-agent-security`
- `defi-amm-security`
- `documentation-lookup`
- `architecture-decision-records`
- `ai-regression-testing`
- `eval-harness`
- `repo-scan`
- `workspace-surface-audit`
- `git-workflow`
- `github-ops`

Reference-only or likely irrelevant:

- social/content/investor/outreach skills
- frontend-slides/media generation skills
- language stacks not used here
- autonomous-loop/continuous-learning skills
- third-party SaaS ops skills

### Rules

Rules are present under:

- `rules/common/*`
- `rules/python/*`
- `rules/web/*`
- language-specific rules for many stacks
- `.cursor/rules/*`
- `.claude/rules/*`

Useful references:

- `rules/common/security.md`
- `rules/python/security.md`
- `rules/python/testing.md`
- `rules/python/coding-style.md`
- `rules/web/security.md`

### Hooks

Hook systems exist in:

- `hooks/hooks.json`
- `.cursor/hooks.json`
- `.cursor/hooks/*.js`
- `.kiro/hooks/*.hook`
- `scripts/hooks/*`

Hook behaviors include pre/post shell checks, MCP checks, file-edit checks, config-protection, quality gates, session persistence, continuous-learning observation, cost tracking, desktop notifications, and stop hooks.

### MCP Configs

`.mcp.json` defines:

- GitHub via `npx @modelcontextprotocol/server-github`
- Context7 via `npx @upstash/context7-mcp`
- Exa via `https://mcp.exa.ai/mcp`
- Memory via `npx @modelcontextprotocol/server-memory`
- Playwright via `npx @playwright/mcp --extension`
- Sequential-thinking via `npx @modelcontextprotocol/server-sequential-thinking`

`mcp-configs/mcp-servers.json` additionally references Jira, Firecrawl, Supabase, Vercel, Railway, Cloudflare, ClickHouse, Magic UI, filesystem, fal.ai, Browserbase, browser-use, devfleet, token optimizer, Confluence, and EvalView.

### Codex / Claude / Cursor / OpenCode Configs

- `.codex/config.toml` sets `approval_policy = "on-request"`, `sandbox_mode = "workspace-write"`, `web_search = "live"`, MCP servers, notifications, persistent instructions, and multi-agent roles.
- `.codex/AGENTS.md` documents Codex skill/MCP usage and recommends MCP servers.
- `.claude/` contains commands, rules, team config, plugin identity, and ECC tools metadata.
- `.cursor/hooks.json` wires many hook events to Node commands.
- `.opencode/opencode.json` defines write-enabled agents and command templates.

### Install Scripts

- `install.ps1`: PowerShell wrapper that auto-runs `npm install` when `node_modules` is absent, then runs `node scripts/install-apply.js`.
- `install.sh`: Bash wrapper with the same auto-install behavior.
- `scripts/install-apply.js`: applies install plans and writes target configs.
- `scripts/install-plan.js`: read-only planner when used with listing/planning options, but still Node-based.

### Security Tools / Scanners

Useful reference files include:

- `agents/security-reviewer.md`
- `skills/security-review/`
- `skills/security-scan/`
- `rules/common/security.md`
- `rules/python/security.md`
- `the-security-guide.md`
- `scripts/harness-audit.js`
- `scripts/ci/validate-workflow-security.js`
- `scripts/hooks/insaits-security-monitor.py`
- `scripts/hooks/insaits-security-wrapper.js`

## Risk Findings

### High Risk: Installers Mutate Tooling State

`install.ps1` and `install.sh` are not safe to run during this project without a separate change plan. They can:

- run `npm install`
- invoke Node installer runtime
- write Claude/Cursor/agent config
- install hooks
- install MCP definitions

This conflicts with the current audit-only constraints and this project’s safety posture.

### High Risk: Hooks Execute Shell/Node Automatically

ECC hook configs contain many event-triggered commands. They can run on shell execution, file edit, MCP execution, session start/end, and stop events. Some hooks are designed to block, warn, format, typecheck, persist state, observe sessions, and monitor MCP health.

For this XRPL project, do not enable ECC hooks until each hook is reviewed and a project-local, fail-closed subset is defined.

### High Risk: MCP Surface Is Broad

ECC MCP configs include both local command servers and remote HTTP servers. Examples include GitHub, Exa, Playwright, Memory, filesystem, browser automation, cloud providers, SaaS integrations, and devfleet.

Risks:

- broad filesystem access if filesystem MCP is enabled
- external network access and credential handling
- accidental third-party mutations
- context bloat and prompt exposure
- MCP auto-tool availability beyond project needs

No MCP servers should be copied or enabled from ECC as-is.

### Medium Risk: Environment Overrides

ECC docs reference `ANTHROPIC_BASE_URL` and `ANTHROPIC_AUTH_TOKEN` for gateway use. These are not inherently malicious but should not be imported into this repo or shell profile. This project should avoid model-provider overrides unless explicitly needed and reviewed.

### Medium Risk: Write-Enabled Agent Defaults

OpenCode config includes agents with `write`, `edit`, and `bash` tools enabled. Some security/build agents are allowed to write. This is not appropriate for automatic adoption in a project with strict execution-safety invariants.

### Medium Risk: Continuous Learning / Session Persistence

ECC includes continuous-learning and session-state hooks. These may write local state, summarize transcripts, or persist observations. For a trading-adjacent project with sensitive safety constraints, keep these reference-only.

### Low/Expected Risk: Credential Placeholders

`.env.example` and MCP configs include placeholder tokens like `GITHUB_TOKEN`, API keys, and SaaS credentials. No real credentials were observed in the inspected output, but the configs are designed to receive credentials.

### Hidden Unicode / Prompt Injection Scan

A search for bidi/control Unicode characters hit binary PNG assets under `assets/images/*`, not text rules/configs. No text-based hidden-Unicode finding was identified from the sampled scan.

## Useful Components For This XRPL Project

### XRPL Python Backend

Use as reference only:

- `skills/python-patterns`
- `skills/python-testing`
- `skills/backend-patterns`
- `skills/api-design`
- `rules/python/security.md`
- `rules/python/testing.md`
- `agents/python-reviewer.md`
- `agents/code-reviewer.md`
- `agents/security-reviewer.md`

Potential adaptation:

- Create a project-local XRPL-specific review checklist inspired by these files.
- Keep focus on deterministic outputs, fail-closed behavior, no wallet/signing/submission paths, validated ledger semantics, and bounded numerical outputs.

### Test / Audit / Reconciliation Phases

Useful references:

- `skills/tdd-workflow`
- `skills/verification-loop`
- `skills/ai-regression-testing`
- `skills/eval-harness`
- `agents/tdd-guide.md`
- `agents/pr-test-analyzer.md`
- `agents/silent-failure-hunter.md`
- `scripts/harness-audit.js` as a design reference only

Recommended use:

- Extract checklist language for regression fixtures, safety grep, API contract tests, and deterministic replay tests.
- Do not adopt ECC’s Node harness directly.

### Docs / Report Generation

Useful references:

- `skills/documentation-lookup`
- `skills/architecture-decision-records`
- `skills/codebase-onboarding`
- `agents/doc-updater.md`
- `agents/docs-lookup.md`

Recommended use:

- Reference structure and sectioning for audit docs and handover reports.
- Do not enable documentation MCPs by default.

### GitHub / Codex / Claude Agent Workflows

Useful references:

- `.codex/agents/explorer.toml`
- `.codex/agents/reviewer.toml`
- `.codex/agents/docs-researcher.toml`
- `.codex/AGENTS.md`
- `agents/code-explorer.md`
- `agents/code-reviewer.md`

Recommended use:

- Copy ideas into local prompts only after trimming MCP and write-tool assumptions.
- Prefer read-only explorer/reviewer roles.
- Keep user approval required for push/PR/external actions.

## Components To Avoid Or Keep Reference-Only

Avoid installing or enabling:

- `install.ps1`
- `install.sh`
- `scripts/install-apply.js`
- `hooks/hooks.json`
- `.cursor/hooks.json`
- `.kiro/hooks/*`
- `.mcp.json`
- `mcp-configs/mcp-servers.json`
- `.codex/config.toml` as a wholesale copy
- `.opencode/opencode.json` as a wholesale copy
- `skills/autonomous-loops`
- `skills/continuous-agent-loop`
- `skills/continuous-learning`
- `skills/continuous-learning-v2`
- `skills/claude-devfleet`
- devfleet MCP
- filesystem MCP
- browser automation MCPs except task-scoped local Playwright already available in this environment
- SaaS MCPs requiring credentials
- media/social/outreach skills unrelated to XRPL work

## Recommended Minimal Adoption Plan

### Phase A: Keep ECC Read-Only

1. Leave `.ecc-source/` as reference material.
2. Do not stage `.ecc-source/` into the project unless deliberately vendoring a small subset later.
3. Add `.ecc-source/` to `.gitignore` only after deciding it should remain a local-only reference clone.

### Phase B: Create Project-Specific Checklists

Create local docs/checklists, not installed configs:

- `docs/checklists/XRPL_CODE_REVIEW_CHECKLIST.md`
- `docs/checklists/XRPL_TEST_VERIFICATION_CHECKLIST.md`
- `docs/checklists/XRPL_SECURITY_REVIEW_CHECKLIST.md`

Source inspiration:

- ECC `security-review`
- ECC `python-testing`
- ECC `verification-loop`
- ECC `code-reviewer`
- existing project phase audits

### Phase C: Optional Read-Only Agent Prompts

If agent prompts are desired, create project-local prompts that are explicitly read-only unless the current task asks for edits:

- XRPL protocol reviewer
- deterministic test reviewer
- safety grep reviewer
- API contract reviewer

Do not import ECC agent configs with write-enabled assumptions.

### Phase D: No MCP Adoption By Default

Use existing tools and project tests. Add MCPs only case-by-case:

- Documentation lookup: acceptable only when explicitly needed.
- GitHub: only if user asks for GitHub issue/PR work.
- Playwright: already available via local tooling; no need to import ECC MCP.

### Phase E: No Hooks Until Separate Hook Review

If hooks are later desired, write project-native hooks from scratch with narrow behavior:

- block edits to execution safety guards without explicit task scope
- run `pytest` command suggestions, not automatic mutation
- warn on forbidden XRPL terms

Do not use ECC hook bundles directly.

## Exact Next Commands - NOT EXECUTED

These are suggestions only. They were not executed during this audit.

```powershell
# Keep ECC clone local-only if desired
Add-Content .gitignore "`n.ecc-source/"

# Create project-local checklist directory
New-Item -ItemType Directory -Force docs\checklists

# Inspect a candidate ECC skill before adapting text manually
Get-Content .ecc-source\skills\security-review\SKILL.md
Get-Content .ecc-source\skills\python-testing\SKILL.md
Get-Content .ecc-source\skills\verification-loop\SKILL.md

# Verify project remains green after any future checklist-only docs change
.venv\Scripts\python.exe -m pytest

# Safety grep after any future adoption change
git grep -n -E "submit|sign|wallet|OfferCreate|Payment|autofill|secret|seed|path_find|ripple_path_find" -- app tests scripts execution_prototype docs
```

Do not run:

```powershell
# NOT RECOMMENDED
.\.ecc-source\install.ps1
bash .\.ecc-source\install.sh
npm install --prefix .ecc-source
Copy-Item .ecc-source\.mcp.json .
Copy-Item .ecc-source\hooks\hooks.json .
Copy-Item .ecc-source\.codex\config.toml .codex\config.toml
```

## Final Recommendation

**Partial adopt.**

Use ECC as a reference library for review checklists, testing discipline, documentation structure, and security thinking. Do not install or enable ECC components in this XRPL project yet. The automation, hooks, MCPs, and config layers are too broad for the project’s fail-closed, non-executing, safety-critical workflow without a separate controlled adoption phase.

Minimal safe adoption now:

- reference-only `.ecc-source`
- optionally ignore `.ecc-source/`
- manually distill a few project-specific checklist docs
- no hooks
- no MCPs
- no installer
- no global config mutation

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

## GitHub End-to-End Workflow Template

Use this template when assigning a master prompt to a coding agent that has local
git access and GitHub credentials. The agent should continue from task receipt
through merge unless a validation, safety, credential, or policy blocker is
encountered.

```text
You are working in a safety-critical repository. Complete this task end to end
using GitHub.

Task:
<describe the requested change/audit/fix>

Operating rules:
- Read the repository instructions and relevant docs before editing.
- Preserve all safety boundaries. Do not add wallet seed handling, private-key
  handling, signing, transaction submission, auto-buy, autonomous loops, or live
  execution unless this prompt explicitly authorizes that exact phase.
- Do not revert unrelated user changes.
- Keep changes small, reviewable, and scoped to the task.

Required GitHub workflow:
1. Check `git status --short --branch`.
2. Fetch current remote refs.
3. Create a new branch from current `origin/main` using `codex/<short-task-name>`.
4. Implement the requested change.
5. Run targeted tests for touched modules.
6. Run broad validation where feasible:
   - `python -m pytest`
   - `python scripts/safety_grep.py`
   - `python scripts/audit_validator.py`
7. Run any repo-specific security grep or smoke checks listed in the project
   instructions.
8. Check `git diff --check`.
9. Commit with a concise, descriptive message.
10. Push the branch to GitHub.
11. Open a pull request against `main`.
12. Mark the PR ready for review once validation is complete.
13. Merge the PR when it is mergeable and required checks are green or absent.
14. Fetch `origin/main` and verify the merge commit is present.
15. Report:
    - objective completed
    - files changed
    - commands run
    - validation results
    - safety/risk notes
    - rollback notes
    - PR URL and merge commit

Stop and report instead of merging if:
- validation fails and cannot be fixed safely
- the PR has unresolved requested changes
- GitHub branch protection blocks the merge
- credentials are unavailable
- the requested change conflicts with safety boundaries
- the repository has unrelated dirty changes that make the task unsafe to stage
```

## Cloud Coding Agent Workaround Template

Use this template for cloud coding agents that can edit and test code but cannot
push to the repository, cannot open PRs, or run in an environment without a
configured remote.

```text
You are a cloud coding agent working in a copy of the repository. Complete the
implementation and prepare a GitHub-ready handoff.

Task:
<describe the requested change/audit/fix>

Operating rules:
- Read the repository instructions and relevant docs before editing.
- Preserve all safety boundaries. Do not add wallet seed handling, private-key
  handling, signing, transaction submission, auto-buy, autonomous loops, or live
  execution unless this prompt explicitly authorizes that exact phase.
- Keep the patch small, reviewable, and scoped to the task.
- Do not claim the PR is merged unless you directly verify it on GitHub.

Required cloud workflow:
1. Check `git status --short --branch`.
2. Identify the intended base branch and commit SHA, preferably `origin/main`.
3. Implement the requested change.
4. Run targeted tests for touched modules.
5. Run broad validation where feasible:
   - `python -m pytest`
   - `python scripts/safety_grep.py`
   - `python scripts/audit_validator.py`
6. Run repo-specific security grep or smoke checks listed in the project
   instructions.
7. Check `git diff --check`.
8. Create a local commit if the environment allows commits.
9. Produce a handoff package containing:
   - branch name to create locally, e.g. `codex/<short-task-name>`
   - base commit SHA
   - local commit SHA, if created
   - full patch file via `git format-patch -1 HEAD` or `git diff`
   - files changed
   - commands run
   - validation output summary
   - safety/risk notes
   - rollback notes
   - proposed PR title and body

Human/local-agent follow-up:
1. On a machine with GitHub credentials, fetch latest `main`.
2. Create `codex/<short-task-name>` from `origin/main`.
3. Apply the cloud patch:
   - preferred: `git am <patch-file>`
   - fallback: apply the diff, inspect, then commit manually
4. Re-run validation locally.
5. Push the branch.
6. Open a PR against `main`.
7. Merge only after checks pass and the PR is mergeable.
8. Fetch `origin/main` and verify the merge commit is present.

Cloud-agent final response must clearly state one of:
- `READY_FOR_LOCAL_GITHUB_FLOW`: patch is prepared and validated, but not pushed.
- `BLOCKED`: explain the blocker and exact next action.
- `MERGED`: only if the agent directly pushed, opened the PR, merged it, and
  verified the merge on GitHub.
```

## Local Merge Checklist

Use this checklist before merging any coding-agent PR:

- PR branch is based on current `origin/main`.
- PR title/body explain scope, validation, and safety impact.
- Required tests and safety checks are green.
- No secrets, generated junk, `.ecc-source/`, or unrelated files are included.
- No live execution, signing, wallet, or submission path was added unless the
  approved phase explicitly required it.
- PR is not draft.
- GitHub reports the PR as mergeable.
- After merge, `origin/main` contains the merge commit.

## ECC Usage

- ECC remains ignored in `.ecc-source/`.
- ECC is reference-only.
- Do not install/enable/copy hooks/MCPs.
- Adapt only small project-local ideas that directly improve Sonic XRPL Autotrader.

## Local Validation on Windows

Use the virtual-environment interpreter for all local validation commands:

```powershell
.venv\Scripts\python.exe -m pip install -e ".[dev]"
.venv\Scripts\python.exe -m pytest
.venv\Scripts\python.exe scripts\safety_grep.py
.venv\Scripts\python.exe scripts\audit_validator.py
```

Do **not** use bare `python` — the system interpreter will not have `sqlmodel`,
`xrpl`, or other project dependencies installed.

## .ecc-source Exclusion From Safety Scans

`.ecc-source/` is explicitly excluded from `scripts/safety_grep.py` and
`src/sonic_xrpl/audit/safety_scan.py`.

Rationale — excluding `.ecc-source/` does **not** weaken runtime safety because:

- It is ignored by Git (listed in `.gitignore`).
- It is never committed to the repository.
- It is never installed or imported by any Sonic XRPL Autotrader code path.
- It is an external reference clone only; its strings (e.g. `background=`,
  widget styling) have no bearing on this project's execution safety.
- Any ECC-sourced pattern that does appear in project runtime code would still
  be caught by the scan because only `.ecc-source/` itself is excluded, not the
  patterns.

#!/usr/bin/env python3
"""Create a PR for Phase 49 offline FirstLedger signal contracts via GitHub REST API.

This script uses a GitHub personal access token provided in the GITHUB_TOKEN
environment variable. The token must have repo scope for the target repository.

Heads up: this script is self-contained (no external dependencies) and relies
only on the standard library so it can run in restricted environments.
"""

import os
import sys
import json
import urllib.request
import urllib.error

REPO_OWNER = "SonicJavis"  # update if you forked to another owner
REPO_NAME = "Sonic_XRPL_Autotrader"
HEAD_BRANCH = "codex/phase49-firstledger-signal-contracts"
BASE_BRANCH = "main"
TITLE = "Phase 49: Offline FirstLedger Signal Contracts"
BODY = (
    "Phase 49 offline signals: offline FirstLedger evidence-based signals; read-only; "
    "no live submission. Branch codex/phase49-firstledger-signal-contracts prepared from origin/main "
    "with changes merged from codex/implement-phase-49-signal-contracts. Validation: V2 audit 33/0/0; "
    "safety findings 107 require review (334 total). Next steps: CI gating and merge when ready."
)

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
if not GITHUB_TOKEN:
    print("ERROR: GITHUB_TOKEN environment variable is not set.")
    print("Set it to a GitHub token with repo scope and re-run.")
    sys.exit(3)

url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/pulls"
payload = {
    "title": TITLE,
    "head": HEAD_BRANCH,
    "base": BASE_BRANCH,
    "body": BODY,
}
data = json.dumps(payload).encode("utf-8")

req = urllib.request.Request(url, data=data, method="POST")
req.add_header("Authorization", f"token {GITHUB_TOKEN}")
req.add_header("Accept", "application/vnd.github+json")
req.add_header("Content-Type", "application/json")

try:
    with urllib.request.urlopen(req) as resp:
        resp_body = resp.read().decode("utf-8")
        result = json.loads(resp_body)
        pr_url = result.get("html_url") or result.get("url")
        print("PR URL:", pr_url)
        sys.exit(0)
except urllib.error.HTTPError as e:
    err = e.read().decode("utf-8")
    print(f"HTTP error creating PR: {e.code} {e.reason}")
    print(err[:1000])
    sys.exit(2)
except Exception as e:
    print("Failed to create PR:", e)
    sys.exit(1)

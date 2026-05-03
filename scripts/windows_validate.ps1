# scripts/windows_validate.ps1
# Phase 47.2 — Windows local validation runner
#
# Runs all safe local checks using the project virtual-environment interpreter.
# Does NOT connect to live XRPL, does NOT sign or submit transactions,
# does NOT mutate source code or trading state.
#
# Usage (from repo root):
#   .\scripts\windows_validate.ps1
#
# Prerequisites:
#   python -m venv .venv
#   .venv\Scripts\python.exe -m pip install -e ".[dev]"

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$REPO_ROOT = $PSScriptRoot | Split-Path -Parent
Set-Location $REPO_ROOT

$PYTHON = Join-Path $REPO_ROOT ".venv\Scripts\python.exe"

if (-not (Test-Path $PYTHON)) {
    Write-Error "Virtual environment not found at $PYTHON`nCreate it with: python -m venv .venv && .venv\Scripts\python.exe -m pip install -e '.[dev]'"
    exit 1
}

function Step {
    param([string]$Label, [scriptblock]$Body)
    Write-Host "`n==> $Label" -ForegroundColor Cyan
    & $Body
    if ($LASTEXITCODE -ne 0) {
        Write-Host "FAILED: $Label" -ForegroundColor Red
        exit $LASTEXITCODE
    }
    Write-Host "OK: $Label" -ForegroundColor Green
}

# ------------------------------------------------------------------
# 1. Show interpreter version
# ------------------------------------------------------------------
Step "Python version" {
    & $PYTHON --version
}

# ------------------------------------------------------------------
# 2. Ensure dev dependencies are installed
# ------------------------------------------------------------------
Step "Install dev dependencies" {
    & $PYTHON -m pip install -e ".[dev]" --quiet
}

# ------------------------------------------------------------------
# 3. Run tests
# ------------------------------------------------------------------
Step "pytest" {
    & $PYTHON -m pytest
}

# ------------------------------------------------------------------
# 4. Safety grep (no forbidden live-execution patterns)
# ------------------------------------------------------------------
Step "safety_grep" {
    & $PYTHON scripts\safety_grep.py
}

# ------------------------------------------------------------------
# 5. Audit validator
# ------------------------------------------------------------------
Step "audit_validator" {
    & $PYTHON scripts\audit_validator.py
}

# ------------------------------------------------------------------
# 6. V2 CLI smoke checks (PYTHONPATH=src, offline only)
# ------------------------------------------------------------------
$env:PYTHONPATH = "src"

Step "CLI --help" {
    & $PYTHON -m sonic_xrpl.cli.main --help
}

Step "CLI health" {
    & $PYTHON -m sonic_xrpl.cli.main health
}

Step "CLI capabilities" {
    & $PYTHON -m sonic_xrpl.cli.main capabilities
}

Step "CLI safety-scan" {
    & $PYTHON -m sonic_xrpl.cli.main safety-scan
}

Step "CLI market-snapshot" {
    & $PYTHON -m sonic_xrpl.cli.main market-snapshot --path tests/fixtures/xrpl
}

Step "CLI market-snapshot-report" {
    & $PYTHON -m sonic_xrpl.cli.main market-snapshot-report --path tests/fixtures/xrpl
}

Remove-Item Env:\PYTHONPATH

# ------------------------------------------------------------------
# Done
# ------------------------------------------------------------------
Write-Host "`n==> All Windows validation checks PASSED" -ForegroundColor Green
Write-Host "NOTE: artifacts/audit_validator_report.json may have been refreshed." -ForegroundColor Yellow
Write-Host "      If you do not want to commit the refreshed report, run:" -ForegroundColor Yellow
Write-Host "          git checkout -- artifacts/audit_validator_report.json" -ForegroundColor Yellow

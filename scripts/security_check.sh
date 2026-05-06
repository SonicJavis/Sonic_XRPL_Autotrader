#!/usr/bin/env bash
set -euo pipefail

echo "Running security checks..."

# Run lightweight secret scan (Python module-based)
echo "Scanning for secrets..."
python - <<'PY'
from security.secret_scanner import scan_for_secrets
findings = scan_for_secrets('.')
if findings:
  print("FOUND {} potential secret(s):".format(len(findings)))
  for path, line, content in findings:
    print(f"{path}:{line}: {content}")
else:
  print("No obvious secrets found.")
PY

echo "Running test scaffold for security scan..."
pytest -q tests/test_security_scan.py

echo "Security checks completed."

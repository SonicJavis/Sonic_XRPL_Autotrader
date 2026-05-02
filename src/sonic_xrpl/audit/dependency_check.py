"""Dependency security checker."""

from __future__ import annotations

import json
from pathlib import Path

COMPROMISED_XRPL_JS_VERSIONS = {
    "4.2.1", "4.2.2", "4.2.3", "4.2.4", "2.14.2"
}


def check_xrpl_js(repo_root: Path) -> list[tuple[str, bool, str]]:
    """Check package.json and lockfiles for compromised xrpl.js versions.

    Returns list of (check_name, passed, message) tuples.
    """
    results = []

    # Check package.json
    pkg_json = repo_root / "package.json"
    if pkg_json.exists():
        try:
            data = json.loads(pkg_json.read_text())
            for dep_section in ("dependencies", "devDependencies"):
                deps = data.get(dep_section, {})
                if "xrpl" in deps:
                    version = deps["xrpl"].lstrip("^~>=")
                    if version in COMPROMISED_XRPL_JS_VERSIONS:
                        results.append((
                            f"package.json xrpl@{version}",
                            False,
                            f"COMPROMISED xrpl.js version {version} in package.json",
                        ))
                    else:
                        results.append((
                            f"package.json xrpl@{version}",
                            True,
                            f"xrpl.js version {version} not in compromised list",
                        ))
        except Exception as e:
            results.append(("package.json parse", False, f"Could not parse package.json: {e}"))

    # Check package-lock.json
    lock = repo_root / "package-lock.json"
    if lock.exists():
        lock_text = lock.read_text()
        for v in COMPROMISED_XRPL_JS_VERSIONS:
            if v in lock_text:
                results.append((
                    f"package-lock.json xrpl@{v}",
                    False,
                    f"COMPROMISED xrpl.js version {v} found in package-lock.json",
                ))

    if not results:
        results.append((
            "xrpl.js check",
            True,
            "No package.json/lockfile found — no xrpl.js to check",
        ))

    return results


def check_xrpl_py_version(repo_root: Path) -> tuple[bool, str]:
    """Check that xrpl-py version meets minimum safe version."""
    try:
        import xrpl
        version = xrpl.__version__
        parts = [int(x) for x in version.split(".")[:2]]
        if parts >= [2, 6]:
            return True, f"xrpl-py {version} >= 2.6.0 (safe)"
        return False, f"xrpl-py {version} < 2.6.0 (upgrade recommended)"
    except Exception as e:
        return False, f"Could not check xrpl-py version: {e}"

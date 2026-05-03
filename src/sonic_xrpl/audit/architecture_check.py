"""Architecture checker — verifies V2 package structure is complete."""

from __future__ import annotations

from pathlib import Path

REQUIRED_PACKAGES = [
    "src/sonic_xrpl",
    "src/sonic_xrpl/core",
    "src/sonic_xrpl/protocol",
    "src/sonic_xrpl/providers",
    "src/sonic_xrpl/ingestion",
    "src/sonic_xrpl/intelligence",
    "src/sonic_xrpl/strategy",
    "src/sonic_xrpl/risk",
    "src/sonic_xrpl/simulation",
    "src/sonic_xrpl/execution",
    "src/sonic_xrpl/reconciliation",
    "src/sonic_xrpl/telemetry",
    "src/sonic_xrpl/storage",
    "src/sonic_xrpl/cli",
    "src/sonic_xrpl/audit",
    "src/sonic_xrpl/compatibility",
]


def check_package_structure(repo_root: Path) -> list[tuple[str, bool, str]]:
    """Check all required V2 packages exist."""
    results = []
    for pkg in REQUIRED_PACKAGES:
        full = repo_root / pkg
        init_py = full / "__init__.py"
        has_init = init_py.exists()
        results.append((
            pkg,
            has_init,
            f"OK: {pkg}/__init__.py" if has_init else f"MISSING __init__.py: {pkg}",
        ))
    return results


def check_no_circular_imports(repo_root: Path) -> tuple[bool, str]:
    """Quick heuristic check that core/ does not import from other V2 packages."""
    core_dir = repo_root / "src" / "sonic_xrpl" / "core"
    if not core_dir.exists():
        return False, "src/sonic_xrpl/core does not exist"

    violations = []
    for py_file in core_dir.glob("*.py"):
        if py_file.name == "__init__.py":
            continue
        text = py_file.read_text()
        # core/ should only import from sonic_xrpl.core itself
        for line in text.splitlines():
            if "from sonic_xrpl." in line and "from sonic_xrpl.core" not in line:
                violations.append(f"{py_file.name}: {line.strip()}")

    if violations:
        return False, f"Potential circular imports in core/: {violations}"
    return True, "No circular import violations detected in core/"

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType


def _load_v2_cli() -> ModuleType:
    repo_root = Path(__file__).resolve().parents[2]
    src_dir = repo_root / "src"
    cli_path = src_dir / "sonic_xrpl" / "cli" / "main.py"
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))
    parent_pkg = sys.modules.get("sonic_xrpl")
    src_pkg = str(src_dir / "sonic_xrpl")
    if parent_pkg is not None and hasattr(parent_pkg, "__path__") and src_pkg not in parent_pkg.__path__:
        parent_pkg.__path__.append(src_pkg)

    spec = importlib.util.spec_from_file_location("_sonic_xrpl_v2_cli_main", cli_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load V2 CLI from {cli_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main(argv: list[str] | None = None) -> int:
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    v2_cli = _load_v2_cli()
    return int(v2_cli.main(argv))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

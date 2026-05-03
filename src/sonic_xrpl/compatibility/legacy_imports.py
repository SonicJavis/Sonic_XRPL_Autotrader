"""Legacy import compatibility wrappers for V2."""

from __future__ import annotations


def try_import(module_path: str, attribute: str | None = None):
    """Safely import a module or attribute, returning None on failure."""
    try:
        import importlib
        mod = importlib.import_module(module_path)
        if attribute is not None:
            return getattr(mod, attribute, None)
        return mod
    except ImportError:
        return None

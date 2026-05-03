"""Thin re-export shim — scan_fixture_files lives in sonic_xrpl.audit.safety_scan."""

from sonic_xrpl.audit.safety_scan import scan_fixture_files  # noqa: F401

__all__ = ["scan_fixture_files"]

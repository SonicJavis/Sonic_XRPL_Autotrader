"""Compatibility bridge from the Phase 48 FirstLedger parser to Phase 49 signals."""

from __future__ import annotations

from pathlib import Path

from execution_prototype.discovery.firstledger_reader import parse_firstledger_fixture
from sonic_xrpl.signals.evidence import load_candidate_rows


def parse_source_backed_firstledger_events(fixture: str | Path):
    """Return strict parser events from a fixture without live calls."""
    return parse_firstledger_fixture(load_candidate_rows(fixture))

"""Tests for FixtureManifest loading."""
from __future__ import annotations
import json
from pathlib import Path
import pytest
from sonic_xrpl.providers.fixture_manifest import load_manifest, compute_fixture_id, compute_checksum
from sonic_xrpl.providers.errors import FixtureMissingError

FIXTURE_DIR = Path(__file__).parent.parent / "fixtures" / "xrpl"


def test_load_manifest_returns_fixture_manifest():
    manifest = load_manifest(FIXTURE_DIR)
    assert manifest.name == "synthetic_test_fixture"
    assert manifest.version == "1.0.0"
    assert manifest.network == "synthetic"
    assert manifest.ledger_min == 1000
    assert manifest.ledger_max == 1001


def test_manifest_fixture_id_deterministic():
    id1 = compute_fixture_id("foo", "1.0", "mainnet")
    id2 = compute_fixture_id("foo", "1.0", "mainnet")
    assert id1 == id2
    assert len(id1) == 64


def test_manifest_fixture_id_differs_by_network():
    id_main = compute_fixture_id("foo", "1.0", "mainnet")
    id_test = compute_fixture_id("foo", "1.0", "testnet")
    assert id_main != id_test


def test_manifest_checksum_deterministic():
    data = {"a": 1, "b": 2}
    c1 = compute_checksum(data)
    c2 = compute_checksum(data)
    assert c1 == c2
    assert len(c1) == 64


def test_manifest_missing_raises(tmp_path):
    with pytest.raises(FixtureMissingError):
        load_manifest(tmp_path)


def test_manifest_corrupt_raises(tmp_path):
    (tmp_path / "manifest.json").write_text("not valid json{{{")
    with pytest.raises(FixtureMissingError):
        load_manifest(tmp_path)


def test_manifest_has_fixture_id():
    manifest = load_manifest(FIXTURE_DIR)
    assert len(manifest.fixture_id) == 64


def test_manifest_limitations_list():
    manifest = load_manifest(FIXTURE_DIR)
    assert isinstance(manifest.limitations, list)
    assert len(manifest.limitations) > 0

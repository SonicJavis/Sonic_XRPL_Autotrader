"""Tests for manifest builder and source hash computation."""

from __future__ import annotations

from sonic_xrpl.market.manifest import (
    compute_source_hash,
    compute_snapshot_id,
    build_snapshot_manifest,
)


class TestManifest:
    def test_source_hash_deterministic(self):
        data = {"a": 1, "b": 2}
        assert compute_source_hash(data) == compute_source_hash(data)

    def test_source_hash_differs_for_different_data(self):
        assert compute_source_hash({"a": 1}) != compute_source_hash({"a": 2})

    def test_source_hash_length(self):
        assert len(compute_source_hash({})) == 64

    def test_snapshot_id_deterministic(self):
        s1 = compute_snapshot_id("fixture1", 1000, "2026-05-03T00:00:00")
        s2 = compute_snapshot_id("fixture1", 1000, "2026-05-03T00:00:00")
        assert s1 == s2

    def test_snapshot_id_differs_by_ledger(self):
        s1 = compute_snapshot_id("fixture1", 1000, "2026-05-03T00:00:00")
        s2 = compute_snapshot_id("fixture1", 1001, "2026-05-03T00:00:00")
        assert s1 != s2

    def test_build_snapshot_manifest(self):
        m = build_snapshot_manifest(
            fixture_id="abc123",
            ledger_index=1000,
            input_paths=["tests/fixtures/xrpl"],
            limitations=["synthetic data"],
            source_hash="deadbeef" * 8,
        )
        assert m.fixture_id == "abc123"
        assert len(m.snapshot_id) == 64
        assert m.builder_version.startswith("2.0.0")
        assert m.limitations == ["synthetic data"]

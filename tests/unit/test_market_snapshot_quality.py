"""Tests for snapshot quality scorer."""

from __future__ import annotations

import pytest
from sonic_xrpl.market.quality import score_snapshot
from sonic_xrpl.market.models import SnapshotRecommendation


def _full_score(**overrides):
    defaults = dict(
        manifest_valid=True,
        has_amm_data=True,
        amm_requested=True,
        has_orderbook_data=True,
        has_metadata=True,
        metadata_sufficient_truth=True,
        has_mpt_data=True,
        mpt_requested=True,
        has_account_data=True,
        account_requested=True,
        capability_warnings=[],
        fixture_warnings=[],
    )
    defaults.update(overrides)
    return score_snapshot(**defaults)


class TestQualityScorer:
    def test_perfect_score(self):
        q = _full_score()
        assert q.score == 100
        assert q.recommendation == SnapshotRecommendation.USABLE_FOR_SIMULATION

    def test_invalid_manifest_rejected(self):
        q = _full_score(manifest_valid=False)
        assert q.score == 0
        assert q.recommendation == SnapshotRecommendation.REJECTED

    def test_missing_metadata_deducts(self):
        q = _full_score(has_metadata=False)
        assert q.score == 80
        assert "metadata" in q.missing_sections

    def test_insufficient_truth_deducts(self):
        q = _full_score(metadata_sufficient_truth=False)
        assert q.score == 85
        assert any("tesSUCCESS" in w for w in q.protocol_warnings)

    def test_missing_amm_deducts(self):
        q = _full_score(has_amm_data=False)
        assert q.score == 90
        assert "amm" in q.missing_sections

    def test_missing_orderbook_deducts(self):
        q = _full_score(has_orderbook_data=False)
        assert q.score == 90
        assert "orderbook" in q.missing_sections

    def test_missing_mpt_deducts(self):
        q = _full_score(has_mpt_data=False)
        assert q.score == 95
        assert "mpt" in q.missing_sections

    def test_capability_warnings_deduct(self):
        q = _full_score(capability_warnings=["warning1", "warning2"])
        assert q.score == 90  # 2 * 5 = 10 deducted

    def test_capability_warning_deduction_capped(self):
        # 5 warnings × 5 = 25 but capped at 20
        q = _full_score(capability_warnings=["w1", "w2", "w3", "w4", "w5"])
        assert q.score == 80

    def test_fixture_warnings_deduct(self):
        q = _full_score(fixture_warnings=["warn1"])
        assert q.score == 95

    def test_xahau_hooks_does_not_improve(self):
        q = _full_score(xahau_hooks_context=True)
        assert q.score == 100  # no score boost
        assert any("Xahau" in w for w in q.protocol_warnings)

    def test_insufficient_data_threshold(self):
        # Missing metadata (−20) + missing orderbook (−10) + missing amm (−10) + missing mpt (−5) = −45
        q = _full_score(
            has_metadata=False,
            has_orderbook_data=False,
            has_amm_data=False,
            has_mpt_data=False,
        )
        assert q.score == 55
        assert q.recommendation == SnapshotRecommendation.USABLE_FOR_RESEARCH

    def test_rejected_threshold(self):
        # Pile on many deductions to get below 20
        q = _full_score(
            has_metadata=False,
            has_orderbook_data=False,
            has_amm_data=False,
            has_mpt_data=False,
            has_account_data=False,
            metadata_sufficient_truth=False,
            capability_warnings=["w1", "w2", "w3", "w4"],
            fixture_warnings=["f1", "f2", "f3", "f4"],
        )
        assert q.score <= 19
        assert q.recommendation == SnapshotRecommendation.REJECTED

    def test_coverage_dict(self):
        q = _full_score()
        assert q.coverage["manifest"] is True
        assert q.coverage["amm"] is True
        assert q.coverage["orderbook"] is True
        assert q.coverage["metadata"] is True

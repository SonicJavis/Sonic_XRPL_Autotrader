"""Tests for simulation models — must be deterministic."""

from __future__ import annotations

import pytest
from sonic_xrpl.simulation.fill_model import FillModelType, FillEstimate, estimate_fill
from sonic_xrpl.simulation.slippage import SlippageEstimate, estimate_slippage
from sonic_xrpl.simulation.fees import FeeEstimate, estimate_fee
from sonic_xrpl.simulation.latency import LatencyEstimate, estimate_latency


class TestFillModel:
    def test_fixed_model_deterministic(self):
        """Fixed fill model returns same result for same input."""
        result1 = estimate_fill(100.0, FillModelType.FIXED)
        result2 = estimate_fill(100.0, FillModelType.FIXED)
        assert result1.expected_fill_pct == result2.expected_fill_pct

    def test_fill_pct_in_range(self):
        """Fill percentage must be in [0, 1]."""
        result = estimate_fill(100.0)
        assert 0.0 <= result.expected_fill_pct <= 1.0

    def test_no_guaranteed_full_fill(self):
        """Fill model should not guarantee 100% fill for large amounts."""
        result = estimate_fill(1_000_000.0, FillModelType.AMM_IMPACT, pool_size=100.0)
        assert result.expected_fill_pct < 1.0

    def test_amm_impact_model(self):
        """AMM impact model returns valid fill estimate."""
        result = estimate_fill(1000.0, FillModelType.AMM_IMPACT, pool_size=1_000_000.0)
        assert 0.0 <= result.expected_fill_pct <= 1.0
        assert result.model_type == FillModelType.AMM_IMPACT


class TestSlippage:
    def test_slippage_deterministic(self):
        """Slippage estimate is deterministic."""
        r1 = estimate_slippage(100.0)
        r2 = estimate_slippage(100.0)
        assert r1.basis_points == r2.basis_points

    def test_higher_amount_more_slippage(self):
        """Larger trades have more slippage."""
        small = estimate_slippage(10.0)
        large = estimate_slippage(10_000.0)
        assert large.basis_points >= small.basis_points

    def test_slippage_non_negative(self):
        """Slippage cannot be negative."""
        result = estimate_slippage(100.0)
        assert result.basis_points >= 0


class TestFees:
    def test_base_fee_is_12_drops(self):
        """Base XRPL fee is 12 drops for standard transactions."""
        fee = estimate_fee("Payment")
        assert fee.base_fee_drops == 12

    def test_escalated_fee_gte_base(self):
        """Escalated fee >= base fee."""
        fee = estimate_fee()
        assert fee.escalated_fee_drops >= fee.base_fee_drops

    def test_fee_deterministic(self):
        """Fee estimate is deterministic for same inputs."""
        f1 = estimate_fee("Payment", 1.0)
        f2 = estimate_fee("Payment", 1.0)
        assert f1.base_fee_drops == f2.base_fee_drops


class TestLatency:
    def test_latency_reasonable(self):
        """Latency should be in a reasonable range for XRPL."""
        lat = estimate_latency()
        assert lat.ledger_close_ms >= 3000
        assert lat.ledger_close_ms <= 5000
        assert lat.total_ms > lat.ledger_close_ms

    def test_worst_case_latency_higher(self):
        """Worst-case latency >= normal latency."""
        normal = estimate_latency()
        worst = estimate_latency(worst_case=True)
        assert worst.ledger_close_ms >= normal.ledger_close_ms

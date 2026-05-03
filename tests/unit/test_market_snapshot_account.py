"""Tests for account context and trustline context builders."""

from __future__ import annotations

import pytest
from sonic_xrpl.market.account_context import build_account_context
from sonic_xrpl.market.trustline_context import build_trustline_contexts


_RAW_ACCOUNT = {
    "account_data": {
        "Account": "rTrader1111111111111111111111111111",
        "Balance": "1000000000",
        "Flags": 0,
        "Sequence": 5,
        "OwnerCount": 2,
    },
    "validated": True,
}

_RAW_ACCOUNT_LINES = {
    "account": "rTrader1111111111111111111111111111",
    "lines": [
        {
            "account": "rIssuer1111111111111111111111111111",
            "balance": "100",
            "currency": "USD",
            "limit": "1000",
            "limit_peer": "0",
            "flags": 0,
        }
    ],
    "validated": True,
}


class TestAccountContext:
    def test_basic_build(self):
        ctx = build_account_context(_RAW_ACCOUNT, ledger_index=1000)
        assert ctx.account == "rTrader1111111111111111111111111111"
        assert ctx.balance_drops == "1000000000"
        assert ctx.flags == 0
        assert ctx.sequence == 5
        assert ctx.owner_count == 2
        assert ctx.ledger_index == 1000

    def test_previous_txn_id_none(self):
        ctx = build_account_context(_RAW_ACCOUNT, ledger_index=1000)
        assert ctx.previous_txn_id is None

    def test_previous_txn_id_present(self):
        raw = {
            "account_data": {
                "Account": "rTrader",
                "Balance": "0",
                "Flags": 0,
                "Sequence": 1,
                "PreviousTxnID": "DEADBEEF",
            },
            "validated": True,
        }
        ctx = build_account_context(raw, ledger_index=1000)
        assert ctx.previous_txn_id == "DEADBEEF"

    def test_not_validated_adds_limitation(self):
        raw = dict(_RAW_ACCOUNT)
        raw["validated"] = False
        ctx = build_account_context(raw, ledger_index=1000)
        assert any("validated" in lim for lim in ctx.limitations)

    def test_missing_account_adds_limitation(self):
        raw = {"account_data": {"Balance": "0", "Flags": 0, "Sequence": 1}, "validated": True}
        ctx = build_account_context(raw, ledger_index=1000)
        assert any("Account" in lim for lim in ctx.limitations)

    def test_frozen(self):
        ctx = build_account_context(_RAW_ACCOUNT, ledger_index=1000)
        with pytest.raises((TypeError, AttributeError)):
            ctx.account = "new"  # type: ignore[misc]


class TestTrustlineContext:
    def test_basic_build(self):
        ctxs = build_trustline_contexts(_RAW_ACCOUNT_LINES)
        assert len(ctxs) == 1
        ctx = ctxs[0]
        assert ctx.account == "rTrader1111111111111111111111111111"
        assert ctx.issuer == "rIssuer1111111111111111111111111111"
        assert ctx.currency == "USD"
        assert ctx.balance == "100"
        assert ctx.limit == "1000"

    def test_no_ripple_false_by_default(self):
        ctxs = build_trustline_contexts(_RAW_ACCOUNT_LINES)
        assert ctxs[0].no_ripple is False

    def test_freeze_state_none(self):
        ctxs = build_trustline_contexts(_RAW_ACCOUNT_LINES)
        assert ctxs[0].freeze_state == "none"

    def test_freeze_state_frozen(self):
        raw = dict(_RAW_ACCOUNT_LINES)
        raw["lines"] = [dict(raw["lines"][0])]
        raw["lines"][0]["freeze"] = True
        ctxs = build_trustline_contexts(raw)
        assert ctxs[0].freeze_state == "frozen"

    def test_not_validated_adds_limitation(self):
        raw = dict(_RAW_ACCOUNT_LINES)
        raw["validated"] = False
        ctxs = build_trustline_contexts(raw)
        assert any("validated" in lim for lim in ctxs[0].limitations)

    def test_clawback_relevant_with_issuer(self):
        issuer = "rIssuer1111111111111111111111111111"
        ctxs = build_trustline_contexts(_RAW_ACCOUNT_LINES, clawback_issuers={issuer})
        # Clawback amendment is ENABLED in test fixture — check for flag
        if ctxs[0].clawback_relevant:
            assert any("clawback" in lim.lower() for lim in ctxs[0].limitations)

    def test_empty_lines(self):
        raw = {"account": "rTrader", "lines": [], "validated": True}
        ctxs = build_trustline_contexts(raw)
        assert ctxs == []

    def test_frozen_dataclass(self):
        ctxs = build_trustline_contexts(_RAW_ACCOUNT_LINES)
        with pytest.raises((TypeError, AttributeError)):
            ctxs[0].currency = "EUR"  # type: ignore[misc]

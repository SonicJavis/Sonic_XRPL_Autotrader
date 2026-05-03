"""Trustline context builder — Phase 47.

Reads account_lines fixture data. No live calls.
Surfaces NoRipple, freeze, deep-freeze, and clawback relevance.
"""

from __future__ import annotations

from typing import Any

from sonic_xrpl.market.models import TrustlineContext
from sonic_xrpl.protocol.capability_matrix import is_capability_available

# Capability names
_CLAWBACK_CAP = "Clawback"
_DEEPFREEZE_CAP = "DeepFreeze"

# XRPL trust line flag bits (lsfNoRipple, lsfFreeze, lsfHighNoRipple, etc.)
_LSF_NO_RIPPLE = 0x00020000
_LSF_FREEZE = 0x00400000


def _freeze_state(flags: int, no_ripple_field: bool | None, freeze_field: bool | None) -> str:
    """Derive freeze state from trust line flags and fields."""
    # Deep-freeze is indicated by the DeepFreeze amendment context
    # For fixtures, we rely on the 'freeze' field from account_lines
    if freeze_field:
        return "frozen"
    if flags & _LSF_FREEZE:
        return "frozen"
    return "none"


def build_trustline_contexts(
    raw_account_lines: dict[str, Any],
    clawback_issuers: set[str] | None = None,
) -> list[TrustlineContext]:
    """Build TrustlineContext objects from raw account_lines fixture data."""
    clawback_issuers = clawback_issuers or set()
    lines = raw_account_lines.get("lines", [])
    contexts: list[TrustlineContext] = []

    for line in lines:
        limitations: list[str] = []

        account = raw_account_lines.get("account", "")
        issuer = line.get("account", "")     # counterparty is the issuer
        currency = line.get("currency", "")
        balance = str(line.get("balance", "0"))
        limit = str(line.get("limit", "0"))
        flags = int(line.get("flags", 0))

        no_ripple_field = line.get("no_ripple", False)
        no_ripple = bool(no_ripple_field) or bool(flags & _LSF_NO_RIPPLE)

        freeze_field = line.get("freeze", False)
        freeze_st = _freeze_state(flags, no_ripple_field, freeze_field)

        # DeepFreeze: if DeepFreeze amendment is enabled, check for deep-freeze indicator
        if is_capability_available(_DEEPFREEZE_CAP):
            deep_freeze_field = line.get("deep_freeze", False) or line.get("lsfDeepFreeze", False)
            if deep_freeze_field:
                freeze_st = "deep_frozen"

        clawback_rel = is_capability_available(_CLAWBACK_CAP) and issuer in clawback_issuers
        if clawback_rel:
            limitations.append(f"issuer {issuer} has clawback enabled — token may be reclaimed")

        if not raw_account_lines.get("validated", False):
            limitations.append("account_lines not from a validated ledger")

        contexts.append(TrustlineContext(
            account=account,
            issuer=issuer,
            currency=currency,
            balance=balance,
            limit=limit,
            flags=flags,
            no_ripple=no_ripple,
            freeze_state=freeze_st,
            clawback_relevant=clawback_rel,
            limitations=limitations,
        ))

    return contexts

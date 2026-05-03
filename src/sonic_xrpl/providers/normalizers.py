"""Asset/identifier normalization for XRPL."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class NormalizedAssetKey:
    currency: str
    issuer: str | None  # None for XRP

    def __str__(self) -> str:
        return "XRP" if self.issuer is None else f"{self.currency}:{self.issuer}"


_HEX64_RE = re.compile(r'^[0-9A-Fa-f]{64}$')
_ACCOUNT_RE = re.compile(r'^r[1-9A-HJ-NP-Za-km-z]{24,34}$')


def normalize_account(account: str) -> str:
    """Validate and normalize XRPL account address."""
    if not isinstance(account, str):
        raise ValueError(f"Account must be a string, got {type(account)}")
    account = account.strip()
    if not account:
        raise ValueError("Account address cannot be empty")
    return account


def normalize_currency(currency: str) -> str:
    """Normalize currency code to uppercase."""
    if not isinstance(currency, str):
        raise ValueError(f"Currency must be a string, got {type(currency)}")
    currency = currency.strip().upper()
    if not currency:
        raise ValueError("Currency code cannot be empty")
    return currency


def normalize_asset_key(currency: str, issuer: str | None) -> NormalizedAssetKey:
    """Create NormalizedAssetKey with validation."""
    currency = normalize_currency(currency)
    if currency == "XRP":
        if issuer is not None:
            raise ValueError("XRP is a native asset and must not have an issuer")
        return NormalizedAssetKey(currency="XRP", issuer=None)
    else:
        if issuer is None:
            raise ValueError(f"IOU currency '{currency}' requires an issuer")
        issuer = normalize_account(issuer)
        return NormalizedAssetKey(currency=currency, issuer=issuer)


def parse_asset_key(key: str) -> NormalizedAssetKey:
    """Parse asset key string: 'XRP' or 'USD:rIssuerXXX'."""
    if not isinstance(key, str):
        raise ValueError(f"Asset key must be a string, got {type(key)}")
    key = key.strip()
    if key.upper() == "XRP":
        return NormalizedAssetKey(currency="XRP", issuer=None)
    parts = key.split(":", 1)
    if len(parts) != 2:
        raise ValueError(f"Ambiguous asset key: '{key}'. Expected 'XRP' or 'CURRENCY:issuer'")
    currency, issuer = parts
    return normalize_asset_key(currency, issuer)


def normalize_ledger_index(idx: int | str) -> int:
    """Normalize ledger index to non-negative integer."""
    try:
        value = int(idx)
    except (ValueError, TypeError) as exc:
        raise ValueError(f"Ledger index must be an integer, got {idx!r}") from exc
    if value < 0:
        raise ValueError(f"Ledger index must be non-negative, got {value}")
    return value


def normalize_tx_hash(tx_hash: str) -> str:
    """Normalize transaction hash to uppercase 64-char hex string."""
    if not isinstance(tx_hash, str):
        raise ValueError(f"Transaction hash must be a string, got {type(tx_hash)}")
    tx_hash = tx_hash.strip().upper()
    if not _HEX64_RE.match(tx_hash):
        raise ValueError(
            f"Transaction hash must be a 64-character hex string, got {tx_hash!r} (len={len(tx_hash)})"
        )
    return tx_hash


def normalize_amm_pair(
    asset_a: str,
    asset_b: str,
) -> tuple[NormalizedAssetKey, NormalizedAssetKey]:
    """Normalize an AMM asset pair."""
    return parse_asset_key(asset_a), parse_asset_key(asset_b)

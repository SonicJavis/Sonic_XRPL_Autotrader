"""Dataclasses for XRPL fixture data."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ServerInfoFixture:
    build_version: str
    complete_ledgers: str
    ledger_index: int
    ledger_hash: str
    close_time_iso: str
    server_state: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ServerInfoFixture":
        info = data.get("info", data)
        vl = info.get("validated_ledger", {})
        return cls(
            build_version=info.get("build_version", ""),
            complete_ledgers=info.get("complete_ledgers", ""),
            ledger_index=vl.get("ledger_index", 0),
            ledger_hash=vl.get("hash", ""),
            close_time_iso=str(vl.get("close_time", "")),
            server_state=info.get("server_state", ""),
        )


@dataclass
class LedgerFixture:
    ledger_index: int
    ledger_hash: str
    close_time_iso: str
    validated: bool
    transactions: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LedgerFixture":
        return cls(
            ledger_index=data["ledger_index"],
            ledger_hash=data["ledger_hash"],
            close_time_iso=data.get("close_time_iso", ""),
            validated=data.get("validated", True),
            transactions=data.get("transactions", []),
        )


@dataclass
class AccountInfoFixture:
    account: str
    balance_drops: str
    flags: int
    sequence: int
    validated: bool

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AccountInfoFixture":
        account_data = data.get("account_data", data)
        return cls(
            account=account_data.get("Account", ""),
            balance_drops=account_data.get("Balance", "0"),
            flags=account_data.get("Flags", 0),
            sequence=account_data.get("Sequence", 0),
            validated=data.get("validated", True),
        )


@dataclass
class AccountLineFixture:
    account: str
    balance: str
    currency: str
    issuer: str
    limit: str
    limit_peer: str
    quality_in: int
    quality_out: int

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AccountLineFixture":
        return cls(
            account=data.get("account", ""),
            balance=data.get("balance", "0"),
            currency=data.get("currency", ""),
            issuer=data.get("account", ""),
            limit=data.get("limit", "0"),
            limit_peer=data.get("limit_peer", "0"),
            quality_in=data.get("quality_in", 0),
            quality_out=data.get("quality_out", 0),
        )


@dataclass
class TransactionFixture:
    hash: str
    ledger_index: int
    transaction_type: str
    account: str
    metadata: dict[str, Any] = field(default_factory=dict)
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TransactionFixture":
        return cls(
            hash=data.get("hash", ""),
            ledger_index=data.get("ledger_index", 0),
            transaction_type=data.get("transaction_type", ""),
            account=data.get("account", ""),
            metadata=data.get("metadata", {}),
            raw=data,
        )


@dataclass
class OrderbookFixture:
    taker_gets: Any
    taker_pays: Any
    offers: list[dict[str, Any]] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "OrderbookFixture":
        return cls(
            taker_gets=data.get("taker_gets", "XRP"),
            taker_pays=data.get("taker_pays", {}),
            offers=data.get("offers", []),
        )


@dataclass
class AMMFixture:
    asset_a: Any
    asset_b: Any
    lp_token: dict[str, Any]
    trading_fee: int
    amm_account: str
    validated: bool

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AMMFixture":
        amm = data.get("amm", data)
        return cls(
            asset_a=amm.get("amount", "0"),
            asset_b=amm.get("amount2", {}),
            lp_token=amm.get("lp_token", {}),
            trading_fee=amm.get("trading_fee", 0),
            amm_account=amm.get("amm_account", ""),
            validated=data.get("validated", True),
        )


@dataclass
class MPTHolderFixture:
    mpt_issuance_id: str
    holders: list[dict[str, Any]] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MPTHolderFixture":
        return cls(
            mpt_issuance_id=data.get("mpt_issuance_id", ""),
            holders=data.get("holders", []),
        )

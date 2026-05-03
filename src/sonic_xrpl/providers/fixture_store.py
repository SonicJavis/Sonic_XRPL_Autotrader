"""FixtureStore — loads structured XRPL fixture data from a directory."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from sonic_xrpl.providers.errors import FixtureCorruptError, FixtureMissingError
from sonic_xrpl.providers.fixture_manifest import FixtureManifest, load_manifest

REQUIRED_DIRS = [
    "ledgers",
    "accounts",
    "account_lines",
    "account_tx",
    "transactions",
    "orderbooks",
    "amm",
    "metadata",
]

_SECRET_PATTERNS = [
    re.compile(r'\bseed\b', re.IGNORECASE),
    re.compile(r'\bprivate_key\b', re.IGNORECASE),
    re.compile(r'\bmnemonic\b', re.IGNORECASE),
]


class FixtureStore:
    """Loads and caches XRPL fixture data from a structured directory."""

    def __init__(self, fixture_dir: Path) -> None:
        self._dir = fixture_dir

    def _load_json(self, path: Path) -> dict[str, Any]:
        if not path.exists():
            raise FixtureMissingError(f"Fixture not found: {path}")
        try:
            return json.loads(path.read_text())
        except Exception as exc:
            raise FixtureCorruptError(f"Failed to parse fixture {path}: {exc}") from exc

    def load_manifest(self) -> FixtureManifest:
        return load_manifest(self._dir)

    def load_server_info(self) -> dict[str, Any]:
        return self._load_json(self._dir / "server_info.json")

    def load_ledger(self, ledger_index: int) -> dict[str, Any]:
        return self._load_json(self._dir / "ledgers" / f"ledger_{ledger_index}.json")

    def load_latest_ledger(self) -> dict[str, Any]:
        manifest = self.load_manifest()
        return self.load_ledger(manifest.ledger_max)

    def load_account_info(self, account: str) -> dict[str, Any]:
        exact = self._dir / "accounts" / f"{account}.json"
        if exact.exists():
            return self._load_json(exact)
        accounts_dir = self._dir / "accounts"
        if accounts_dir.exists():
            for f in accounts_dir.glob("*.json"):
                data = self._load_json(f)
                acct_data = data.get("account_data", {})
                if acct_data.get("Account", "") == account:
                    return data
                if f.stem.lower() == account.lower():
                    return data
        raise FixtureMissingError(f"Account info fixture not found for: {account}")

    def load_account_lines(self, account: str) -> dict[str, Any]:
        exact = self._dir / "account_lines" / f"{account}_lines.json"
        if exact.exists():
            return self._load_json(exact)
        lines_dir = self._dir / "account_lines"
        if lines_dir.exists():
            for f in lines_dir.glob("*_lines.json"):
                data = self._load_json(f)
                if data.get("account", "") == account:
                    return data
                stem = f.stem.replace("_lines", "")
                if stem.lower() == account.lower():
                    return data
        raise FixtureMissingError(f"Account lines fixture not found for: {account}")

    def load_account_tx(
        self,
        account: str,
        ledger_min: int | None = None,
        ledger_max: int | None = None,
    ) -> dict[str, Any]:
        exact = self._dir / "account_tx" / f"{account}_tx.jsonl"
        if exact.exists():
            txs = self._load_jsonl(exact, ledger_min=ledger_min, ledger_max=ledger_max)
            return {"account": account, "transactions": txs, "validated": True}
        tx_dir = self._dir / "account_tx"
        if tx_dir.exists():
            for f in tx_dir.glob("*_tx.jsonl"):
                stem = f.stem.replace("_tx", "")
                if stem.lower() == account.lower() or account.lower().startswith(stem.lower()):
                    txs = self._load_jsonl(f, ledger_min=ledger_min, ledger_max=ledger_max)
                    return {"account": account, "transactions": txs, "validated": True}
            # fallback: scan JSONL content for matching account
            for f in tx_dir.glob("*_tx.jsonl"):
                txs = self._load_jsonl(f, ledger_min=ledger_min, ledger_max=ledger_max)
                if any(t.get("account", "") == account for t in txs):
                    return {"account": account, "transactions": txs, "validated": True}
        raise FixtureMissingError(f"Account tx fixture not found for: {account}")

    def _load_jsonl(
        self,
        path: Path,
        ledger_min: int | None = None,
        ledger_max: int | None = None,
    ) -> list[dict[str, Any]]:
        txs = []
        for line in path.read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            li = obj.get("ledger_index", 0)
            if ledger_min is not None and li < ledger_min:
                continue
            if ledger_max is not None and li > ledger_max:
                continue
            txs.append(obj)
        return txs

    def load_transaction(self, tx_hash: str) -> dict[str, Any]:
        tx_dir = self._dir / "transactions"
        if tx_dir.exists():
            for f in tx_dir.glob("*.json"):
                data = self._load_json(f)
                if data.get("hash", "").upper() == tx_hash.upper():
                    return data
        acct_tx_dir = self._dir / "account_tx"
        if acct_tx_dir.exists():
            for f in acct_tx_dir.glob("*.jsonl"):
                for line in f.read_text().splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                        if obj.get("hash", "").upper() == tx_hash.upper():
                            return obj
                    except Exception:
                        continue
        raise FixtureMissingError(f"Transaction fixture not found for hash: {tx_hash}")

    def load_orderbook(self, asset_a: str, asset_b: str) -> dict[str, Any]:
        ob_dir = self._dir / "orderbooks"
        if ob_dir.exists():
            filename = f"{asset_a}_{asset_b}.json"
            path = ob_dir / filename
            if path.exists():
                return self._load_json(path)
            filename_rev = f"{asset_b}_{asset_a}.json"
            path_rev = ob_dir / filename_rev
            if path_rev.exists():
                return self._load_json(path_rev)
            for f in ob_dir.glob("*.json"):
                return self._load_json(f)
        raise FixtureMissingError(f"Orderbook fixture not found for: {asset_a}/{asset_b}")

    def load_amm_info(self, asset_a: str, asset_b: str) -> dict[str, Any]:
        amm_dir = self._dir / "amm"
        if amm_dir.exists():
            filename = f"{asset_a}_{asset_b}.json"
            path = amm_dir / filename
            if path.exists():
                return self._load_json(path)
            filename_rev = f"{asset_b}_{asset_a}.json"
            path_rev = amm_dir / filename_rev
            if path_rev.exists():
                return self._load_json(path_rev)
            for f in amm_dir.glob("*.json"):
                return self._load_json(f)
        raise FixtureMissingError(f"AMM fixture not found for: {asset_a}/{asset_b}")

    def load_mpt_holders(self, mpt_issuance_id: str) -> dict[str, Any]:
        mpt_dir = self._dir / "mpt"
        if mpt_dir.exists():
            specific = mpt_dir / f"holders_{mpt_issuance_id}.json"
            if specific.exists():
                return self._load_json(specific)
            sample = mpt_dir / "holders_sample.json"
            if sample.exists():
                return self._load_json(sample)
            for f in mpt_dir.glob("*.json"):
                return self._load_json(f)
        raise FixtureMissingError(f"MPT holders fixture not found for: {mpt_issuance_id}")

    def validate_health(self) -> dict[str, Any]:
        issues = []
        manifest_ok = False
        dirs_ok: dict[str, bool] = {}
        secret_scan_ok = True

        try:
            self.load_manifest()
            manifest_ok = True
        except Exception as exc:
            issues.append(f"manifest: {exc}")

        for d in REQUIRED_DIRS:
            exists = (self._dir / d).exists()
            dirs_ok[d] = exists
            if not exists:
                issues.append(f"Missing directory: {d}")

        for ext in ("*.json", "*.jsonl"):
            for f in self._dir.rglob(ext):
                try:
                    text = f.read_text()
                    for pat in _SECRET_PATTERNS:
                        if pat.search(text):
                            issues.append(f"Potential secret in {f.name}")
                            secret_scan_ok = False
                            break
                except Exception:
                    pass

        return {
            "manifest_ok": manifest_ok,
            "dirs_ok": dirs_ok,
            "secret_scan_ok": secret_scan_ok,
            "issues": issues,
            "ok": manifest_ok and all(dirs_ok.values()) and secret_scan_ok,
        }

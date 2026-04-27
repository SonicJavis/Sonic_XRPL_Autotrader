from __future__ import annotations

import time
from typing import Any

from xrpl.clients import JsonRpcClient
from xrpl.models.requests import AccountInfo, AccountLines, BookOffers, ServerState

from app.market_data.normalization import normalize_amount


class XRPLReadOnlyClient:
    def __init__(self, rpc_url: str, retries: int = 2, retry_delay_seconds: float = 0.4) -> None:
        self.rpc_url = rpc_url
        self.client = JsonRpcClient(rpc_url)
        self.retries = retries
        self.retry_delay_seconds = retry_delay_seconds

    def safe_request(self, request_obj: Any, timeout_seconds: float = 10.0) -> dict[str, Any]:
        last_error: Exception | None = None
        for attempt in range(self.retries + 1):
            start = time.time()
            try:
                response = self.client.request(request_obj)
                elapsed = time.time() - start
                if elapsed > timeout_seconds:
                    raise TimeoutError(f"XRPL request exceeded timeout of {timeout_seconds}s")
                if getattr(response, "is_successful", lambda: True)() is False:
                    raise RuntimeError(str(response.result))
                return response.result
            except Exception as exc:  # pragma: no cover - network dependent
                last_error = exc
                if attempt < self.retries:
                    time.sleep(self.retry_delay_seconds)
        raise RuntimeError(f"XRPL safe_request failed after retries: {last_error}")

    def request_account_info(self, account: str) -> dict[str, Any]:
        return self.safe_request(AccountInfo(account=account, ledger_index="validated", strict=True))

    def get_account_lines(self, account: str) -> list[dict[str, Any]]:
        result = self.safe_request(AccountLines(account=account, ledger_index="validated"))
        lines = result.get("lines", [])
        normalized: list[dict[str, Any]] = []
        for line in lines:
            normalized.append(
                {
                    "issuer": line.get("account", ""),
                    "currency": line.get("currency", ""),
                    "balance": normalize_amount(line.get("balance", 0.0)),
                }
            )
        return normalized

    def request_account_lines(self, account: str) -> dict[str, Any]:
        return self.safe_request(AccountLines(account=account, ledger_index="validated"))

    def get_book_offers(self, taker_gets: dict[str, Any] | str, taker_pays: dict[str, Any] | str) -> dict[str, Any]:
        result = self.safe_request(BookOffers(taker_gets=taker_gets, taker_pays=taker_pays, limit=80))
        offers_out: list[dict[str, Any]] = []
        for offer in result.get("offers", []):
            offer_gets = offer.get("TakerGets", offer.get("taker_gets", 0))
            offer_pays = offer.get("TakerPays", offer.get("taker_pays", 0))
            quality = float(offer.get("quality", 0.0))
            offers_out.append(
                {
                    "quality": quality,
                    "taker_gets": normalize_amount(offer_gets),
                    "taker_pays": normalize_amount(offer_pays),
                }
            )

        return {
            "offers": offers_out,
            "quality": [o["quality"] for o in offers_out],
            "taker_gets": taker_gets,
            "taker_pays": taker_pays,
        }

    def request_book_offers(self, taker_gets: dict[str, Any], taker_pays: dict[str, Any]) -> dict[str, Any]:
        return self.safe_request(BookOffers(taker_gets=taker_gets, taker_pays=taker_pays, limit=80))

    def get_server_state(self) -> dict[str, Any]:
        result = self.safe_request(ServerState())
        state = result.get("state", {})
        validated = state.get("validated_ledger", {})
        return {
            "validated_ledger_index": validated.get("seq", result.get("validated_ledger", {}).get("seq")),
            "server_load_factor": state.get("load_factor"),
        }

    def request_server_state(self) -> dict[str, Any]:
        return self.safe_request(ServerState())

    def health_check(self) -> dict[str, Any]:
        try:
            state = self.get_server_state()
            return {"ok": True, **state}
        except Exception as exc:  # pragma: no cover - network dependent
            return {"ok": False, "error": str(exc)}

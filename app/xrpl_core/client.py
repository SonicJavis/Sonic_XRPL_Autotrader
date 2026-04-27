from __future__ import annotations

from typing import Any

from xrpl.clients import JsonRpcClient
from xrpl.models.requests import AccountInfo, AccountLines, BookOffers, ServerState


class XRPLReadOnlyClient:
    def __init__(self, rpc_url: str) -> None:
        self.rpc_url = rpc_url
        self.client = JsonRpcClient(rpc_url)

    def request_account_info(self, account: str) -> dict[str, Any]:
        response = self.client.request(AccountInfo(account=account, ledger_index="validated", strict=True))
        return response.result

    def request_account_lines(self, account: str) -> dict[str, Any]:
        response = self.client.request(AccountLines(account=account, ledger_index="validated"))
        return response.result

    def request_book_offers(self, taker_gets: dict[str, Any], taker_pays: dict[str, Any]) -> dict[str, Any]:
        response = self.client.request(BookOffers(taker_gets=taker_gets, taker_pays=taker_pays, limit=20))
        return response.result

    def request_server_state(self) -> dict[str, Any]:
        response = self.client.request(ServerState())
        return response.result

    def health_check(self) -> dict[str, Any]:
        try:
            state = self.request_server_state()
            return {"ok": True, "state": state.get("state", "unknown")}
        except Exception as exc:  # pragma: no cover - network dependent
            return {"ok": False, "error": str(exc)}

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class RegisteredToken:
    issuer: str
    currency: str
    symbol: str
    is_xrp: bool = False
    source: str = "manual"


class TokenRegistry:
    def __init__(self) -> None:
        self._tokens: list[RegisteredToken] = []

    def register(self, token: RegisteredToken) -> None:
        self._tokens.append(token)

    def list_tokens(self) -> list[RegisteredToken]:
        return list(self._tokens)

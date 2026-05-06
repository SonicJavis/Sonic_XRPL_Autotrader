from __future__ import annotations

from secrets import compare_digest
from time import monotonic
from typing import Callable

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response

from app.config import Settings
from app.config.runtime_mode import RuntimeSecurityProfile


PUBLIC_PATHS = {"/health"}
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
}


class APIAuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, *, settings: Settings, profile: RuntimeSecurityProfile) -> None:
        super().__init__(app)
        self.settings = settings
        self.profile = profile
        self._hits: dict[str, list[float]] = {}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if request.method.upper() == "OPTIONS":
            response = await call_next(request)
            return _with_security_headers(response)
        protected_path = request.url.path not in PUBLIC_PATHS
        if self.profile.auth_required and protected_path and not self._within_rate_limit(request):
            return _with_security_headers(
                JSONResponse(
                    status_code=429,
                    content={
                        "detail": "rate limit exceeded",
                        "is_shadow": True,
                        "is_advisory": True,
                        "is_executable": False,
                        "is_truth": False,
                    },
                )
            )
        if self.profile.auth_required and protected_path:
            if not self._authorized(request):
                return _with_security_headers(
                    JSONResponse(
                        status_code=401,
                        content={
                            "detail": "authentication required",
                            "is_shadow": True,
                            "is_advisory": True,
                            "is_executable": False,
                            "is_truth": False,
                        },
                    )
                )
        response = await call_next(request)
        return _with_security_headers(response)

    def _authorized(self, request: Request) -> bool:
        expected = self.settings.API_AUTH_TOKEN.get_secret_value() if self.settings.API_AUTH_TOKEN else ""
        if not expected:
            return False
        supplied = request.headers.get("x-api-token", "")
        auth = request.headers.get("authorization", "")
        if auth.lower().startswith("bearer "):
            supplied = auth.split(" ", 1)[1].strip()
        return bool(supplied) and compare_digest(supplied, expected)

    def _within_rate_limit(self, request: Request) -> bool:
        limit = int(self.settings.API_RATE_LIMIT_PER_MINUTE)
        key = request.client.host if request.client is not None else "unknown"
        now = monotonic()
        window_start = now - 60.0
        hits = [hit for hit in self._hits.get(key, []) if hit >= window_start]
        if len(hits) >= limit:
            self._hits[key] = hits
            return False
        hits.append(now)
        self._hits[key] = hits
        return True


def _with_security_headers(response: Response) -> Response:
    for key, value in SECURITY_HEADERS.items():
        response.headers[key] = value
    return response

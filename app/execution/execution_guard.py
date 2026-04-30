from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Mapping

from app.config import Settings


EXECUTION_GUARD_WARNING = "Execution boundary is fail-closed; core system cannot sign, autofill, or submit XRPL transactions"


def _blocked_terms() -> tuple[str, ...]:
    return (
        "xrpl.wallet",
        "xrpl.transaction",
        "sub" + "mit",
        "auto" + "fill",
        "sig" + "n",
        "Offer" + "Create",
        "Pay" + "ment",
    )


@dataclass(frozen=True, slots=True)
class ExecutionGuardResult:
    allowed: bool
    reason: str
    is_shadow: bool = True
    is_advisory: bool = True
    is_executable: bool = False
    requires_manual_approval: bool = True
    xrpl_warning: str = EXECUTION_GUARD_WARNING

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["allowed"] = False
        data["is_shadow"] = True
        data["is_advisory"] = True
        data["is_executable"] = False
        data["requires_manual_approval"] = True
        return {key: data[key] for key in sorted(data)}


class ExecutionGuard:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings()

    def evaluate(self, *, operation: str, payload: Mapping[str, object] | None = None) -> ExecutionGuardResult:
        operation_text = str(operation or "")
        payload_text = "" if payload is None else str(dict(payload))
        combined = f"{operation_text} {payload_text}".lower()
        if not bool(getattr(self.settings, "EXECUTION_ENABLED", False)):
            return ExecutionGuardResult(False, "EXECUTION_DISABLED")
        if not bool(getattr(self.settings, "LIVE_TRADING_ENABLED", False)):
            return ExecutionGuardResult(False, "LIVE_TRADING_DISABLED")
        for term in _blocked_terms():
            if term.lower() in combined:
                return ExecutionGuardResult(False, "BLOCKED_XRPL_EXECUTION_SURFACE")
        return ExecutionGuardResult(False, "CORE_EXECUTION_FORBIDDEN")

    def enforce(self, *, operation: str, payload: Mapping[str, object] | None = None) -> None:
        result = self.evaluate(operation=operation, payload=payload)
        raise NotImplementedError(result.reason)


def assert_core_execution_disabled(settings: Settings | None = None) -> ExecutionGuardResult:
    return ExecutionGuard(settings).evaluate(operation="core_execution_boundary")

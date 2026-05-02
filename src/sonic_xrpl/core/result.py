"""Generic Result type for Sonic XRPL V2.

Avoids exception propagation across module boundaries.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass
class Result(Generic[T]):
    """Represents the outcome of an operation — either success or failure."""

    ok: bool
    value: T | None = field(default=None)
    error: str | None = field(default=None)

    @classmethod
    def success(cls, value: T) -> "Result[T]":
        """Create a successful result."""
        return cls(ok=True, value=value, error=None)

    @classmethod
    def failure(cls, error: str) -> "Result[T]":
        """Create a failed result."""
        return cls(ok=False, value=None, error=error)

    def unwrap(self) -> T:
        """Return the value or raise RuntimeError if failed."""
        if not self.ok:
            raise RuntimeError(f"Result.unwrap() on failure: {self.error}")
        return self.value  # type: ignore[return-value]

    def __bool__(self) -> bool:
        return self.ok

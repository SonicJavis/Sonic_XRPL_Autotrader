"""Risk rules — enforce position-size and open-trade limits."""

from __future__ import annotations

from sqlmodel import Session, select

from app.config import settings
from app.db.models import PaperTrade
from app.telemetry import get_logger

logger = get_logger("risk.rules")


class RiskDenied(Exception):
    """Raised when a risk check blocks a trade."""


def check_position_size(size_xrp: float, request_id: str = "") -> None:
    """Raise RiskDenied if the trade size exceeds the configured maximum.

    Args:
        size_xrp: Proposed trade size in XRP.
        request_id: Trace ID for logging.
    """
    max_xrp = settings.max_trade_xrp
    if size_xrp > max_xrp:
        logger.warning(
            "Risk denied — position size too large",
            request_id=request_id,
            size_xrp=size_xrp,
            max_xrp=max_xrp,
        )
        raise RiskDenied(
            f"Trade size {size_xrp} XRP exceeds maximum {max_xrp} XRP."
        )


def check_open_positions(session: Session, request_id: str = "") -> None:
    """Raise RiskDenied if the number of open paper trades is at the maximum.

    Args:
        session: Active SQLModel session.
        request_id: Trace ID for logging.
    """
    max_pos = settings.max_open_positions
    open_count = session.exec(
        select(PaperTrade).where(PaperTrade.status == "OPEN")
    ).all()
    count = len(open_count)
    if count >= max_pos:
        logger.warning(
            "Risk denied — too many open positions",
            request_id=request_id,
            open_positions=count,
            max_open_positions=max_pos,
        )
        raise RiskDenied(
            f"Open positions ({count}) have reached the limit ({max_pos})."
        )


def run_all_checks(size_xrp: float, session: Session, request_id: str = "") -> None:
    """Run all risk checks in sequence.

    Raises:
        RiskDenied: On first failed check.
    """
    check_position_size(size_xrp, request_id=request_id)
    check_open_positions(session, request_id=request_id)
    logger.debug("Risk checks passed", request_id=request_id, size_xrp=size_xrp)

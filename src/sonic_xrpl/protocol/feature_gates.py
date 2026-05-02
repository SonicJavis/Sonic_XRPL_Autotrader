"""Feature gates — check whether a protocol capability is enabled before use.

No module may use an XRPL amendment-dependent feature without checking here first.
This is Architecture Rule #1.
"""

from __future__ import annotations

from sonic_xrpl.core.errors import CapabilityNotAvailableError
from sonic_xrpl.protocol.amendments import AmendmentStatus, is_amendment_enabled


def is_feature_enabled(name: str) -> bool:
    """Return True if the named amendment/feature is enabled in the research baseline."""
    return is_amendment_enabled(name)


def require_feature(name: str) -> None:
    """Raise CapabilityNotAvailableError if the feature is not enabled.

    Usage::

        require_feature("AMM")  # OK — enabled
        require_feature("LendingProtocol")  # raises CapabilityNotAvailableError
    """
    if not is_feature_enabled(name):
        raise CapabilityNotAvailableError(
            f"Protocol feature {name!r} is not available. "
            f"Check amendment status before using this capability."
        )


def is_research_only(name: str) -> bool:
    """Return True if the amendment is marked as research-only."""
    from sonic_xrpl.protocol.amendments import KNOWN_AMENDMENTS

    try:
        return KNOWN_AMENDMENTS[name].status == AmendmentStatus.RESEARCH_ONLY
    except KeyError:
        return False


def is_obsolete(name: str) -> bool:
    """Return True if the amendment is marked as obsolete."""
    from sonic_xrpl.protocol.amendments import KNOWN_AMENDMENTS

    try:
        return KNOWN_AMENDMENTS[name].status == AmendmentStatus.OBSOLETE
    except KeyError:
        return False

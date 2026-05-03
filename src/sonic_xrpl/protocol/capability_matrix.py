"""Protocol Capability Matrix — central registry of what is usable.

Architecture Rule #1: No module may assume a capability exists without
checking this matrix.

Each entry documents:
- name: capability key
- status: enabled / feature_gated / research_only / obsolete
- source: primary reference URL
- architecture_impact: how this capability affects the system
- enabled_by_default: whether it is active on mainnet
- feature_gate: name of the gate that must be checked
- network_assumptions: which networks support this
- last_checked: date of last research check
"""

from __future__ import annotations

from dataclasses import dataclass

from sonic_xrpl.core.errors import CapabilityNotAvailableError
from sonic_xrpl.protocol.amendments import AmendmentStatus, KNOWN_AMENDMENTS


@dataclass(frozen=True)
class CapabilityEntry:
    """A single entry in the protocol capability matrix."""

    name: str
    status: AmendmentStatus
    source: str
    architecture_impact: str
    enabled_by_default: bool
    feature_gate: str | None
    network_assumptions: str
    last_checked: str


def _build_matrix() -> dict[str, CapabilityEntry]:
    """Derive the capability matrix from the amendments registry."""
    matrix: dict[str, CapabilityEntry] = {}
    for name, amendment in KNOWN_AMENDMENTS.items():
        matrix[name] = CapabilityEntry(
            name=name,
            status=amendment.status,
            source=amendment.source_url,
            architecture_impact=amendment.architecture_impact,
            enabled_by_default=amendment.enabled_by_default,
            feature_gate=None if amendment.enabled_by_default else name,
            network_assumptions="XRPL mainnet"
            if amendment.status == AmendmentStatus.ENABLED
            else "Not on mainnet",
            last_checked=amendment.last_checked,
        )
    return matrix


CAPABILITY_MATRIX: dict[str, CapabilityEntry] = _build_matrix()


def get_capability(name: str) -> CapabilityEntry:
    """Return a capability entry by name."""
    if name not in CAPABILITY_MATRIX:
        raise KeyError(f"Unknown capability: {name!r}")
    return CAPABILITY_MATRIX[name]


def is_capability_available(name: str) -> bool:
    """Return True if the capability is marked ENABLED."""
    try:
        return CAPABILITY_MATRIX[name].status == AmendmentStatus.ENABLED
    except KeyError:
        return False


def require_capability(name: str) -> None:
    """Raise CapabilityNotAvailableError if capability is not ENABLED."""
    if not is_capability_available(name):
        raise CapabilityNotAvailableError(
            f"Capability {name!r} is not available on mainnet. "
            f"Status: {CAPABILITY_MATRIX.get(name, {})}"
        )


def get_enabled_capabilities() -> list[str]:
    """Return names of all ENABLED capabilities."""
    return [
        name
        for name, cap in CAPABILITY_MATRIX.items()
        if cap.status == AmendmentStatus.ENABLED
    ]


def get_research_only_capabilities() -> list[str]:
    """Return names of all RESEARCH_ONLY capabilities."""
    return [
        name
        for name, cap in CAPABILITY_MATRIX.items()
        if cap.status == AmendmentStatus.RESEARCH_ONLY
    ]


def get_obsolete_capabilities() -> list[str]:
    """Return names of all OBSOLETE capabilities."""
    return [
        name
        for name, cap in CAPABILITY_MATRIX.items()
        if cap.status == AmendmentStatus.OBSOLETE
    ]

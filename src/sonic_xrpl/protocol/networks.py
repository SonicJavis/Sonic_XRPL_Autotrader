"""XRPL network definitions and endpoint registry."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class XRPLNetwork(str, Enum):
    """Known XRPL-family networks."""

    MAINNET = "mainnet"
    TESTNET = "testnet"
    DEVNET = "devnet"
    AMM_DEVNET = "amm_devnet"
    XAHAU_MAINNET = "xahau_mainnet"
    XAHAU_TESTNET = "xahau_testnet"
    MOCK = "mock"


@dataclass(frozen=True)
class NetworkConfig:
    """Configuration for a specific XRPL-family network."""

    network: XRPLNetwork
    ws_url: str
    description: str
    submission_allowed: bool = False


NETWORK_CONFIG: dict[XRPLNetwork, NetworkConfig] = {
    XRPLNetwork.MAINNET: NetworkConfig(
        network=XRPLNetwork.MAINNET,
        ws_url="wss://xrplcluster.com",
        description="XRPL Mainnet — production network",
        submission_allowed=False,
    ),
    XRPLNetwork.TESTNET: NetworkConfig(
        network=XRPLNetwork.TESTNET,
        ws_url="wss://s.altnet.rippletest.net:51233",
        description="XRPL Testnet — non-production testing",
        submission_allowed=False,
    ),
    XRPLNetwork.DEVNET: NetworkConfig(
        network=XRPLNetwork.DEVNET,
        ws_url="wss://s.devnet.rippletest.net:51233",
        description="XRPL Devnet — feature previews",
        submission_allowed=False,
    ),
    XRPLNetwork.AMM_DEVNET: NetworkConfig(
        network=XRPLNetwork.AMM_DEVNET,
        ws_url="wss://amm.devnet.rippletest.net:51233",
        description="AMM Devnet — AMM feature testing",
        submission_allowed=False,
    ),
    XRPLNetwork.XAHAU_MAINNET: NetworkConfig(
        network=XRPLNetwork.XAHAU_MAINNET,
        ws_url="wss://xahau.network",
        description="Xahau Mainnet — Hooks-enabled sidechain (research-only)",
        submission_allowed=False,
    ),
    XRPLNetwork.XAHAU_TESTNET: NetworkConfig(
        network=XRPLNetwork.XAHAU_TESTNET,
        ws_url="wss://hooks-testnet-v3.xrpl-labs.com",
        description="Xahau Testnet — Hooks testing (research-only)",
        submission_allowed=False,
    ),
    XRPLNetwork.MOCK: NetworkConfig(
        network=XRPLNetwork.MOCK,
        ws_url="mock://localhost",
        description="Mock network for offline testing",
        submission_allowed=False,
    ),
}


def get_network_config(network: XRPLNetwork) -> NetworkConfig:
    """Return config for the given network."""
    return NETWORK_CONFIG[network]

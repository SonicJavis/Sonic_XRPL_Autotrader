"""Bridge between V2 and execution_prototype legacy modules."""

from __future__ import annotations


def get_execution_prototype_status() -> dict:
    """Check availability of execution_prototype modules."""
    status: dict[str, bool] = {}

    modules_to_check = [
        "execution_prototype.reconciliation",
        "execution_prototype.walk_forward_replay.cli",
    ]

    for mod in modules_to_check:
        try:
            __import__(mod)
            status[mod] = True
        except ImportError:
            status[mod] = False

    return status

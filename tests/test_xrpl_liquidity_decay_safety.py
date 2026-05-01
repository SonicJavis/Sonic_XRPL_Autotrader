from pathlib import Path


def test_liquidity_decay_model_has_no_execution_or_pathfinding_calls() -> None:
    source = Path("app/xrpl/liquidity_decay.py").read_text(encoding="utf-8")
    forbidden_fragments = (
        "xrpl_core.wallet",
        "xrpl_core.transactions",
        "submit_transaction",
        "autofill",
        "OfferCreate",
        "Payment",
        "path_find",
        "ripple_path_find",
    )

    for fragment in forbidden_fragments:
        assert fragment not in source

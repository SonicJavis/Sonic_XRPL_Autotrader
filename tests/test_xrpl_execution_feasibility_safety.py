from pathlib import Path


def test_feasibility_layer_has_no_execution_boundary_imports_or_calls() -> None:
    source = Path("app/xrpl/execution_feasibility.py").read_text(encoding="utf-8")

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

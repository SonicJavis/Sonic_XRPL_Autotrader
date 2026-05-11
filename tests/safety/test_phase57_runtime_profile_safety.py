from pathlib import Path

from sonic_xrpl.runtime_profile.conformance import evaluate_runtime_profile_conformance


def test_phase57_runtime_profile_package_has_no_forbidden_execution_terms():
    combined = "\n".join(path.read_text(encoding="utf-8") for path in Path("src/sonic_xrpl/runtime_profile").glob("*.py"))
    forbidden = [
        "submitAndWait",
        "fromSeed",
        "familySeed",
        "auto-buy",
        "while True",
        "requests.get(",
        "requests.post(",
        "Xaman",
    ]
    for term in forbidden:
        assert term not in combined


def test_phase57_runtime_profile_conformance_preserves_fail_closed_defaults():
    report = evaluate_runtime_profile_conformance(
        env={
            "SONIC_RUNTIME_MODE": "paper",
            "SONIC_DRY_RUN": "true",
            "EXECUTION_ENABLED": "false",
            "LIVE_TRADING_ENABLED": "false",
            "SONIC_STORAGE_PATH": "data/v2.db",
        }
    )
    assert report.paper_only is True
    assert report.live_execution_allowed is False
    assert report.runtime_mutation_allowed is False

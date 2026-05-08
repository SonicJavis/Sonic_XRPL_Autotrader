from pathlib import Path

from sonic_xrpl.outcome_corpus import build_outcome_corpus


def test_phase52_runtime_does_not_add_execution_keywords():
    combined = "\n".join(path.read_text() for path in Path("src/sonic_xrpl/outcome_corpus").glob("*.py"))
    forbidden = [
        "submitAndWait",
        "autofill",
        "Xaman",
        "fromSeed",
        "familySeed",
        "auto-buy",
        "place_order",
        "while True",
        "websocket",
        "requests.",
    ]
    for term in forbidden:
        assert term not in combined


def test_phase52_live_execution_remains_false():
    corpus = build_outcome_corpus(["tests/fixtures/outcome_corpus/source_backed_multi_window.json"])

    assert corpus.live_execution_allowed is False
    assert all(case.live_execution_allowed is False for case in corpus.replay_cases)


def test_phase52_safety_grep_script_keeps_runtime_blocked():
    script = Path("scripts/safety_grep.py").read_text()

    assert "submitAndWait" in script
    assert "autofill" in script
    assert "auto_calibrate" in script

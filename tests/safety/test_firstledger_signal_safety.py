from pathlib import Path


def test_signal_layer_does_not_add_execution_keywords():
    combined = "\n".join(path.read_text() for path in Path("src/sonic_xrpl/signals").glob("*.py"))
    forbidden = ["submitAndWait", "autofill", "Xaman", "fromSeed", "familySeed", "auto-buy", "place_order"]
    for term in forbidden:
        assert term not in combined


def test_signal_layer_states_live_execution_false():
    text = Path("src/sonic_xrpl/signals/models.py").read_text()
    assert "live_execution_allowed: bool = False" in text

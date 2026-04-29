from app.execution.simulation_store import AppendOnlySimulationStore


def test_append_only_simulation_store_preserves_order_and_copying() -> None:
    store = AppendOnlySimulationStore()

    first = store.append({"simulation_id": "sim_a", "fill_ratio": 0.5})
    second = store.append({"simulation_id": "sim_b", "fill_ratio": 0.8})
    first["fill_ratio"] = 0.0

    assert store.get("sim_a")["fill_ratio"] == 0.5
    assert store.get("sim_b") == second
    assert [row["simulation_id"] for row in store.list(limit=10)] == ["sim_b", "sim_a"]


def test_append_only_simulation_store_limit_is_bounded() -> None:
    store = AppendOnlySimulationStore()
    store.extend({"simulation_id": f"sim_{idx}"} for idx in range(3))

    assert len(store.list(limit=0)) == 1
    assert store.get("missing") is None

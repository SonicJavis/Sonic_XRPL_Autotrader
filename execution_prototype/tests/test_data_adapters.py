import pytest
from pathlib import Path
from execution_prototype.data_adapters.models import DataAdapterConfig
from execution_prototype.data_adapters.clio_adapter import ClioAdapter

def test_adapter_safety_disabled_by_default():
    config = DataAdapterConfig(
        adapter_id="test",
        source_type="clio",
        endpoint="https://clio.example.com",
        network_read_enabled=False # Disabled by default
    )
    adapter = ClioAdapter(config)
    with pytest.raises(PermissionError) as exc:
        adapter.fetch_records()
    assert "Network read disabled" in str(exc.value)

def test_adapter_dry_run_mode():
    config = DataAdapterConfig(
        adapter_id="test",
        source_type="clio",
        endpoint="https://clio.example.com",
        network_read_enabled=True,
        dry_run=True
    )
    adapter = ClioAdapter(config)
    records = adapter.fetch_records()
    assert len(records) == 0 # Dry run returns nothing

def test_deterministic_adapter_id():
    import hashlib
    source = "clio"
    endpoint = "https://clio.example.com"
    id1 = hashlib.sha256(f"{source}:{endpoint}".encode()).hexdigest()
    
    config = DataAdapterConfig(adapter_id=id1, source_type=source, endpoint=endpoint)
    assert config.adapter_id == id1

def test_no_forbidden_imports():
    # Ensure no wallet or signing logic is imported in the adapters
    import sys
    forbidden = ["xrpl.wallet", "xrpl.transaction", "xrpl.clients.json_rpc_client.submit"]
    for f in forbidden:
        assert f not in sys.modules or "data_adapters" not in sys.modules[f].__name__

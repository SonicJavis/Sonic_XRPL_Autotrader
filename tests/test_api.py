from fastapi.testclient import TestClient

from app.main import create_app


def test_health_endpoint_works() -> None:
    app = create_app()
    app.state.container.xrpl_client.health_check = lambda: {"ok": True, "validated_ledger_index": 1, "server_load_factor": 1}
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_register_token_and_list_tokens() -> None:
    app = create_app()
    client = TestClient(app)

    reg = client.post("/tokens/register", json={"issuer": "rPT1Sjq2YGrBMTttX4GZHjKu9dyfzbpAYe", "currency": "USD"})
    assert reg.status_code == 200
    assert reg.json()["ok"] is True

    listed = client.get("/tokens")
    assert listed.status_code == 200
    assert isinstance(listed.json(), list)


def test_market_orderbook_endpoint() -> None:
    app = create_app()
    app.state.container.xrpl_client.get_book_offers = lambda taker_gets, taker_pays: {
        "offers": [
            {"quality": 1.0, "taker_gets": 1000.0, "taker_pays": 1000.0},
            {"quality": 1.01, "taker_gets": 1000.0, "taker_pays": 1010.0},
            {"quality": 0.99, "taker_gets": 1000.0, "taker_pays": 990.0},
        ]
    }
    client = TestClient(app)

    client.post("/tokens/register", json={"issuer": "rPT1Sjq2YGrBMTttX4GZHjKu9dyfzbpAYe", "currency": "USD"})
    response = client.get("/market/orderbook")

    assert response.status_code == 200
    assert response.json()["ok"] is True


def test_phase4_endpoints_after_pipeline_run() -> None:
    app = create_app()
    app.state.container.xrpl_client.get_book_offers = lambda taker_gets, taker_pays: {
        "offers": [
            {"quality": 0.99, "taker_gets": 990.0, "taker_pays": 1000.0},
            {"quality": 0.98, "taker_gets": 980.0, "taker_pays": 1000.0},
            {"quality": 0.97, "taker_gets": 970.0, "taker_pays": 1000.0},
            {"quality": 1.01, "taker_gets": 1000.0, "taker_pays": 1010.0},
            {"quality": 1.02, "taker_gets": 1000.0, "taker_pays": 1020.0},
            {"quality": 1.03, "taker_gets": 1000.0, "taker_pays": 1030.0},
        ]
    }
    client = TestClient(app)

    reg = client.post("/tokens/register", json={"issuer": "rPT1Sjq2YGrBMTttX4GZHjKu9dyfzbpAYe", "currency": "USD"})
    assert reg.status_code == 200
    run = client.post("/pipeline/run-once")
    assert run.status_code == 200

    alpha = client.get("/signals/alpha")
    assert alpha.status_code == 200
    assert isinstance(alpha.json(), list)

    depth = client.get("/market/depth")
    assert depth.status_code == 200
    assert "ok" in depth.json()

    history = client.get("/market/history")
    assert history.status_code == 200
    assert isinstance(history.json(), list)

    decisions = client.get("/risk/decisions")
    assert decisions.status_code == 200
    assert isinstance(decisions.json(), list)

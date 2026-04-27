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

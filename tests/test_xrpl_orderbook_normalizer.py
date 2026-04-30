from app.xrpl.orderbook_normalizer import normalize_book_offers, normalize_offer


def test_xrp_drop_conversion_and_recomputed_quality() -> None:
    normalized = normalize_offer(
        {
            "TakerGets": "1000000",
            "TakerPays": "2000000",
            "quality": "999",
            "owner": "rOwner",
        }
    )

    assert normalized is not None
    assert normalized["taker_gets"] == 1.0
    assert normalized["taker_pays"] == 2.0
    assert normalized["currency_gets"] == "XRP"
    assert normalized["issuer_gets"] is None
    assert normalized["is_xrp_gets"] is True
    assert normalized["quality"] == 2.0
    assert normalized["quality_delta"] == 997.0
    assert normalized["quality_matches"] is False


def test_iou_parsing_preserves_currency_and_issuer() -> None:
    normalized = normalize_offer(
        {
            "TakerGets": {"currency": "USD", "issuer": "rIssuer", "value": "10.5"},
            "TakerPays": "5250000",
            "owner": "rOwner",
        }
    )

    assert normalized is not None
    assert normalized["taker_gets"] == 10.5
    assert normalized["taker_pays"] == 5.25
    assert normalized["currency_gets"] == "USD"
    assert normalized["issuer_gets"] == "rIssuer"
    assert normalized["currency_pays"] == "XRP"
    assert normalized["issuer_pays"] is None
    assert normalized["is_xrp_pays"] is True


def test_owner_funds_caps_effective_gets_for_iou_context() -> None:
    normalized = normalize_offer(
        {
            "TakerGets": {"currency": "USD", "issuer": "rIssuer", "value": "100"},
            "TakerPays": "200000000",
            "owner_funds": "25",
            "owner": "rOwner",
        }
    )

    assert normalized is not None
    assert normalized["effective_gets"] == 25.0
    assert normalized["effective_pays"] == 50.0


def test_taker_gets_funded_precedes_owner_funds() -> None:
    normalized = normalize_offer(
        {
            "TakerGets": {"currency": "USD", "issuer": "rIssuer", "value": "100"},
            "TakerPays": "200000000",
            "taker_gets_funded": {"currency": "USD", "issuer": "rIssuer", "value": "10"},
            "owner_funds": "50",
        }
    )

    assert normalized is not None
    assert normalized["effective_gets"] == 10.0
    assert normalized["effective_pays"] == 20.0


def test_taker_pays_funded_caps_effective_pays_and_gets() -> None:
    normalized = normalize_offer(
        {
            "TakerGets": {"currency": "USD", "issuer": "rIssuer", "value": "100"},
            "TakerPays": "200000000",
            "taker_pays_funded": "50000000",
        }
    )

    assert normalized is not None
    assert normalized["effective_pays"] == 50.0
    assert normalized["effective_gets"] == 25.0


def test_malformed_zero_and_unfunded_offers_are_discarded() -> None:
    offers = normalize_book_offers(
        [
            {"TakerGets": "0", "TakerPays": "1000000"},
            {"TakerGets": {"currency": "USD", "value": "10"}, "TakerPays": "1000000"},
            {"TakerGets": {"currency": "USD", "issuer": "rIssuer", "value": "10"}, "TakerPays": "1000000", "owner_funds": "0"},
            {"TakerGets": {"currency": "USD", "issuer": "rIssuer", "value": "10"}, "TakerPays": "1000000"},
        ]
    )

    assert offers["offer_count"] == 1
    assert offers["offers"][0]["effective_gets"] == 10.0


def test_quality_sorting_is_stable_for_fifo_within_same_quality() -> None:
    book = normalize_book_offers(
        [
            {"TakerGets": "1000000", "TakerPays": "2000000", "owner": "rA"},
            {"TakerGets": "1000000", "TakerPays": "1000000", "owner": "rB"},
            {"TakerGets": "2000000", "TakerPays": "2000000", "owner": "rC"},
        ]
    )

    assert [offer["owner"] for offer in book["offers"]] == ["rB", "rC", "rA"]
    assert [offer["quality"] for offer in book["offers"]] == [1.0, 1.0, 2.0]


def test_cumulative_depth_and_depth_by_quality_are_deterministic() -> None:
    book = normalize_book_offers(
        [
            {"TakerGets": "1000000", "TakerPays": "1000000", "owner": "rA"},
            {"TakerGets": "2000000", "TakerPays": "2000000", "owner": "rB"},
            {"TakerGets": "3000000", "TakerPays": "6000000", "owner": "rC"},
        ],
        spread_estimate=0.05,
    )

    assert book["cumulative_depth"] == [1.0, 3.0, 6.0]
    assert book["depth_by_quality"] == {"1": 3.0, "2": 3.0}
    assert book["best_price"] == 1.0
    assert book["spread_estimate"] == 0.05
    assert book["is_shadow"] is True
    assert book["is_advisory"] is True
    assert book["is_executable"] is False


def test_identical_input_produces_identical_output() -> None:
    offers = [
        {
            "TakerGets": {"currency": "EUR", "issuer": "rIssuer", "value": "123.456789123456"},
            "TakerPays": "987654321",
            "owner_funds": "12.345678912345",
            "owner": "rOwner",
        },
        {"TakerGets": "2000000", "TakerPays": "3000000", "owner": "rXrpOwner"},
    ]

    assert normalize_book_offers(offers) == normalize_book_offers(offers)

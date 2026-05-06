from execution_prototype.discovery.firstledger_reader import parse_firstledger_fixture


def test_parse_firstledger_fixture_uses_source_backed_rows_only():
    rows = [
        {
            "event_type": "amm_create",
            "issuer": "rIssuer",
            "currency": "MEME",
            "ledger_index": 123,
            "tx_hash": "ABC123",
            "validated": True,
            "metadata_present": True,
            "observed_at": "2026-05-05T11:00:00+00:00",
        },
        {
            "event_type": "amm_create",
            "currency": "NOISSUER",
            "ledger_index": 124,
            "tx_hash": "DEF456",
            "validated": True,
            "metadata_present": True,
        },
    ]

    events = parse_firstledger_fixture(rows)

    assert len(events) == 1
    assert events[0].event_type == "amm_created"
    assert events[0].issuer == "rIssuer"
    assert events[0].currency_code == "MEME"
    assert events[0].ledger_index == 123
    assert events[0].tx_hash == "ABC123"
    assert events[0].validated is True
    assert events[0].metadata_present is True
    assert events[0].limitations == []


def test_parse_firstledger_fixture_does_not_invent_fake_launches():
    assert parse_firstledger_fixture([]) == []
    assert parse_firstledger_fixture([{"token": "FAKEONLY"}]) == []


def test_parse_firstledger_fixture_marks_low_confidence_when_metadata_or_validation_missing():
    rows = [
        {
            "type": "offer",
            "issuer_address": "rIssuer",
            "symbol": "MEME",
            "ledger": "999",
            "hash": "HASH999",
            "validated": False,
            "metadata_present": False,
            "timestamp": "2026-05-05T11:01:00+00:00",
        }
    ]

    events = parse_firstledger_fixture(rows)

    assert len(events) == 1
    assert events[0].event_type == "offer_activity_low_confidence"
    assert "not_validated_do_not_treat_as_final" in events[0].limitations
    assert "metadata_missing_signal_is_low_confidence" in events[0].limitations


def test_parse_firstledger_fixture_has_deterministic_ids_and_ordering():
    rows = [
        {
            "type": "trustline",
            "issuer": "rIssuer2",
            "currency_code": "BBB",
            "ledger_index": 12,
            "tx_hash": "B",
            "validated": True,
            "metadata_present": True,
            "observed_at": "2026-05-05T11:02:00+00:00",
        },
        {
            "type": "trustline",
            "issuer": "rIssuer1",
            "currency_code": "AAA",
            "ledger_index": 11,
            "tx_hash": "A",
            "validated": True,
            "metadata_present": True,
            "observed_at": "2026-05-05T11:02:00+00:00",
        },
    ]

    first = parse_firstledger_fixture(rows)
    second = parse_firstledger_fixture(rows)

    assert [event.event_id for event in first] == [event.event_id for event in second]
    assert [event.ledger_index for event in first] == [11, 12]


def test_parse_firstledger_fixture_preserves_missing_observed_at_without_synthesis():
    rows = [
        {
            "type": "trustline",
            "issuer": "rIssuer",
            "currency_code": "MISS_TIME",
            "ledger_index": 777,
            "tx_hash": "MISSINGTIME777",
            "validated": True,
            "metadata_present": True,
        }
    ]

    first = parse_firstledger_fixture(rows)
    second = parse_firstledger_fixture(rows)

    assert len(first) == 1
    assert first[0].observed_at == ""
    assert second[0].observed_at == ""
    assert first[0].observed_at == second[0].observed_at
    assert "observed_at_missing" in first[0].limitations
    assert "observed_at_missing_generated_by_parser" not in first[0].limitations

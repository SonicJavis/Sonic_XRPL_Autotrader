import pytest
from execution_prototype.discovery.xrpl_reader import process_transactions, generate_event_id
from execution_prototype.discovery.candidate_builder import build_candidates, _generate_candidate_id
from execution_prototype.discovery.signal_scorer import calculate_score
from execution_prototype.discovery.risk_classifier import generate_risk_flags

def test_deterministic_ids():
    id1 = generate_event_id("hash1", "trustline")
    id2 = generate_event_id("hash1", "trustline")
    assert id1 == id2
    
    cid1 = _generate_candidate_id("issuer1", "MEME")
    cid2 = _generate_candidate_id("issuer1", "MEME")
    assert cid1 == cid2

def test_trustline_detection():
    tx = {
        "hash": "tx1",
        "TransactionType": "TrustSet",
        "LimitAmount": {"currency": "MEME", "issuer": "rIssuer"},
        "meta": {"TransactionResult": "tesSUCCESS"},
        "validated": True
    }
    events = process_transactions([tx])
    assert len(events) == 1
    assert events[0].event_type == "trustline_created"
    assert events[0].currency_code == "MEME"
    assert events[0].issuer == "rIssuer"
    assert events[0].metadata_present is True

def test_ammcreate_detection():
    tx = {
        "hash": "tx2",
        "TransactionType": "AMMCreate",
        "Amount": {"currency": "MEME", "issuer": "rIssuer"},
        "Amount2": "10000", # XRP
        "meta": {"TransactionResult": "tesSUCCESS"},
        "validated": True
    }
    events = process_transactions([tx])
    assert len(events) == 1
    assert events[0].event_type == "amm_created"
    assert events[0].currency_code == "MEME"

def test_no_inference_without_metadata():
    tx = {
        "hash": "tx3",
        "TransactionType": "TrustSet",
        "LimitAmount": {"currency": "NO_META", "issuer": "rIssuer"},
        "validated": True
        # No meta
    }
    events = process_transactions([tx])
    assert events[0].metadata_present is False
    assert any("MISSING_METADATA" in lim for lim in events[0].limitations)
    
    cands = build_candidates(events)
    assert len(cands) == 1
    assert cands[0].confidence == "low"
    assert "MISSING_METADATA" in cands[0].risk_flags

def test_weak_signal_handling():
    # 1 offer create = no candidate (needs 2 weak signals or 1 strong)
    tx_offer = {
        "TransactionType": "OfferCreate",
        "TakerGets": {"currency": "WEAK", "issuer": "rIssuer"},
        "TakerPays": "10",
        "meta": {}
    }
    events = process_transactions([tx_offer])
    cands = build_candidates(events)
    assert len(cands) == 0
    
    # 1 offer + 1 issuer activity = candidate
    tx_payment = {
        "TransactionType": "Payment",
        "Account": "rIssuer",
        "Amount": {"currency": "WEAK", "issuer": "rIssuer"},
        "meta": {}
    }
    events_both = process_transactions([tx_offer, tx_payment])
    cands_both = build_candidates(events_both)
    assert len(cands_both) == 1
    assert cands_both[0].confidence == "low" # weak signals only -> low confidence

def test_scoring_correctness():
    # 2 trustlines + metadata + validated
    txs = [
        {
            "TransactionType": "TrustSet",
            "LimitAmount": {"currency": "SCORE", "issuer": "rIssuer"},
            "meta": {}, "validated": True
        },
        {
            "TransactionType": "TrustSet",
            "LimitAmount": {"currency": "SCORE", "issuer": "rIssuer"},
            "meta": {}, "validated": True
        }
    ]
    events = process_transactions(txs)
    cands = build_candidates(events)
    cand = cands[0]
    
    # Trustlines: 2 * 10 = 20
    # AMM: 0
    # Issuer Act: 0
    # Meta: 10
    # Risks: 0
    # Total = 30 -> "watch"
    assert cand.score == 30
    assert cand.score_band == "watch"

def test_confidence_rules():
    tx_amm = {
        "TransactionType": "AMMCreate",
        "Amount": {"currency": "HIGH_CONF", "issuer": "rIssuer"},
        "Amount2": "100",
        "meta": {}, "validated": True
    }
    events = process_transactions([tx_amm])
    cands = build_candidates(events)
    assert cands[0].confidence == "high"

import hashlib
from datetime import datetime, timezone
from typing import List, Dict, Any
from execution_prototype.discovery.models import RawDiscoveryEvent

def generate_event_id(tx_hash: str, event_type: str) -> str:
    basis = f"{tx_hash}|{event_type}"
    return hashlib.sha256(basis.encode("utf-8")).hexdigest()[:16]

def parse_currency_and_issuer(amount_obj: Any) -> tuple[str, str]:
    if isinstance(amount_obj, dict):
        return amount_obj.get("currency", ""), amount_obj.get("issuer", "")
    return "", ""

def extract_events_from_tx(tx: Dict[str, Any]) -> List[RawDiscoveryEvent]:
    events = []
    
    # We must treat XRPL tx wrapper formats carefully
    tx_body = tx.get("tx_json", tx.get("tx", tx)) if "tx_json" in tx or "tx" in tx else tx
    meta = tx.get("meta", tx.get("metaData", None))
    
    validated = tx.get("validated", False)
    metadata_present = meta is not None
    tx_hash = tx_body.get("hash", "")
    ledger_index = tx_body.get("ledger_index", tx.get("ledger_index", 0))
    tx_type = tx_body.get("TransactionType", "")
    account = tx_body.get("Account", "")
    
    # If missing metadata, we add limitation but still generate events to track the lack of metadata
    limitations = []
    if not metadata_present:
        limitations.append("MISSING_METADATA: Event lacks validated ledger execution context.")
    if not validated:
        limitations.append("UNVALIDATED: Transaction has not been confirmed on ledger.")
        
    observed_at = datetime.now(timezone.utc).isoformat()
    
    if tx_type == "TrustSet":
        limit_amount = tx_body.get("LimitAmount", {})
        currency, issuer = parse_currency_and_issuer(limit_amount)
        if currency and issuer:
            events.append(RawDiscoveryEvent(
                event_id=generate_event_id(tx_hash, "trustline_created"),
                event_type="trustline_created",
                issuer=issuer,
                currency_code=currency,
                ledger_index=ledger_index,
                tx_hash=tx_hash,
                validated=validated,
                metadata_present=metadata_present,
                observed_at=observed_at,
                limitations=limitations.copy()
            ))
            
    elif tx_type == "AMMCreate":
        amount1 = tx_body.get("Amount", {})
        amount2 = tx_body.get("Amount2", {})
        c1, i1 = parse_currency_and_issuer(amount1)
        c2, i2 = parse_currency_and_issuer(amount2)
        
        # We flag the issued currency
        for c, i in [(c1, i1), (c2, i2)]:
            if c and i and c != "XRP":
                events.append(RawDiscoveryEvent(
                    event_id=generate_event_id(tx_hash, f"amm_created_{c}_{i}"),
                    event_type="amm_created",
                    issuer=i,
                    currency_code=c,
                    ledger_index=ledger_index,
                    tx_hash=tx_hash,
                    validated=validated,
                    metadata_present=metadata_present,
                    observed_at=observed_at,
                    limitations=limitations.copy()
                ))
                
    elif tx_type == "OfferCreate":
        taker_gets = tx_body.get("TakerGets", {})
        taker_pays = tx_body.get("TakerPays", {})
        c1, i1 = parse_currency_and_issuer(taker_gets)
        c2, i2 = parse_currency_and_issuer(taker_pays)
        
        for c, i in [(c1, i1), (c2, i2)]:
            if c and i and c != "XRP":
                events.append(RawDiscoveryEvent(
                    event_id=generate_event_id(tx_hash, f"offer_activity_{c}_{i}"),
                    event_type="offer_activity_low_confidence",
                    issuer=i,
                    currency_code=c,
                    ledger_index=ledger_index,
                    tx_hash=tx_hash,
                    validated=validated,
                    metadata_present=metadata_present,
                    observed_at=observed_at,
                    limitations=limitations.copy() + ["OFFER_ONLY: Does not prove liquidity or fill"]
                ))
                
    # Check for issuer activity (if account == issuer of a known token)
    # This requires state or just checking if account matches any token issuer in the tx.
    # We will let candidate_builder aggregate this if needed, or flag it here if it's a payment of their own token.
    if tx_type == "Payment":
        amount = tx_body.get("Amount", {})
        c, i = parse_currency_and_issuer(amount)
        if c and i and account == i:
            events.append(RawDiscoveryEvent(
                event_id=generate_event_id(tx_hash, "issuer_activity"),
                event_type="issuer_activity",
                issuer=i,
                currency_code=c,
                ledger_index=ledger_index,
                tx_hash=tx_hash,
                validated=validated,
                metadata_present=metadata_present,
                observed_at=observed_at,
                limitations=limitations.copy()
            ))

    return events

def process_transactions(txs: List[Dict[str, Any]]) -> List[RawDiscoveryEvent]:
    all_events = []
    for tx in txs:
        all_events.extend(extract_events_from_tx(tx))
    return all_events

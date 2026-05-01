import hashlib
from typing import Optional, Dict, Any
from .models import AssetKey

def normalize_asset(issuer: Optional[str], currency: str, asset_type: Optional[str] = None) -> AssetKey:
    """
    Normalizes asset information into a deterministic AssetKey.
    """
    # XRP check
    is_xrp = False
    if not issuer and currency.upper() in ["XRP", "XNS"]:
        is_xrp = True
    elif currency.upper() == "XRP" and (not issuer or issuer == ""):
        is_xrp = True
        
    if is_xrp:
        norm_currency = "XRP"
        a_type = "xrp"
        issuer = None
    else:
        norm_currency = currency.upper()
        a_type = asset_type or "issued_currency"
        
    # Generate ID
    key_id = AssetKey.generate_id(issuer, norm_currency)
    
    return AssetKey(
        issuer=issuer,
        currency_code=currency,
        normalized_currency=norm_currency,
        asset_type=a_type,
        asset_key_id=key_id
    )

def generate_deterministic_id(data: Dict[str, Any], salt: str = "") -> str:
    """
    Generates a deterministic ID from a dictionary by sorting keys.
    """
    serialized = json.dumps(data, sort_keys=True)
    raw = f"{salt}:{serialized}"
    return hashlib.sha256(raw.encode()).hexdigest()

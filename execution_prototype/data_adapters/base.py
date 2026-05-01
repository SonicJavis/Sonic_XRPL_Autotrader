from abc import ABC, abstractmethod
from typing import List, Dict, Any
from .models import DataAdapterConfig, RawSourceRecord

class BaseDataAdapter(ABC):
    def __init__(self, config: DataAdapterConfig):
        self.config = config
        
    def _check_safety(self):
        if not self.config.network_read_enabled and self.config.source_type != "fixture":
            raise PermissionError(f"Network read disabled for source type: {self.config.source_type}. Use --enable-network-read.")
        
    @abstractmethod
    def fetch_records(self) -> List[RawSourceRecord]:
        """
        Fetches raw records from the source.
        """
        pass
        
    def _generate_record_id(self, payload: Dict[str, Any], salt: str = "") -> str:
        import hashlib
        import json
        serialized = json.dumps(payload, sort_keys=True)
        raw = f"{self.config.source_type}:{salt}:{serialized}"
        return hashlib.sha256(raw.encode()).hexdigest()

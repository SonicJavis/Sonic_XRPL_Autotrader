from typing import List, Dict, Any
from .base import BaseDataAdapter
from .models import RawSourceRecord

class XrplRpcAdapter(BaseDataAdapter):
    def fetch_records(self) -> List[RawSourceRecord]:
        self._check_safety()
        
        if self.config.dry_run:
            print(f"Dry run: Would fetch from XRPL RPC endpoint {self.config.endpoint}")
            return []
            
        print(f"Fetching from XRPL RPC: {self.config.endpoint}")
        return []

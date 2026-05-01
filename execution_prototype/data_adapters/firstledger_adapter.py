from typing import List, Dict, Any
from .base import BaseDataAdapter
from .models import RawSourceRecord

class FirstLedgerAdapter(BaseDataAdapter):
    def fetch_records(self) -> List[RawSourceRecord]:
        self._check_safety()
        
        if self.config.dry_run:
            print(f"Dry run: Would fetch from FirstLedger API")
            return []
            
        print("Fetching from FirstLedger API")
        return []

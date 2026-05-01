from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class SourceConfig:
    source_name: str
    is_public: bool
    rate_limit: int
    requires_auth: bool
    limitations: list[str]

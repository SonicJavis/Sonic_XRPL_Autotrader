from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Mapping


@dataclass(slots=True)
class AppendOnlySimulationStore:
    _rows: list[dict[str, object]] = field(default_factory=list)

    def append(self, result: Mapping[str, object]) -> dict[str, object]:
        row = dict(result)
        row["append_index"] = len(self._rows) + 1
        self._rows.append(row)
        return dict(row)

    def list(self, *, limit: int = 500) -> list[dict[str, object]]:
        safe_limit = min(max(int(limit), 1), 5000)
        return [dict(row) for row in reversed(self._rows[-safe_limit:])]

    def get(self, simulation_id: str) -> dict[str, object] | None:
        for row in reversed(self._rows):
            if row.get("simulation_id") == simulation_id:
                return dict(row)
        return None

    def extend(self, results: Iterable[Mapping[str, object]]) -> list[dict[str, object]]:
        return [self.append(result) for result in results]

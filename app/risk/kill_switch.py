from __future__ import annotations


class KillSwitch:
    def __init__(self) -> None:
        self._engaged = False

    def engage(self) -> None:
        self._engaged = True

    def disengage(self) -> None:
        self._engaged = False

    def is_engaged(self) -> bool:
        return self._engaged

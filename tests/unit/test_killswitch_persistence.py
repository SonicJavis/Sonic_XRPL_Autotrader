from __future__ import annotations

from pathlib import Path

from sonic_xrpl.core.killswitch import PersistentKillSwitch


def test_killswitch_persists_state_across_instances(tmp_path: Path) -> None:
    db_path = tmp_path / "state.db"
    ks1 = PersistentKillSwitch(db_path)
    state1 = ks1.set_state(is_active=True, reason="test_activate", updated_by="pytest")
    ks1.close()

    ks2 = PersistentKillSwitch(db_path)
    state2 = ks2.get_state()
    ks2.close()

    assert state1.is_active is True
    assert state2.is_active is True
    assert state2.reason == "test_activate"
    assert state2.updated_by == "pytest"


def test_killswitch_assert_execution_allowed_raises_when_active(tmp_path: Path) -> None:
    db_path = tmp_path / "state.db"
    ks = PersistentKillSwitch(db_path)
    ks.set_state(is_active=True, reason="maintenance", updated_by="pytest")
    try:
        ks.assert_execution_allowed()
        assert False, "Expected RuntimeError for active killswitch"
    except RuntimeError as exc:
        assert str(exc) == "killswitch_active"
    finally:
        ks.close()

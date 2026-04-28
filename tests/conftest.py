from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path


def _build_test_database_url() -> tuple[Path, Path, str]:
    temp_dir = Path(tempfile.mkdtemp(prefix="sonic-xrpl-pytest-"))
    db_path = temp_dir / "sonic_autotrader_test.db"
    db_url = f"sqlite:///{db_path.resolve().as_posix()}"
    return temp_dir, db_path, db_url


def _cleanup_sqlite_artifacts(db_path: Path) -> None:
    for suffix in ("", "-journal", "-wal", "-shm"):
        artifact = Path(f"{db_path}{suffix}")
        if artifact.exists():
            artifact.unlink()


_TEST_DB_DIR, _TEST_DB_PATH, _TEST_DATABASE_URL = _build_test_database_url()

# Force pytest to use an isolated SQLite database before any app modules import
# app.db.session and bind the global SQLModel engine.
os.environ["DATABASE_URL"] = _TEST_DATABASE_URL


def pytest_sessionfinish(session, exitstatus) -> None:  # type: ignore[no-untyped-def]
    try:
        from app.db.session import engine

        engine.dispose()
    except Exception:
        pass

    try:
        _cleanup_sqlite_artifacts(_TEST_DB_PATH)
    finally:
        shutil.rmtree(_TEST_DB_DIR, ignore_errors=True)
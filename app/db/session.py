"""SQLAlchemy / SQLModel database session management."""

from __future__ import annotations

from sqlmodel import Session, SQLModel, create_engine

from app.config import settings

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},  # needed for SQLite
    echo=False,
)


def create_db_and_tables() -> None:
    """Create all tables (idempotent)."""
    SQLModel.metadata.create_all(engine)


def get_session():
    """FastAPI dependency — yields a DB session."""
    with Session(engine) as session:
        yield session

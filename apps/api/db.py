"""Database engine/session helpers for the api service.

SQLite only, per `_docs/outdated/architecture.md` §4.3. `seed.py` is the
only writer; at runtime the database is treated as read-only.
"""

from pathlib import Path

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from models import Base

# Default seed output location, per the issue's "Seed output path" constraint.
# Parameterizable — callers may pass a different path (e.g. a tmp path in tests).
DEFAULT_DB_PATH = Path(__file__).resolve().parent / "data" / "eligibility.db"


def make_engine(db_path: str | Path = DEFAULT_DB_PATH) -> Engine:
    """Create a SQLite engine for `db_path`, ensuring its parent dir exists."""
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return create_engine(f"sqlite:///{db_path}")


def make_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine)


def create_schema(engine: Engine) -> None:
    """Create all tables from the SQLAlchemy models (no hand-written SQL)."""
    Base.metadata.create_all(engine)

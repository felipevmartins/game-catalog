"""SQLite engine construction and connection invariants."""

from sqlite3 import Connection as SQLiteConnection

from sqlalchemy import Engine, create_engine, event, text
from sqlalchemy.engine import make_url
from sqlalchemy.engine.base import Engine as EngineType
from sqlalchemy.orm import Session, sessionmaker


def create_database_engine(database_url: str) -> EngineType:
    """Create an engine and enforce the SQLite connection contract."""
    url = make_url(database_url)
    if url.get_backend_name() != "sqlite":
        raise ValueError("Game Catalog supports SQLite only")

    engine = create_engine(database_url)

    @event.listens_for(engine, "connect")
    def set_sqlite_pragmas(dbapi_connection: object, _: object) -> None:
        if not isinstance(dbapi_connection, SQLiteConnection):
            raise TypeError("expected a sqlite3 connection")
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA busy_timeout=5000")
        cursor.close()

    return engine


def foreign_keys_enabled(engine: Engine) -> bool:
    """Report whether the current connection enforces foreign keys."""
    with engine.connect() as connection:
        value = connection.execute(text("PRAGMA foreign_keys")).scalar_one()
        return bool(value == 1)


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    """Create sessions whose transaction lifecycle is owned by a Unit of Work."""
    return sessionmaker(bind=engine, expire_on_commit=False)

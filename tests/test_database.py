from pathlib import Path

from game_catalog.persistence.database import create_database_engine, foreign_keys_enabled


def test_sqlite_connections_enable_foreign_keys(tmp_path: Path) -> None:
    engine = create_database_engine(f"sqlite:///{tmp_path / 'catalog.db'}")
    try:
        assert foreign_keys_enabled(engine)
    finally:
        engine.dispose()


def test_non_sqlite_database_is_rejected() -> None:
    try:
        create_database_engine("postgresql://localhost/catalog")
    except ValueError as error:
        assert str(error) == "Game Catalog supports SQLite only"
    else:
        raise AssertionError("a non-SQLite database URL was accepted")

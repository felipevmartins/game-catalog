from pathlib import Path
from sqlite3 import IntegrityError, connect

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text

from game_catalog.domain.identifiers import new_uuid7

TIMESTAMP = "2026-07-20T22:00:00.000Z"


def migrated_database(tmp_path: Path) -> tuple[Config, Path]:
    config = Config("alembic.ini")
    database = tmp_path / "reference.db"
    config.set_main_option("sqlalchemy.url", f"sqlite:///{database}")
    command.upgrade(config, "0002_reference_catalog")
    return config, database


def test_reference_catalog_schema_and_expression_indexes(tmp_path: Path) -> None:
    _, database = migrated_database(tmp_path)
    engine = create_engine(f"sqlite:///{database}")
    expected = {
        "regions",
        "manufacturers",
        "ecosystems",
        "companies",
        "franchises",
        "franchise_ecosystems",
        "platforms",
    }
    assert expected <= set(inspect(engine).get_table_names())

    with engine.connect() as connection:
        index_sql = connection.execute(
            text("SELECT sql FROM sqlite_master WHERE type = 'index' AND sql IS NOT NULL")
        ).scalars()
        definitions = "\n".join(index_sql)
    assert "uq_companies_active_identity" in definitions
    assert "COALESCE(country_code, '')" in definitions
    assert "uq_franchises_active_identity" in definitions
    assert "uq_franchise_ecosystems_identity" in definitions
    engine.dispose()


def test_partial_uniqueness_allows_reusing_soft_deleted_name(tmp_path: Path) -> None:
    _, database = migrated_database(tmp_path)
    statement = """INSERT INTO manufacturers
        (id, name, normalized_name, created_at, updated_at, deleted_at)
        VALUES (?, ?, 'nintendo', ?, ?, ?)"""
    with connect(database) as connection:
        connection.execute(statement, (str(new_uuid7()), "Nintendo", TIMESTAMP, TIMESTAMP, None))
        with pytest.raises(IntegrityError):
            connection.execute(
                statement, (str(new_uuid7()), "Duplicate", TIMESTAMP, TIMESTAMP, None)
            )
        connection.execute(
            statement,
            (str(new_uuid7()), "Historical", TIMESTAMP, TIMESTAMP, TIMESTAMP),
        )


def test_hierarchy_year_and_reference_constraints(tmp_path: Path) -> None:
    _, database = migrated_database(tmp_path)
    manufacturer_id = str(new_uuid7())
    platform_id = str(new_uuid7())
    with connect(database) as connection:
        connection.execute("PRAGMA foreign_keys=ON")
        with pytest.raises(IntegrityError):
            region_id = str(new_uuid7())
            connection.execute(
                """INSERT INTO regions
                (id, code, name, region_type, parent_region_id, active, created_at, updated_at)
                VALUES (?, 'BR', 'Brazil', 'country', ?, 1, ?, ?)""",
                (region_id, region_id, TIMESTAMP, TIMESTAMP),
            )

        connection.execute(
            """INSERT INTO manufacturers
            (id, name, normalized_name, created_at, updated_at)
            VALUES (?, 'Sony', 'sony', ?, ?)""",
            (manufacturer_id, TIMESTAMP, TIMESTAMP),
        )
        with pytest.raises(IntegrityError):
            connection.execute(
                """INSERT INTO platforms
                (id, name, normalized_name, manufacturer_id, platform_type, release_year,
                 discontinuation_year, created_at, updated_at)
                VALUES (?, 'Invalid', 'invalid', ?, 'home_console', 2020, 2019, ?, ?)""",
                (platform_id, manufacturer_id, TIMESTAMP, TIMESTAMP),
            )
        connection.execute(
            """INSERT INTO platforms
            (id, name, normalized_name, manufacturer_id, platform_type, release_year,
             discontinuation_year, created_at, updated_at)
            VALUES (?, 'PlayStation 5', 'playstation 5', ?, 'home_console', 2020, NULL, ?, ?)""",
            (platform_id, manufacturer_id, TIMESTAMP, TIMESTAMP),
        )
        with pytest.raises(IntegrityError):
            connection.execute("DELETE FROM manufacturers WHERE id = ?", (manufacturer_id,))


def test_franchise_end_status_requires_confirmation(tmp_path: Path) -> None:
    _, database = migrated_database(tmp_path)
    with connect(database) as connection, pytest.raises(IntegrityError):
        connection.execute(
            """INSERT INTO franchises
            (id, name, normalized_name, status, official_end_confirmed, created_at, updated_at)
            VALUES (?, 'Series', 'series', 'officially_ended', 0, ?, ?)""",
            (str(new_uuid7()), TIMESTAMP, TIMESTAMP),
        )


def test_downgrade_to_0001_removes_reference_catalog(tmp_path: Path) -> None:
    config, database = migrated_database(tmp_path)
    command.downgrade(config, "0001_foundation")

    engine = create_engine(f"sqlite:///{database}")
    tables = set(inspect(engine).get_table_names())
    assert "regions" not in tables
    assert "platforms" not in tables
    with engine.connect() as connection:
        version = connection.execute(
            text("SELECT schema_version FROM schema_metadata WHERE id = 1")
        ).scalar_one()
    assert version == "0001_foundation"
    engine.dispose()

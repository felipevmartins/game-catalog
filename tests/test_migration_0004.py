from pathlib import Path
from sqlite3 import IntegrityError, connect

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text

from game_catalog.domain.identifiers import new_uuid7

NOW = "2026-07-20T22:00:00.000Z"


def migrated_database(tmp_path: Path) -> tuple[Config, Path]:
    config = Config("alembic.ini")
    database = tmp_path / "sources.db"
    config.set_main_option("sqlalchemy.url", f"sqlite:///{database}")
    command.upgrade(config, "head")
    return config, database


def insert_source(connection: object) -> str:
    source_id = str(new_uuid7())
    connection.execute(
        """INSERT INTO sources
        (id,code,name,source_type,integration_type,priority,default_confidence,
         enabled,credential_required,redistribution_policy,created_at,updated_at)
        VALUES (?,'manual','Manual','manual','manual',100,'high',1,0,'allowed',?,?)""",
        (source_id, NOW, NOW),
    )
    return source_id


def test_sources_schema_and_deferred_alias_fk(tmp_path: Path) -> None:
    _, database = migrated_database(tmp_path)
    tables = set(inspect(create_engine(f"sqlite:///{database}")).get_table_names())
    expected = {
        "sources",
        "source_references",
        "record_source_links",
        "catalog_assertions",
        "game_external_ids",
        "edition_external_ids",
        "release_external_ids",
        "platform_external_ids",
        "company_external_ids",
        "franchise_external_ids",
        "product_external_ids",
    }
    assert expected <= tables
    foreign_keys = inspect(create_engine(f"sqlite:///{database}")).get_foreign_keys("game_aliases")
    assert any(fk["referred_table"] == "source_references" for fk in foreign_keys)


def test_provenance_primary_and_accepted_assertions_are_unique(tmp_path: Path) -> None:
    _, database = migrated_database(tmp_path)
    entity_id = str(new_uuid7())
    with connect(database) as connection:
        connection.execute("PRAGMA foreign_keys=ON")
        source_id = insert_source(connection)
        reference_id = str(new_uuid7())
        connection.execute(
            """INSERT INTO source_references
            (id,source_id,source_record_id,retrieved_at,created_at)
            VALUES (?,?,?, ?, ?)""",
            (reference_id, source_id, "record-1", NOW, NOW),
        )
        connection.execute(
            """INSERT INTO record_source_links
            (id,entity_type,entity_id,source_reference_id,link_role,created_at)
            VALUES (?,'game',?,?,'primary',?)""",
            (str(new_uuid7()), entity_id, reference_id, NOW),
        )
        with pytest.raises(IntegrityError):
            connection.execute(
                """INSERT INTO record_source_links
                (id,entity_type,entity_id,source_reference_id,link_role,created_at)
                VALUES (?,'game',?,?,'primary',?)""",
                (str(new_uuid7()), entity_id, reference_id, NOW),
            )
        assertion = """INSERT INTO catalog_assertions
            (id,entity_type,entity_id,field_name,value_json,source_reference_id,
             confidence,status,is_manual_override,observed_at,created_at,updated_at)
            VALUES (?,'game',?,'canonical_title',?,?,'high','accepted',0,?,?,?)"""
        connection.execute(
            assertion,
            (str(new_uuid7()), entity_id, '"Title"', reference_id, NOW, NOW, NOW),
        )
        with pytest.raises(IntegrityError):
            connection.execute(
                assertion,
                (str(new_uuid7()), entity_id, '"Other"', reference_id, NOW, NOW, NOW),
            )


def test_external_identifier_uniqueness_and_cascade(tmp_path: Path) -> None:
    _, database = migrated_database(tmp_path)
    platform_id = str(new_uuid7())
    with connect(database) as connection:
        connection.execute("PRAGMA foreign_keys=ON")
        source_id = insert_source(connection)
        connection.execute(
            """INSERT INTO platforms
            (id,name,normalized_name,platform_type,created_at,updated_at)
            VALUES (?,'Platform','platform','other',?,?)""",
            (platform_id, NOW, NOW),
        )
        statement = """INSERT INTO platform_external_ids
            (id,platform_id,source_id,external_id,context,is_primary,created_at,updated_at)
            VALUES (?,?,?,'p-1','global',1,?,?)"""
        connection.execute(statement, (str(new_uuid7()), platform_id, source_id, NOW, NOW))
        with pytest.raises(IntegrityError):
            connection.execute(statement, (str(new_uuid7()), platform_id, source_id, NOW, NOW))
        connection.execute("DELETE FROM platforms WHERE id=?", (platform_id,))
        assert connection.execute("SELECT count(*) FROM platform_external_ids").fetchone()[0] == 0


def test_downgrade_to_0003_removes_source_tables(tmp_path: Path) -> None:
    config, database = migrated_database(tmp_path)
    command.downgrade(config, "0003_game_identity")
    engine = create_engine(f"sqlite:///{database}")
    assert "sources" not in inspect(engine).get_table_names()
    with engine.connect() as connection:
        assert (
            connection.execute(text("SELECT schema_version FROM schema_metadata")).scalar_one()
            == "0003_game_identity"
        )
    engine.dispose()

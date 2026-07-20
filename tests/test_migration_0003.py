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
    database = tmp_path / "identity.db"
    config.set_main_option("sqlalchemy.url", f"sqlite:///{database}")
    command.upgrade(config, "head")
    return config, database


def seed_release_parents(connection: object) -> tuple[str, str]:
    region_id, platform_id = str(new_uuid7()), str(new_uuid7())
    connection.execute(
        "INSERT INTO regions (id,code,name,region_type,active,created_at,updated_at) "
        "VALUES (?,'WORLD','World','global',1,?,?)",
        (region_id, NOW, NOW),
    )
    connection.execute(
        "INSERT INTO platforms (id,name,normalized_name,platform_type,created_at,updated_at) "
        "VALUES (?,'Test','test','other',?,?)",
        (platform_id, NOW, NOW),
    )
    return region_id, platform_id


def test_identity_schema_and_complete_chain(tmp_path: Path) -> None:
    _, database = migrated_database(tmp_path)
    expected = {
        "games",
        "game_editions",
        "releases",
        "products",
        "game_aliases",
        "game_relations",
        "game_contents",
    }
    assert expected <= set(inspect(create_engine(f"sqlite:///{database}")).get_table_names())
    game_id, edition_id, release_id, product_id = (str(new_uuid7()) for _ in range(4))
    with connect(database) as connection:
        connection.execute("PRAGMA foreign_keys=ON")
        region_id, platform_id = seed_release_parents(connection)
        connection.execute(
            "INSERT INTO games (id,canonical_title,normalized_title,game_type,campaign_focus,"
            "online_only,regional_only,historically_relevant,collector_relevant,"
            "created_at,updated_at) "
            "VALUES (?,'Game','game','main','primary',0,0,0,0,?,?)",
            (game_id, NOW, NOW),
        )
        connection.execute(
            "INSERT INTO game_editions (id,game_id,identity_discriminator,name,normalized_name,"
            "edition_type,is_definitive,created_at,updated_at) VALUES (?,?,'original','Original',"
            "'original','original',0,?,?)",
            (edition_id, game_id, NOW, NOW),
        )
        connection.execute(
            "INSERT INTO releases (id,edition_id,platform_id,region_id,release_type,"
            "identity_discriminator,release_precision,identity_key,official,created_at,updated_at) "
            "VALUES (?,?,?,?,'original','default','unknown',?,1,?,?)",
            (
                release_id,
                edition_id,
                platform_id,
                region_id,
                f"{edition_id}:{platform_id}:{region_id}:default",
                NOW,
                NOW,
            ),
        )
        connection.execute(
            "INSERT INTO products (id,release_id,product_type,identity_discriminator,identity_key,"
            "created_at,updated_at) VALUES (?,?,'physical','physical',?, ?, ?)",
            (product_id, release_id, f"{release_id}:physical", NOW, NOW),
        )
        counts = [
            connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
            for table in ("games", "game_editions", "releases", "products")
        ]
        assert counts == [1, 1, 1, 1]


def test_original_discriminator_partial_date_and_relation_constraints(tmp_path: Path) -> None:
    _, database = migrated_database(tmp_path)
    game_id, edition_id = str(new_uuid7()), str(new_uuid7())
    with connect(database) as connection:
        connection.execute("PRAGMA foreign_keys=ON")
        region_id, platform_id = seed_release_parents(connection)
        connection.execute(
            "INSERT INTO games (id,canonical_title,normalized_title,game_type,campaign_focus,"
            "online_only,regional_only,historically_relevant,collector_relevant,"
            "created_at,updated_at) "
            "VALUES (?,'Game','game','main','primary',0,0,0,0,?,?)",
            (game_id, NOW, NOW),
        )
        connection.execute(
            "INSERT INTO game_editions (id,game_id,identity_discriminator,name,normalized_name,"
            "edition_type,is_definitive,created_at,updated_at) VALUES (?,?,'original','Original',"
            "'original','original',0,?,?)",
            (edition_id, game_id, NOW, NOW),
        )
        with pytest.raises(IntegrityError):
            connection.execute(
                "INSERT INTO game_editions (id,game_id,identity_discriminator,name,normalized_name,"
                "edition_type,is_definitive,created_at,updated_at) VALUES (?,?,'other','Other',"
                "'other','original',0,?,?)",
                (str(new_uuid7()), game_id, NOW, NOW),
            )
        with pytest.raises(IntegrityError):
            connection.execute(
                "INSERT INTO releases (id,edition_id,platform_id,region_id,release_type,"
                "identity_discriminator,release_year,release_precision,identity_key,"
                "official,created_at,updated_at) "
                "VALUES (?,?,?,?,'original','default',NULL,'year','bad',1,?,?)",
                (str(new_uuid7()), edition_id, platform_id, region_id, NOW, NOW),
            )
        with pytest.raises(IntegrityError):
            connection.execute(
                "INSERT INTO game_relations "
                "(id,source_game_id,target_game_id,relation_type,confidence,created_at,updated_at) "
                "VALUES (?,?,?,'remake_of','high',?,?)",
                (str(new_uuid7()), game_id, game_id, NOW, NOW),
            )


def test_downgrade_to_0002_removes_identity_tables(tmp_path: Path) -> None:
    config, database = migrated_database(tmp_path)
    command.downgrade(config, "0002_reference_catalog")
    engine = create_engine(f"sqlite:///{database}")
    assert "games" not in inspect(engine).get_table_names()
    with engine.connect() as connection:
        assert (
            connection.execute(text("SELECT schema_version FROM schema_metadata")).scalar_one()
            == "0002_reference_catalog"
        )
    engine.dispose()

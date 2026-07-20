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
    database = tmp_path / "collection.db"
    config.set_main_option("sqlalchemy.url", f"sqlite:///{database}")
    command.upgrade(config, "head")
    return config, database


def seed_two_chains(connection: object) -> dict[str, str]:
    ids = {
        name: str(new_uuid7())
        for name in (
            "region",
            "platform",
            "game1",
            "game2",
            "edition1",
            "edition2",
            "release1",
            "release2",
            "product1",
            "product2",
        )
    }
    connection.execute(
        "INSERT INTO regions (id,code,name,region_type,active,created_at,updated_at) VALUES (?,'WORLD','World','global',1,?,?)",
        (ids["region"], NOW, NOW),
    )
    connection.execute(
        "INSERT INTO platforms (id,name,normalized_name,platform_type,created_at,updated_at) VALUES (?,'Test','test','other',?,?)",
        (ids["platform"], NOW, NOW),
    )
    for number in (1, 2):
        connection.execute(
            "INSERT INTO games (id,canonical_title,normalized_title,game_type,campaign_focus,online_only,regional_only,historically_relevant,collector_relevant,created_at,updated_at) VALUES (?,?,?,'main','primary',0,0,0,0,?,?)",
            (ids[f"game{number}"], f"Game {number}", f"game {number}", NOW, NOW),
        )
        connection.execute(
            "INSERT INTO game_editions (id,game_id,identity_discriminator,name,normalized_name,edition_type,is_definitive,created_at,updated_at) VALUES (?,?,'original','Original','original','original',0,?,?)",
            (ids[f"edition{number}"], ids[f"game{number}"], NOW, NOW),
        )
        connection.execute(
            "INSERT INTO releases (id,edition_id,platform_id,region_id,release_type,identity_discriminator,release_precision,identity_key,official,created_at,updated_at) VALUES (?,?,?,?,'original','default','unknown',?,1,?,?)",
            (
                ids[f"release{number}"],
                ids[f"edition{number}"],
                ids["platform"],
                ids["region"],
                f"release-{number}",
                NOW,
                NOW,
            ),
        )
        connection.execute(
            "INSERT INTO products (id,release_id,product_type,identity_discriminator,identity_key,created_at,updated_at) VALUES (?,?,'physical','physical',?, ?, ?)",
            (ids[f"product{number}"], ids[f"release{number}"], f"product-{number}", NOW, NOW),
        )
    return ids


def test_multiple_collection_items_and_chain_trigger(tmp_path: Path) -> None:
    _, database = migrated_database(tmp_path)
    with connect(database) as connection:
        connection.execute("PRAGMA foreign_keys=ON")
        ids = seed_two_chains(connection)
        statement = """INSERT INTO personal_collection_items
        (id,game_id,edition_id,release_id,product_id,ownership_status,ownership_format,
         purchase_amount_minor,purchase_currency_code,played,completed,created_at,updated_at)
        VALUES (?,?,?,?,?,'owned','physical',1000,'BRL',0,0,?,?)"""
        connection.execute(
            statement,
            (
                str(new_uuid7()),
                ids["game1"],
                ids["edition1"],
                ids["release1"],
                ids["product1"],
                NOW,
                NOW,
            ),
        )
        connection.execute(
            statement,
            (
                str(new_uuid7()),
                ids["game1"],
                ids["edition1"],
                ids["release1"],
                ids["product1"],
                NOW,
                NOW,
            ),
        )
        assert (
            connection.execute("SELECT count(*) FROM personal_collection_items").fetchone()[0] == 2
        )
        with pytest.raises(IntegrityError):
            connection.execute(
                statement,
                (
                    str(new_uuid7()),
                    ids["game1"],
                    ids["edition1"],
                    ids["release1"],
                    ids["product2"],
                    NOW,
                    NOW,
                ),
            )


@pytest.mark.parametrize(
    "status,columns,values",
    [
        ("owned", "purchase_amount_minor", "100"),
        ("loaned_out", "private_notes", "NULL"),
        ("owned", "completed", "1"),
        ("owned", "personal_score", "11"),
    ],
)
def test_personal_constraints(status: str, columns: str, values: str, tmp_path: Path) -> None:
    _, database = migrated_database(tmp_path)
    with connect(database) as connection:
        connection.execute("PRAGMA foreign_keys=ON")
        ids = seed_two_chains(connection)
        with pytest.raises(IntegrityError):
            connection.execute(
                f"INSERT INTO personal_collection_items (id,game_id,ownership_status,"
                f"ownership_format,{columns},created_at,updated_at) "
                f"VALUES (?,? ,?,'unknown',{values},?,?)",
                (str(new_uuid7()), ids["game1"], status, NOW, NOW),
            )


def test_downgrade_refuses_personal_data_and_allows_empty_database(tmp_path: Path) -> None:
    config, database = migrated_database(tmp_path)
    with connect(database) as connection:
        connection.execute("PRAGMA foreign_keys=ON")
        ids = seed_two_chains(connection)
        connection.execute(
            "INSERT INTO personal_collection_items (id,game_id,ownership_status,ownership_format,played,completed,created_at,updated_at) VALUES (?,?,'owned','unknown',0,0,?,?)",
            (str(new_uuid7()), ids["game1"], NOW, NOW),
        )
    with pytest.raises(RuntimeError):
        command.downgrade(config, "0005_catalog_facts_and_availability")

    empty_path = tmp_path / "empty"
    empty_path.mkdir()
    empty_config, empty_database = migrated_database(empty_path)
    command.downgrade(empty_config, "0005_catalog_facts_and_availability")
    engine = create_engine(f"sqlite:///{empty_database}")
    assert "personal_collection_items" not in inspect(engine).get_table_names()
    with engine.connect() as connection:
        assert (
            connection.execute(text("SELECT schema_version FROM schema_metadata")).scalar_one()
            == "0005_catalog_facts_and_availability"
        )

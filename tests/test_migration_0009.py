from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text

from game_catalog.domain.identifiers import new_uuid7

NOW = "2026-07-20T22:00:00.000Z"


def migrated_database(tmp_path: Path) -> tuple[Config, object]:
    config = Config("alembic.ini")
    database = tmp_path / "seeds.db"
    config.set_main_option("sqlalchemy.url", f"sqlite:///{database}")
    command.upgrade(config, "head")
    return config, create_engine(f"sqlite:///{database}")


def test_minimum_reference_seeds_are_deterministic(tmp_path: Path) -> None:
    _, engine = migrated_database(tmp_path)
    with engine.connect() as connection:
        assert connection.execute(
            text("SELECT code FROM regions ORDER BY code")
        ).scalars().all() == [
            "JP",
            "NA",
            "WORLD",
        ]
        assert connection.execute(
            text("SELECT normalized_name FROM platforms ORDER BY normalized_name")
        ).scalars().all() == [
            "nintendo ds",
            "playstation",
            "playstation 5",
            "super nintendo entertainment system",
        ]
        assert (
            connection.execute(text("SELECT count(*) FROM platform_lock_reasons")).scalar_one() == 4
        )
        source = connection.execute(
            text("SELECT source_type,integration_type,enabled FROM sources WHERE code='manual'")
        ).one()
        assert source == ("manual", "manual", 1)
        ids = connection.execute(
            text(
                "SELECT id FROM regions UNION ALL SELECT id FROM platforms UNION ALL SELECT id FROM sources"
            )
        ).scalars()
        assert all(value[14] == "7" for value in ids)


def test_seed_downgrade_removes_unreferenced_rows(tmp_path: Path) -> None:
    config, engine = migrated_database(tmp_path)
    engine.dispose()
    command.downgrade(config, "0008_incremental_operations")
    with create_engine(config.get_main_option("sqlalchemy.url")).connect() as connection:
        assert connection.execute(text("SELECT count(*) FROM regions")).scalar_one() == 0
        assert connection.execute(text("SELECT count(*) FROM sources")).scalar_one() == 0


def test_seed_downgrade_preserves_referenced_rows(tmp_path: Path) -> None:
    config, engine = migrated_database(tmp_path)
    with engine.begin() as connection:
        platform_id = connection.execute(
            text("SELECT id FROM platforms WHERE normalized_name='playstation 5'")
        ).scalar_one()
        region_id = connection.execute(
            text("SELECT id FROM regions WHERE code='WORLD'")
        ).scalar_one()
        game_id, edition_id, release_id = (str(new_uuid7()) for _ in range(3))
        connection.execute(
            text(
                "INSERT INTO games (id,canonical_title,normalized_title,game_type,campaign_focus,online_only,regional_only,historically_relevant,collector_relevant,created_at,updated_at) VALUES (:id,'Seed test','seed test','main','primary',0,0,0,0,:now,:now)"
            ),
            {"id": game_id, "now": NOW},
        )
        connection.execute(
            text(
                "INSERT INTO game_editions (id,game_id,identity_discriminator,name,normalized_name,edition_type,is_definitive,created_at,updated_at) VALUES (:id,:game,'original','Original','original','original',0,:now,:now)"
            ),
            {"id": edition_id, "game": game_id, "now": NOW},
        )
        connection.execute(
            text(
                "INSERT INTO releases (id,edition_id,platform_id,region_id,release_type,identity_discriminator,release_precision,identity_key,official,created_at,updated_at) VALUES (:id,:edition,:platform,:region,'original','default','unknown','seed-release',1,:now,:now)"
            ),
            {
                "id": release_id,
                "edition": edition_id,
                "platform": platform_id,
                "region": region_id,
                "now": NOW,
            },
        )
    engine.dispose()
    command.downgrade(config, "0008_incremental_operations")
    with create_engine(config.get_main_option("sqlalchemy.url")).connect() as connection:
        assert (
            connection.execute(
                text("SELECT count(*) FROM platforms WHERE normalized_name='playstation 5'")
            ).scalar_one()
            == 1
        )
        assert (
            connection.execute(text("SELECT count(*) FROM regions WHERE code='WORLD'")).scalar_one()
            == 1
        )

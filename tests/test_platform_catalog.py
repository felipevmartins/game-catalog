import json
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text

from game_catalog.application.platform_catalog import PlatformCatalogService
from game_catalog.application.unit_of_work import UnitOfWork
from game_catalog.persistence.database import create_database_engine, create_session_factory


def test_platform_catalog_sync_is_complete_dry_run_safe_and_idempotent(tmp_path: Path) -> None:
    catalog_path = Path("data/import/platform_catalog.json")
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    assert len(catalog["platforms"]) == 39
    assert {item["ecosystem"] for item in catalog["platforms"]} == {
        "playstation",
        "xbox",
        "nintendo",
    }

    database = tmp_path / "catalog.db"
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", f"sqlite:///{database}")
    command.upgrade(config, "head")
    engine = create_database_engine(f"sqlite:///{database}")
    sessions = create_session_factory(engine)
    service = PlatformCatalogService(lambda: UnitOfWork(sessions))

    dry_run = service.sync(catalog_path, dry_run=True)
    assert dry_run.manufacturers_inserted == 3
    with create_engine(f"sqlite:///{database}").connect() as connection:
        assert connection.execute(text("SELECT count(*) FROM platforms")).scalar_one() == 4

    first = service.sync(catalog_path, dry_run=False)
    second = service.sync(catalog_path, dry_run=False)
    assert first.manufacturers_inserted == 3
    assert first.ecosystems_inserted == 1
    assert first.platforms_inserted == 35
    assert first.links_inserted == 39
    assert second.manufacturers_inserted == 0
    assert second.ecosystems_inserted == 0
    assert second.platforms_inserted == 0
    assert second.records_updated == 0
    assert second.links_inserted == 0
    with create_engine(f"sqlite:///{database}").connect() as connection:
        assert connection.execute(text("SELECT count(*) FROM platforms")).scalar_one() == 39
        assert connection.execute(text("SELECT count(*) FROM manufacturers")).scalar_one() == 3
        assert (
            connection.execute(
                text(
                    "SELECT count(*) FROM platforms p "
                    "JOIN manufacturers m ON m.id=p.manufacturer_id "
                    "JOIN ecosystems e ON e.id=p.ecosystem_id"
                )
            ).scalar_one()
            == 39
        )

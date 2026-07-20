from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from game_catalog.application.identity import IdentityService
from game_catalog.application.unit_of_work import UnitOfWork
from game_catalog.persistence.database import create_database_engine, create_session_factory
from game_catalog.persistence.models import Game, GameEdition


def service_for(tmp_path: Path) -> tuple[IdentityService, object]:
    database = tmp_path / "catalog.db"
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", f"sqlite:///{database}")
    command.upgrade(config, "head")
    engine = create_database_engine(f"sqlite:///{database}")
    sessions = create_session_factory(engine)
    return IdentityService(lambda: UnitOfWork(sessions)), sessions


def test_create_game_persists_mandatory_original_edition(tmp_path: Path) -> None:
    service, sessions = service_for(tmp_path)
    created = service.create_game("  Pokémon   Red  ")
    with sessions() as session:
        game = session.get(Game, created.game_id)
        edition = session.get(GameEdition, created.edition_id)
        assert game is not None
        assert game.canonical_title == "Pokémon Red"
        assert game.normalized_title == "pokemon red"
        assert edition is not None
        assert edition.game_id == game.id
        assert edition.identity_discriminator == "original"


def test_duplicate_normalized_title_is_rejected_atomically(tmp_path: Path) -> None:
    service, sessions = service_for(tmp_path)
    service.create_game("Pokémon Red")
    with pytest.raises(ValueError, match="normalized title"):
        service.create_game("Pokemon Red")
    with sessions() as session:
        assert session.scalar(select(func.count()).select_from(Game)) == 1
        assert session.scalar(select(func.count()).select_from(GameEdition)) == 1


def test_unit_of_work_rolls_back_uncommitted_changes(tmp_path: Path) -> None:
    _, sessions = service_for(tmp_path)
    with UnitOfWork(sessions) as uow:
        assert uow.regions.get_by_code("world") is not None
        assert len(uow.platforms.list_active()) == 4
    with sessions() as session:
        assert isinstance(session, Session)

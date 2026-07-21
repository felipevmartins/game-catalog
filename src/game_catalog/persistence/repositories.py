"""Repositories for the first executable catalog slice."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from game_catalog.persistence.models import (
    Game,
    GameEdition,
    PersonalCollectionItem,
    Platform,
    Region,
    Release,
)


class RegionRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_code(self, code: str) -> Region | None:
        return self.session.scalar(select(Region).where(Region.code == code.upper()))

    def list_active(self) -> list[Region]:
        return list(
            self.session.scalars(
                select(Region).where(Region.active.is_(True)).order_by(Region.code)
            )
        )


class PlatformRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_normalized_name(self, normalized_name: str) -> Platform | None:
        return self.session.scalar(
            select(Platform).where(
                Platform.normalized_name == normalized_name,
                Platform.deleted_at.is_(None),
            )
        )

    def list_active(self) -> list[Platform]:
        return list(
            self.session.scalars(
                select(Platform).where(Platform.deleted_at.is_(None)).order_by(Platform.name)
            )
        )


class GameRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, game: Game) -> None:
        self.session.add(game)

    def add_edition(self, edition: GameEdition) -> None:
        self.session.add(edition)

    def add_release(self, release: Release) -> None:
        self.session.add(release)

    def get(self, game_id: str) -> Game | None:
        return self.session.get(Game, game_id)

    def find_active_by_normalized_title(self, normalized_title: str) -> list[Game]:
        return list(
            self.session.scalars(
                select(Game).where(
                    Game.normalized_title == normalized_title,
                    Game.deleted_at.is_(None),
                )
            )
        )

    def list_active(self) -> list[Game]:
        return list(
            self.session.scalars(
                select(Game).where(Game.deleted_at.is_(None)).order_by(Game.canonical_title)
            )
        )

    def get_original_edition(self, game_id: str) -> GameEdition | None:
        return self.session.scalar(
            select(GameEdition).where(
                GameEdition.game_id == game_id,
                GameEdition.identity_discriminator == "original",
                GameEdition.deleted_at.is_(None),
            )
        )

    def get_release(self, release_id: str) -> Release | None:
        return self.session.get(Release, release_id)


class CollectionRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, item: PersonalCollectionItem) -> None:
        self.session.add(item)

    def list_items(self) -> list[PersonalCollectionItem]:
        return list(
            self.session.scalars(
                select(PersonalCollectionItem).order_by(PersonalCollectionItem.created_at)
            )
        )

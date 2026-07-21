"""Personal collection use cases."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime

from game_catalog.application.unit_of_work import UnitOfWork
from game_catalog.domain.identifiers import new_uuid7
from game_catalog.persistence.models import PersonalCollectionItem


@dataclass(frozen=True)
class AddedCollectionItem:
    item_id: str


class CollectionService:
    def __init__(self, unit_of_work: Callable[[], UnitOfWork]) -> None:
        self.unit_of_work = unit_of_work

    def add_release(self, game_id: str, release_id: str) -> AddedCollectionItem:
        now = datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")
        item_id = str(new_uuid7())
        with self.unit_of_work() as uow:
            game = uow.games.get(game_id)
            release = uow.games.get_release(release_id)
            if game is None or game.deleted_at is not None:
                raise ValueError("active game was not found")
            if release is None or release.deleted_at is not None:
                raise ValueError("active release was not found")
            edition = uow.games.get_original_edition(game_id)
            if edition is None or release.edition_id != edition.id:
                raise ValueError("release does not belong to the game")
            uow.collection.add(
                PersonalCollectionItem(
                    id=item_id,
                    game_id=game_id,
                    edition_id=edition.id,
                    release_id=release.id,
                    ownership_status="owned",
                    ownership_format="unknown",
                    played=False,
                    completed=False,
                    created_at=now,
                    updated_at=now,
                )
            )
            uow.commit()
        return AddedCollectionItem(item_id=item_id)

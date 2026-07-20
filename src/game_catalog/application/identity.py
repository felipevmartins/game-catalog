"""Identity use cases for Games and their mandatory original Edition."""

import unicodedata
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime

from game_catalog.application.unit_of_work import UnitOfWork
from game_catalog.domain.identifiers import new_uuid7
from game_catalog.persistence.models import Game, GameEdition


def normalize_name(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.strip()).encode("ascii", "ignore").decode()
    return " ".join(normalized.casefold().split())


@dataclass(frozen=True)
class CreatedGame:
    game_id: str
    edition_id: str


class IdentityService:
    def __init__(self, unit_of_work: Callable[[], UnitOfWork]) -> None:
        self.unit_of_work = unit_of_work

    def create_game(self, canonical_title: str) -> CreatedGame:
        title = " ".join(canonical_title.strip().split())
        if not title:
            raise ValueError("canonical title is required")
        normalized_title = normalize_name(title)
        now = datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")
        game_id, edition_id = str(new_uuid7()), str(new_uuid7())
        with self.unit_of_work() as uow:
            if uow.games.find_active_by_normalized_title(normalized_title):
                raise ValueError("an active game with this normalized title already exists")
            uow.games.add(
                Game(
                    id=game_id,
                    canonical_title=title,
                    normalized_title=normalized_title,
                    game_type="main",
                    campaign_focus="primary",
                    online_only=False,
                    regional_only=False,
                    historically_relevant=False,
                    collector_relevant=False,
                    created_at=now,
                    updated_at=now,
                )
            )
            uow.games.add_edition(
                GameEdition(
                    id=edition_id,
                    game_id=game_id,
                    identity_discriminator="original",
                    name="Original",
                    normalized_name="original",
                    edition_type="original",
                    is_definitive=False,
                    created_at=now,
                    updated_at=now,
                )
            )
            uow.commit()
        return CreatedGame(game_id=game_id, edition_id=edition_id)

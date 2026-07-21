"""Identity use cases for Games and their mandatory original Edition."""

import unicodedata
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime

from game_catalog.application.unit_of_work import UnitOfWork
from game_catalog.domain.identifiers import new_uuid7
from game_catalog.persistence.models import Game, GameEdition, Release


def normalize_name(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.strip()).encode("ascii", "ignore").decode()
    return " ".join(normalized.casefold().split())


@dataclass(frozen=True)
class CreatedGame:
    game_id: str
    edition_id: str


@dataclass(frozen=True)
class CreatedRelease:
    release_id: str


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

    def create_release(self, game_id: str, platform_name: str, region_code: str) -> CreatedRelease:
        platform_key = normalize_name(platform_name)
        now = datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")
        release_id = str(new_uuid7())
        with self.unit_of_work() as uow:
            game = uow.games.get(game_id)
            edition = uow.games.get_original_edition(game_id)
            platform = uow.platforms.get_by_normalized_name(platform_key)
            region = uow.regions.get_by_code(region_code)
            if game is None or game.deleted_at is not None:
                raise ValueError("active game was not found")
            if edition is None:
                raise ValueError("original edition was not found")
            if platform is None:
                raise ValueError("active platform was not found")
            if region is None or not region.active:
                raise ValueError("active region was not found")
            identity_key = f"{edition.id}:{platform.id}:{region.id}:original:default"
            uow.games.add_release(
                Release(
                    id=release_id,
                    edition_id=edition.id,
                    platform_id=platform.id,
                    region_id=region.id,
                    release_type="original",
                    identity_discriminator="default",
                    release_precision="unknown",
                    identity_key=identity_key,
                    official=True,
                    created_at=now,
                    updated_at=now,
                )
            )
            uow.commit()
        return CreatedRelease(release_id=release_id)

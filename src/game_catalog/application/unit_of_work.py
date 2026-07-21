"""Transaction boundary for application services."""

from types import TracebackType

from sqlalchemy.orm import Session, sessionmaker

from game_catalog.persistence.repositories import (
    CollectionRepository,
    GameRepository,
    PlatformRepository,
    RegionRepository,
)


class UnitOfWork:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self.session_factory = session_factory
        self.session: Session | None = None
        self.games: GameRepository
        self.collection: CollectionRepository
        self.platforms: PlatformRepository
        self.regions: RegionRepository

    def __enter__(self) -> "UnitOfWork":
        self.session = self.session_factory()
        self.games = GameRepository(self.session)
        self.collection = CollectionRepository(self.session)
        self.platforms = PlatformRepository(self.session)
        self.regions = RegionRepository(self.session)
        return self

    def __exit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if self.session is None:
            return
        if exception_type is not None:
            self.session.rollback()
        self.session.close()

    def commit(self) -> None:
        if self.session is None:
            raise RuntimeError("UnitOfWork is not active")
        self.session.commit()

    def rollback(self) -> None:
        if self.session is None:
            raise RuntimeError("UnitOfWork is not active")
        self.session.rollback()

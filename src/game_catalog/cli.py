"""Command-line interface for the local catalog."""

from pathlib import Path
from typing import Annotated

import typer
from alembic import command
from alembic.config import Config
from sqlalchemy.orm import Session, sessionmaker

from game_catalog.application.collection import CollectionService
from game_catalog.application.identity import IdentityService
from game_catalog.application.unit_of_work import UnitOfWork
from game_catalog.persistence.database import create_database_engine, create_session_factory

app = typer.Typer(no_args_is_help=True)
db_app = typer.Typer(no_args_is_help=True)
game_app = typer.Typer(no_args_is_help=True)
release_app = typer.Typer(no_args_is_help=True)
collection_app = typer.Typer(no_args_is_help=True)
app.add_typer(db_app, name="db")
app.add_typer(game_app, name="game")
app.add_typer(release_app, name="release")
app.add_typer(collection_app, name="collection")


def database_url(path: Path) -> str:
    return f"sqlite:///{path.resolve().as_posix()}"


def sessions_for(path: Path) -> sessionmaker[Session]:
    return create_session_factory(create_database_engine(database_url(path)))


@app.callback()
def main(
    context: typer.Context,
    database: Annotated[Path, typer.Option("--database", "-d")] = Path("game_catalog.db"),
) -> None:
    """Manage the local game catalog."""
    context.obj = database


def selected_database(context: typer.Context) -> Path:
    if context.parent is None or not isinstance(context.parent.obj, Path):
        raise RuntimeError("database context is unavailable")
    return context.parent.obj


@app.command()
def version() -> None:
    """Show the application version."""
    from game_catalog import __version__

    typer.echo(__version__)


@db_app.command("init")
def initialize_database(context: typer.Context) -> None:
    """Create or migrate the local database to the latest schema."""
    path = selected_database(context)
    path.parent.mkdir(parents=True, exist_ok=True)
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", database_url(path))
    command.upgrade(config, "head")
    typer.echo(f"Database ready: {path.resolve()}")


@game_app.command("add")
def add_game(context: typer.Context, title: str = typer.Argument(...)) -> None:
    """Add a Game and its mandatory original Edition."""
    path = selected_database(context)
    if not path.exists():
        raise typer.BadParameter("database does not exist; run 'db init' first")
    sessions = sessions_for(path)
    service = IdentityService(lambda: UnitOfWork(sessions))
    try:
        created = service.create_game(title)
    except ValueError as error:
        raise typer.BadParameter(str(error)) from error
    typer.echo(f"Created game {created.game_id} (edition {created.edition_id})")


@game_app.command("list")
def list_games(context: typer.Context) -> None:
    """List active Games in canonical-title order."""
    path = selected_database(context)
    if not path.exists():
        raise typer.BadParameter("database does not exist; run 'db init' first")
    sessions = sessions_for(path)
    with UnitOfWork(sessions) as uow:
        games = uow.games.list_active()
    if not games:
        typer.echo("No games found.")
        return
    for game in games:
        typer.echo(f"{game.id}\t{game.canonical_title}")


@release_app.command("add")
def add_release(
    context: typer.Context,
    game_id: str,
    platform: Annotated[str, typer.Option("--platform")],
    region: Annotated[str, typer.Option("--region")] = "WORLD",
) -> None:
    """Add an official Release for a seeded platform and region."""
    path = selected_database(context)
    if not path.exists():
        raise typer.BadParameter("database does not exist; run 'db init' first")
    sessions = sessions_for(path)
    service = IdentityService(lambda: UnitOfWork(sessions))
    try:
        created = service.create_release(game_id, platform, region)
    except ValueError as error:
        raise typer.BadParameter(str(error)) from error
    typer.echo(f"Created release {created.release_id}")


@collection_app.command("add")
def add_collection_item(context: typer.Context, game_id: str, release_id: str) -> None:
    """Add an owned Release to the private collection."""
    path = selected_database(context)
    if not path.exists():
        raise typer.BadParameter("database does not exist; run 'db init' first")
    sessions = sessions_for(path)
    service = CollectionService(lambda: UnitOfWork(sessions))
    try:
        created = service.add_release(game_id, release_id)
    except ValueError as error:
        raise typer.BadParameter(str(error)) from error
    typer.echo(f"Added collection item {created.item_id}")


@collection_app.command("list")
def list_collection(context: typer.Context) -> None:
    """List private collection items."""
    path = selected_database(context)
    if not path.exists():
        raise typer.BadParameter("database does not exist; run 'db init' first")
    sessions = sessions_for(path)
    with UnitOfWork(sessions) as uow:
        items = uow.collection.list_items()
    if not items:
        typer.echo("No collection items found.")
        return
    for item in items:
        typer.echo(f"{item.id}\tgame={item.game_id}\trelease={item.release_id}")

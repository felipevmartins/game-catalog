"""Command-line interface for the local catalog."""

import json
import os
import sys
from io import TextIOWrapper
from pathlib import Path
from typing import Annotated

import typer
from alembic import command
from alembic.config import Config
from sqlalchemy.orm import Session, sessionmaker

from game_catalog.application.collection import CollectionService
from game_catalog.application.franchise_import import FranchiseImportService
from game_catalog.application.identity import IdentityService
from game_catalog.application.legacy_import import LegacyImportService
from game_catalog.application.platform_catalog import PlatformCatalogService
from game_catalog.application.unit_of_work import UnitOfWork
from game_catalog.integrations.legacy import LegacyWikidataCollector, normalize_legacy
from game_catalog.integrations.mobygames import MobyGamesValidator
from game_catalog.integrations.wikidata import WikidataCollector, normalize_raw_directory
from game_catalog.persistence.database import create_database_engine, create_session_factory

app = typer.Typer(no_args_is_help=True)
db_app = typer.Typer(no_args_is_help=True)
game_app = typer.Typer(no_args_is_help=True)
release_app = typer.Typer(no_args_is_help=True)
collection_app = typer.Typer(no_args_is_help=True)
import_app = typer.Typer(no_args_is_help=True)
platform_app = typer.Typer(no_args_is_help=True)
legacy_app = typer.Typer(no_args_is_help=True)
app.add_typer(db_app, name="db")
app.add_typer(game_app, name="game")
app.add_typer(release_app, name="release")
app.add_typer(collection_app, name="collection")
app.add_typer(import_app, name="import")
app.add_typer(platform_app, name="platform")
app.add_typer(legacy_app, name="legacy")


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
    for stream in (sys.stdout, sys.stderr):
        if isinstance(stream, TextIOWrapper):
            stream.reconfigure(encoding="utf-8", errors="replace")
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
def list_games(
    context: typer.Context,
    limit: Annotated[int, typer.Option("--limit", min=1)] = 50,
) -> None:
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
    for game in games[:limit]:
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


@import_app.command("discover")
def discover_franchises(
    catalog: Annotated[Path, typer.Option("--catalog")] = Path(
        "data/import/franchise_catalog.json"
    ),
    raw_directory: Annotated[Path, typer.Option("--raw-dir")] = Path("data/raw/wikidata"),
) -> None:
    """Discover franchise identities and games through Wikidata."""
    records = WikidataCollector().collect(catalog, raw_directory)
    resolved = sum(item["franchise"]["resolution_status"] == "resolved" for item in records)
    typer.echo(f"Collected {len(records)} franchises; {resolved} resolved automatically.")


@import_app.command("normalize")
def normalize_franchise_discovery(
    raw_directory: Annotated[Path, typer.Option("--raw-dir")] = Path("data/raw/wikidata"),
    output: Annotated[Path, typer.Option("--output")] = Path(
        "data/normalized/franchises-games.jsonl"
    ),
    report: Annotated[Path, typer.Option("--report")] = Path("data/reports/initial-import.json"),
) -> None:
    """Convert raw discovery responses into deterministic JSON Lines."""
    counts = normalize_raw_directory(raw_directory, output, Path("data/import/game_overrides.json"))
    pending = []
    for line in output.read_text(encoding="utf-8").splitlines():
        record = json.loads(line)
        if record["record_type"] == "franchise" and record["resolution_status"] != "resolved":
            pending.append(
                {
                    "key": record["key"],
                    "canonical_name": record["canonical_name"],
                    "resolution_status": record["resolution_status"],
                    "wikidata_id": record.get("wikidata_id"),
                }
            )
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(
        json.dumps({"counts": counts, "pending_review": pending}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    typer.echo(json.dumps(counts, ensure_ascii=False, sort_keys=True))


def run_franchise_import(context: typer.Context, input_file: Path, *, dry_run: bool) -> None:
    path = selected_database(context)
    if not path.exists():
        raise typer.BadParameter("database does not exist; run 'db init' first")
    sessions = sessions_for(path)
    service = FranchiseImportService(lambda: UnitOfWork(sessions))
    result = service.apply(input_file, Path("data/import/source_registry.json"), dry_run=dry_run)
    typer.echo(json.dumps(result.to_dict(), ensure_ascii=False, sort_keys=True))


@import_app.command("dry-run")
def dry_run_franchise_import(
    context: typer.Context,
    input_file: Annotated[Path, typer.Option("--input")] = Path(
        "data/normalized/franchises-games.jsonl"
    ),
) -> None:
    """Validate and simulate the normalized import without persisting changes."""
    run_franchise_import(context, input_file, dry_run=True)


@import_app.command("apply")
def apply_franchise_import(
    context: typer.Context,
    input_file: Annotated[Path, typer.Option("--input")] = Path(
        "data/normalized/franchises-games.jsonl"
    ),
) -> None:
    """Apply the normalized import idempotently."""
    run_franchise_import(context, input_file, dry_run=False)


@platform_app.command("sync")
def sync_platforms(
    context: typer.Context,
    catalog: Annotated[Path, typer.Option("--catalog")] = Path("data/import/platform_catalog.json"),
    dry_run: Annotated[bool, typer.Option("--dry-run")] = False,
) -> None:
    """Synchronize the curated PlayStation, Xbox and Nintendo platforms."""
    path = selected_database(context)
    if not path.exists():
        raise typer.BadParameter("database does not exist; run 'db init' first")
    sessions = sessions_for(path)
    result = PlatformCatalogService(lambda: UnitOfWork(sessions)).sync(catalog, dry_run=dry_run)
    typer.echo(json.dumps(result.to_dict(), ensure_ascii=False, sort_keys=True))


@platform_app.command("list")
def list_platforms(context: typer.Context) -> None:
    """List active platform families."""
    path = selected_database(context)
    if not path.exists():
        raise typer.BadParameter("database does not exist; run 'db init' first")
    sessions = sessions_for(path)
    with UnitOfWork(sessions) as uow:
        platforms = uow.platforms.list_active()
    for record in platforms:
        typer.echo(
            f"{record.id}\t{record.name}\t{record.platform_type}\t{record.release_year or ''}"
        )


@legacy_app.command("discover")
def discover_legacy_games(
    policy: Annotated[Path, typer.Option("--policy")] = Path(
        "data/import/legacy_platform_policy.json"
    ),
    platforms: Annotated[Path, typer.Option("--platforms")] = Path(
        "data/import/platform_catalog.json"
    ),
    raw_directory: Annotated[Path, typer.Option("--raw-dir")] = Path("data/raw/wikidata-legacy"),
) -> None:
    """Discover games and all known platforms for every curated console."""
    result = LegacyWikidataCollector().collect(policy, platforms, raw_directory)
    typer.echo(json.dumps(result, ensure_ascii=False, sort_keys=True))


@legacy_app.command("normalize")
def normalize_legacy_games(
    raw_directory: Annotated[Path, typer.Option("--raw-dir")] = Path("data/raw/wikidata-legacy"),
    policy: Annotated[Path, typer.Option("--policy")] = Path(
        "data/import/legacy_platform_policy.json"
    ),
    output: Annotated[Path, typer.Option("--output")] = Path("data/normalized/legacy-games.jsonl"),
    report: Annotated[Path, typer.Option("--report")] = Path("data/reports/stranded-games.json"),
) -> None:
    """Classify platform discoveries into conservative legacy candidates."""
    typer.echo(json.dumps(normalize_legacy(raw_directory, policy, output, report), sort_keys=True))


def run_legacy_apply(context: typer.Context, input_file: Path, *, dry_run: bool) -> None:
    path = selected_database(context)
    if not path.exists():
        raise typer.BadParameter("database does not exist; run 'db init' first")
    result = LegacyImportService(lambda: UnitOfWork(sessions_for(path))).apply(
        input_file, dry_run=dry_run
    )
    typer.echo(json.dumps(result.to_dict(), ensure_ascii=False, sort_keys=True))


@legacy_app.command("dry-run")
def dry_run_legacy(
    context: typer.Context,
    input_file: Annotated[Path, typer.Option("--input")] = Path(
        "data/normalized/legacy-games.jsonl"
    ),
) -> None:
    """Validate legacy candidates without persisting assessments."""
    run_legacy_apply(context, input_file, dry_run=True)


@legacy_app.command("apply")
def apply_legacy(
    context: typer.Context,
    input_file: Annotated[Path, typer.Option("--input")] = Path(
        "data/normalized/legacy-games.jsonl"
    ),
) -> None:
    """Create dirty assessments and reviews for known legacy candidates."""
    run_legacy_apply(context, input_file, dry_run=False)


@legacy_app.command("validate")
def validate_legacy(
    input_file: Annotated[Path, typer.Option("--input")] = Path(
        "data/normalized/legacy-games.jsonl"
    ),
    config: Annotated[Path, typer.Option("--config")] = Path(
        "data/import/mobygames_validation.json"
    ),
    cache_directory: Annotated[Path, typer.Option("--cache-dir")] = Path(
        "data/raw/mobygames-legacy"
    ),
    output: Annotated[Path, typer.Option("--output")] = Path(
        "data/normalized/legacy-validation.jsonl"
    ),
    report: Annotated[Path, typer.Option("--report")] = Path("data/reports/legacy-validation.json"),
    max_requests: Annotated[int, typer.Option("--max-requests", min=0)] = 100,
) -> None:
    """Validate legacy candidates against MobyGames in resumable batches."""
    try:
        counts = MobyGamesValidator().validate(
            input_file,
            config,
            cache_directory,
            output,
            report,
            api_key=os.environ.get("MOBYGAMES_API_KEY"),
            max_requests=max_requests,
        )
    except ValueError as error:
        raise typer.BadParameter(str(error)) from error
    typer.echo(json.dumps(counts.to_dict(), ensure_ascii=False, sort_keys=True))

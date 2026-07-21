import json
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text

from game_catalog.application.franchise_import import FranchiseImportService
from game_catalog.application.unit_of_work import UnitOfWork
from game_catalog.integrations.wikidata import (
    WikidataCollector,
    load_franchise_catalog,
    normalize_raw_directory,
)
from game_catalog.persistence.database import create_database_engine, create_session_factory


def test_editorial_catalog_has_expected_scope() -> None:
    seeds = load_franchise_catalog(Path("data/import/franchise_catalog.json"))
    assert len(seeds) == 50
    assert {seed.ecosystem for seed in seeds} == {"playstation", "xbox", "nintendo"}
    assert sum(seed.inclusion_status == "review_required" for seed in seeds) == 3
    earthbound = next(seed for seed in seeds if seed.key == "earthbound")
    assert "Mother" in earthbound.aliases


def test_collector_resolves_exact_candidate_and_normalizes_games(tmp_path: Path) -> None:
    catalog = tmp_path / "catalog.json"
    catalog.write_text(
        json.dumps(
            {
                "ecosystems": [{"key": "xbox", "canonical_name": "Xbox"}],
                "franchises": [{"key": "halo", "canonical_name": "Halo", "ecosystem": "xbox"}],
            }
        ),
        encoding="utf-8",
    )

    def transport(url: str) -> dict[str, object]:
        if "wbsearchentities" in url:
            return {
                "search": [
                    {
                        "id": "Q123",
                        "label": "Halo",
                        "description": "video game franchise",
                    }
                ]
            }
        return {
            "results": {
                "bindings": [
                    {
                        "game": {"value": "http://www.wikidata.org/entity/Q456"},
                        "gameLabel": {"value": "Halo: Combat Evolved"},
                    }
                ]
            }
        }

    raw = tmp_path / "raw"
    records = WikidataCollector(transport).collect(catalog, raw)
    assert records[0]["franchise"]["wikidata_id"] == "Q123"
    normalized = tmp_path / "normalized.jsonl"
    counts = normalize_raw_directory(raw, normalized)
    assert counts == {"franchises": 1, "games": 1, "unresolved": 0, "review_required": 0}
    lines = [json.loads(line) for line in normalized.read_text(encoding="utf-8").splitlines()]
    assert lines[1]["wikidata_id"] == "Q456"


def test_approved_game_override_is_added_once(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    raw.mkdir()
    raw.joinpath("fable.json").write_text(
        json.dumps(
            {
                "franchise": {
                    "key": "fable",
                    "canonical_name": "Fable",
                    "ecosystem": "xbox",
                    "aliases": [],
                    "inclusion_status": "approved",
                    "wikidata_id": "Q1",
                    "resolution_status": "resolved",
                },
                "games_response": {"results": {"bindings": []}},
            }
        ),
        encoding="utf-8",
    )
    overrides = tmp_path / "overrides.json"
    overrides.write_text(
        json.dumps(
            {
                "games": [
                    {
                        "wikidata_id": "Q32008364",
                        "canonical_title": "Fable Anniversary",
                        "franchise_key": "fable",
                        "review_status": "approved",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    output = tmp_path / "games.jsonl"
    counts = normalize_raw_directory(raw, output, overrides)
    assert counts["games"] == 1
    assert "Fable Anniversary" in output.read_text(encoding="utf-8")


def test_import_is_dry_run_safe_and_idempotent(tmp_path: Path) -> None:
    database = tmp_path / "catalog.db"
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", f"sqlite:///{database}")
    command.upgrade(config, "head")
    normalized = tmp_path / "normalized.jsonl"
    records = [
        {
            "record_type": "franchise",
            "key": "halo",
            "canonical_name": "Halo",
            "ecosystem": "xbox",
            "aliases": [],
            "inclusion_status": "approved",
            "wikidata_id": "Q123",
            "resolution_status": "resolved",
            "source": "wikidata",
        },
        {
            "record_type": "franchise",
            "key": "ghost-of-tsushima",
            "canonical_name": "Ghost of Tsushima",
            "ecosystem": "playstation",
            "aliases": [],
            "inclusion_status": "review_required",
            "wikidata_id": "Q789",
            "resolution_status": "review_required",
            "source": "wikidata",
        },
        {
            "record_type": "game",
            "franchise_key": "halo",
            "canonical_title": "Halo: Combat Evolved",
            "normalized_title": "halo: combat evolved",
            "wikidata_id": "Q456",
            "source": "wikidata",
        },
    ]
    normalized.write_text(
        "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records),
        encoding="utf-8",
    )
    engine = create_database_engine(f"sqlite:///{database}")
    sessions = create_session_factory(engine)
    service = FranchiseImportService(lambda: UnitOfWork(sessions))

    dry_run = service.apply(normalized, Path("data/import/source_registry.json"), dry_run=True)
    assert dry_run.franchises_inserted == 2
    with create_engine(f"sqlite:///{database}").connect() as connection:
        assert connection.execute(text("SELECT count(*) FROM franchises")).scalar_one() == 0

    first = service.apply(normalized, Path("data/import/source_registry.json"), dry_run=False)
    second = service.apply(normalized, Path("data/import/source_registry.json"), dry_run=False)
    assert first.franchises_inserted == 2
    assert first.games_inserted == 1
    assert first.reviews_created == 1
    assert second.franchises_inserted == 0
    assert second.games_inserted == 0
    assert second.reviews_created == 0
    with create_engine(f"sqlite:///{database}").connect() as connection:
        assert connection.execute(text("SELECT count(*) FROM franchises")).scalar_one() == 2
        assert connection.execute(text("SELECT count(*) FROM games")).scalar_one() == 1
        assert connection.execute(text("SELECT count(*) FROM review_queue")).scalar_one() == 1
        assert connection.execute(text("SELECT count(*) FROM execution_runs")).scalar_one() == 2

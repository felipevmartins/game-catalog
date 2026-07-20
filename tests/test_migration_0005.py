from pathlib import Path
from sqlite3 import IntegrityError, connect

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text

from game_catalog.domain.identifiers import new_uuid7

NOW = "2026-07-20T22:00:00.000Z"


def migrated_database(tmp_path: Path) -> tuple[Config, Path]:
    config = Config("alembic.ini")
    database = tmp_path / "facts.db"
    config.set_main_option("sqlalchemy.url", f"sqlite:///{database}")
    command.upgrade(config, "0005_catalog_facts_and_availability")
    return config, database


def seed_catalog(connection: object) -> dict[str, str]:
    ids = {
        name: str(new_uuid7())
        for name in (
            "region",
            "platform",
            "company",
            "source",
            "reference",
            "game1",
            "game2",
            "edition1",
            "edition2",
            "release1",
            "release2",
        )
    }
    connection.execute(
        "INSERT INTO regions (id,code,name,region_type,active,created_at,updated_at) VALUES (?,'WORLD','World','global',1,?,?)",
        (ids["region"], NOW, NOW),
    )
    connection.execute(
        "INSERT INTO platforms (id,name,normalized_name,platform_type,created_at,updated_at) VALUES (?,'Test','test','other',?,?)",
        (ids["platform"], NOW, NOW),
    )
    connection.execute(
        "INSERT INTO companies (id,name,normalized_name,company_type,created_at,updated_at) VALUES (?,'Company','company','other',?,?)",
        (ids["company"], NOW, NOW),
    )
    connection.execute(
        "INSERT INTO sources (id,code,name,source_type,integration_type,priority,default_confidence,enabled,credential_required,redistribution_policy,created_at,updated_at) VALUES (?,'manual','Manual','manual','manual',100,'high',1,0,'allowed',?,?)",
        (ids["source"], NOW, NOW),
    )
    connection.execute(
        "INSERT INTO source_references (id,source_id,source_record_id,retrieved_at,created_at) VALUES (?,?,'fixture',?,?)",
        (ids["reference"], ids["source"], NOW, NOW),
    )
    for number in (1, 2):
        connection.execute(
            "INSERT INTO games (id,canonical_title,normalized_title,game_type,campaign_focus,online_only,regional_only,historically_relevant,collector_relevant,created_at,updated_at) VALUES (?,?,?,'main','primary',0,0,0,0,?,?)",
            (ids[f"game{number}"], f"Game {number}", f"game {number}", NOW, NOW),
        )
        connection.execute(
            "INSERT INTO game_editions (id,game_id,identity_discriminator,name,normalized_name,edition_type,is_definitive,created_at,updated_at) VALUES (?,?,'original','Original','original','original',0,?,?)",
            (ids[f"edition{number}"], ids[f"game{number}"], NOW, NOW),
        )
        connection.execute(
            "INSERT INTO releases (id,edition_id,platform_id,region_id,release_type,identity_discriminator,release_precision,identity_key,official,created_at,updated_at) VALUES (?,?,?,?,'original','default','unknown',?,1,?,?)",
            (
                ids[f"release{number}"],
                ids[f"edition{number}"],
                ids["platform"],
                ids["region"],
                f"release-{number}",
                NOW,
                NOW,
            ),
        )
    return ids


def test_catalog_fact_schema_and_triggers_exist(tmp_path: Path) -> None:
    _, database = migrated_database(tmp_path)
    engine = create_engine(f"sqlite:///{database}")
    expected = {
        "franchise_ownerships",
        "game_companies",
        "game_scores",
        "game_primary_scores",
        "game_lengths",
        "availability_offers",
        "platform_lock_reasons",
        "platform_lock_assessments",
        "game_platform_lock_reasons",
    }
    assert expected <= set(inspect(engine).get_table_names())
    with engine.connect() as connection:
        triggers = set(
            connection.execute(
                text("SELECT name FROM sqlite_master WHERE type='trigger'")
            ).scalars()
        )
    assert "trg_game_companies_chain_insert" in triggers
    assert "trg_game_primary_scores_chain_insert" in triggers


def test_credit_and_primary_score_triggers_reject_cross_game_chain(tmp_path: Path) -> None:
    _, database = migrated_database(tmp_path)
    with connect(database) as connection:
        connection.execute("PRAGMA foreign_keys=ON")
        ids = seed_catalog(connection)
        with pytest.raises(IntegrityError):
            connection.execute(
                "INSERT INTO game_companies (id,game_id,edition_id,release_id,company_id,role,created_at) VALUES (?,?,?,?,?,'developer',?)",
                (
                    str(new_uuid7()),
                    ids["game1"],
                    ids["edition2"],
                    ids["release2"],
                    ids["company"],
                    NOW,
                ),
            )
        score_id = str(new_uuid7())
        connection.execute(
            "INSERT INTO game_scores (id,release_id,source_id,score_value,source_reference_id,retrieved_at,created_at,updated_at) VALUES (?,?,?,90,?,?,?,?)",
            (score_id, ids["release2"], ids["source"], ids["reference"], NOW, NOW, NOW),
        )
        with pytest.raises(IntegrityError):
            connection.execute(
                "INSERT INTO game_primary_scores (game_id,score_id,selection_reason,selected_at) VALUES (?,?,'fixture',?)",
                (ids["game1"], score_id, NOW),
            )


def test_availability_history_and_lock_state_constraints(tmp_path: Path) -> None:
    _, database = migrated_database(tmp_path)
    with connect(database) as connection:
        connection.execute("PRAGMA foreign_keys=ON")
        ids = seed_catalog(connection)
        statement = """INSERT INTO availability_offers
        (id,release_id,access_platform_id,availability_type,region_id,offer_identity_key,status,is_current,
         valid_from_precision,valid_to_precision,observed_at,last_verified_at,source_reference_id,created_at,updated_at)
        VALUES (?,?,?,'digital_purchase',?,'offer-1',?,?,'unknown','unknown',?,?,?,?,?)"""
        connection.execute(
            statement,
            (
                str(new_uuid7()),
                ids["release1"],
                ids["platform"],
                ids["region"],
                "available",
                1,
                NOW,
                NOW,
                ids["reference"],
                NOW,
                NOW,
            ),
        )
        with pytest.raises(IntegrityError):
            connection.execute(
                statement,
                (
                    str(new_uuid7()),
                    ids["release1"],
                    ids["platform"],
                    ids["region"],
                    "unavailable",
                    1,
                    NOW,
                    NOW,
                    ids["reference"],
                    NOW,
                    NOW,
                ),
            )
        connection.execute(
            statement,
            (
                str(new_uuid7()),
                ids["release1"],
                ids["platform"],
                ids["region"],
                "unavailable",
                0,
                NOW,
                NOW,
                ids["reference"],
                NOW,
                NOW,
            ),
        )
        with pytest.raises(IntegrityError):
            connection.execute(
                "INSERT INTO platform_lock_assessments (game_id,locked,severity_level,content_lost,state) VALUES (?,1,NULL,0,'current')",
                (ids["game1"],),
            )
        connection.execute(
            "INSERT INTO platform_lock_assessments (game_id,locked,severity_level,content_lost,state,rule_version,input_version,calculated_at) VALUES (?,1,3,0,'current','1','1',?)",
            (ids["game1"], NOW),
        )


def test_downgrade_to_0004_removes_fact_tables(tmp_path: Path) -> None:
    config, database = migrated_database(tmp_path)
    command.downgrade(config, "0004_sources_and_external_ids")
    engine = create_engine(f"sqlite:///{database}")
    assert "availability_offers" not in inspect(engine).get_table_names()
    with engine.connect() as connection:
        assert (
            connection.execute(text("SELECT schema_version FROM schema_metadata")).scalar_one()
            == "0004_sources_and_external_ids"
        )
    engine.dispose()

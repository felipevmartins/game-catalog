from pathlib import Path
from sqlite3 import IntegrityError, connect

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

from game_catalog.domain.identifiers import new_uuid7

NOW = "2026-07-20T22:00:00.000Z"


def migrated_database(tmp_path: Path) -> tuple[Config, Path]:
    config = Config("alembic.ini")
    database = tmp_path / "catalog.db"
    config.set_main_option("sqlalchemy.url", f"sqlite:///{database}")
    command.upgrade(config, "head")
    return config, database


def seed_release(connection: object) -> dict[str, str]:
    ids = {name: str(new_uuid7()) for name in ("region", "platform", "game", "edition", "release")}
    connection.execute(
        "INSERT INTO regions (id,code,name,region_type,active,created_at,updated_at) VALUES (?,'WORLD','World','global',1,?,?)",
        (ids["region"], NOW, NOW),
    )
    connection.execute(
        "INSERT INTO platforms (id,name,normalized_name,platform_type,created_at,updated_at) VALUES (?,'Test','test','other',?,?)",
        (ids["platform"], NOW, NOW),
    )
    connection.execute(
        "INSERT INTO games (id,canonical_title,normalized_title,game_type,campaign_focus,online_only,regional_only,historically_relevant,collector_relevant,created_at,updated_at) VALUES (?,'Game','game','main','primary',0,0,0,0,?,?)",
        (ids["game"], NOW, NOW),
    )
    connection.execute(
        "INSERT INTO game_editions (id,game_id,identity_discriminator,name,normalized_name,edition_type,is_definitive,created_at,updated_at) VALUES (?,?,'original','Original','original','original',0,?,?)",
        (ids["edition"], ids["game"], NOW, NOW),
    )
    connection.execute(
        "INSERT INTO releases (id,edition_id,platform_id,region_id,release_type,identity_discriminator,release_precision,identity_key,official,created_at,updated_at) VALUES (?,?,?,?,'original','default','unknown','release',1,?,?)",
        (ids["release"], ids["edition"], ids["platform"], ids["region"], NOW, NOW),
    )
    return ids


def test_hardware_schema_contains_complete_slice(tmp_path: Path) -> None:
    _, database = migrated_database(tmp_path)
    tables = set(inspect(create_engine(f"sqlite:///{database}")).get_table_names())
    assert {
        "hardware_models",
        "hardware_model_external_ids",
        "personal_hardware_units",
        "accessory_models",
        "accessory_platforms",
        "personal_accessory_units",
        "personal_capabilities",
        "hardware_compatibility_rules",
        "compatibility_rule_releases",
        "game_requirement_groups",
        "game_hardware_requirements",
        "personal_playability",
    } <= tables


def test_requirements_and_accessory_adapter_constraints(tmp_path: Path) -> None:
    _, database = migrated_database(tmp_path)
    with connect(database) as connection:
        connection.execute("PRAGMA foreign_keys=ON")
        ids = seed_release(connection)
        hardware_id, accessory_id, group_id = (str(new_uuid7()) for _ in range(3))
        connection.execute(
            "INSERT INTO hardware_models (id,platform_id,name,normalized_name,hardware_type,created_at,updated_at) VALUES (?,?, 'Console','console','console',?,?)",
            (hardware_id, ids["platform"], NOW, NOW),
        )
        connection.execute(
            "INSERT INTO accessory_models (id,name,normalized_name,accessory_type,created_at,updated_at) VALUES (?,'Controller','controller','controller',?,?)",
            (accessory_id, NOW, NOW),
        )
        with pytest.raises(IntegrityError):
            connection.execute(
                "INSERT INTO accessory_platforms (accessory_model_id,platform_id,support_level) VALUES (?,?,'adapter_required')",
                (accessory_id, ids["platform"]),
            )
        connection.execute(
            "INSERT INTO game_requirement_groups (id,release_id,group_operator,mandatory,created_at,updated_at) VALUES (?,?,'all_of',1,?,?)",
            (group_id, ids["release"], NOW, NOW),
        )
        with pytest.raises(IntegrityError):
            connection.execute(
                "INSERT INTO game_hardware_requirements (id,group_id,hardware_model_id,accessory_model_id) VALUES (?,?,?,?)",
                (str(new_uuid7()), group_id, hardware_id, accessory_id),
            )
        connection.execute(
            "INSERT INTO game_hardware_requirements (id,group_id,capability_code,minimum_value) VALUES (?,?,'storage_gb',512)",
            (str(new_uuid7()), group_id),
        )


def test_current_playability_requires_complete_result(tmp_path: Path) -> None:
    _, database = migrated_database(tmp_path)
    with connect(database) as connection:
        connection.execute("PRAGMA foreign_keys=ON")
        ids = seed_release(connection)
        with pytest.raises(IntegrityError):
            connection.execute(
                "INSERT INTO personal_playability (release_id,state) VALUES (?,'current')",
                (ids["release"],),
            )
        connection.execute(
            "INSERT INTO personal_playability (release_id,playable_now,compatibility_level,missing_requirements_json,state,rule_version,input_version,calculated_at) VALUES (?,1,'full','[]','current','1','1',?)",
            (ids["release"], NOW),
        )


def test_downgrade_requires_empty_personal_hardware(tmp_path: Path) -> None:
    config, database = migrated_database(tmp_path)
    with connect(database) as connection:
        ids = seed_release(connection)
        hardware_id = str(new_uuid7())
        connection.execute(
            "INSERT INTO hardware_models (id,name,normalized_name,hardware_type,created_at,updated_at) VALUES (?,'Console','console','console',?,?)",
            (hardware_id, NOW, NOW),
        )
        connection.execute(
            "INSERT INTO personal_hardware_units (id,hardware_model_id,ownership_status,working_status,created_at,updated_at) VALUES (?,?,'owned','working',?,?)",
            (str(new_uuid7()), hardware_id, NOW, NOW),
        )
        assert ids["release"]
    with pytest.raises(RuntimeError):
        command.downgrade(config, "0006_personal_collection")

    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    empty_config, empty_database = migrated_database(empty_dir)
    command.downgrade(empty_config, "0006_personal_collection")
    assert (
        "hardware_models"
        not in inspect(create_engine(f"sqlite:///{empty_database}")).get_table_names()
    )

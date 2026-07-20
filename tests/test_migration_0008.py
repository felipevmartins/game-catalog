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
    database = tmp_path / "operations.db"
    config.set_main_option("sqlalchemy.url", f"sqlite:///{database}")
    command.upgrade(config, "0008_incremental_operations")
    return config, database


def seed_run(connection: object) -> str:
    run_id = str(new_uuid7())
    connection.execute(
        "INSERT INTO execution_runs (id,execution_type,status,requested_by,dry_run,application_version,schema_version,created_at) VALUES (?,'update','queued','cli',0,'0.1.0','0008_incremental_operations',?)",
        (run_id, NOW),
    )
    return run_id


def test_operations_schema_and_downgrade(tmp_path: Path) -> None:
    config, database = migrated_database(tmp_path)
    assert {"run_tasks", "review_queue", "change_log"} <= set(
        inspect(create_engine(f"sqlite:///{database}")).get_table_names()
    )
    command.downgrade(config, "0007_hardware_and_playability")
    assert "run_tasks" not in inspect(create_engine(f"sqlite:///{database}")).get_table_names()


def test_task_lock_terminal_and_active_deduplication(tmp_path: Path) -> None:
    _, database = migrated_database(tmp_path)
    with connect(database) as connection:
        run_id = seed_run(connection)
        insert = "INSERT INTO run_tasks (id,execution_run_id,task_type,priority,status,idempotency_policy,scheduled_for,deduplication_key,created_at,updated_at) VALUES (?,?,'collect','normal',?,'idempotent',?,'same',?,?)"
        connection.execute(insert, (str(new_uuid7()), run_id, "pending", NOW, NOW, NOW))
        with pytest.raises(IntegrityError):
            connection.execute(insert, (str(new_uuid7()), run_id, "pending", NOW, NOW, NOW))
        with pytest.raises(IntegrityError):
            connection.execute(insert, (str(new_uuid7()), run_id, "running", NOW, NOW, NOW))
        with pytest.raises(IntegrityError):
            connection.execute(insert, (str(new_uuid7()), run_id, "succeeded", NOW, NOW, NOW))


def test_review_deduplication_json_and_personal_entity_guard(tmp_path: Path) -> None:
    _, database = migrated_database(tmp_path)
    with connect(database) as connection:
        entity_id = str(new_uuid7())
        statement = "INSERT INTO review_queue (id,entity_type,entity_id,current_value_json,reason,priority,status,deduplication_key,created_at) VALUES (?,'game',?,'{}','conflict','high','pending','conflict-1',?)"
        connection.execute(statement, (str(new_uuid7()), entity_id, NOW))
        with pytest.raises(IntegrityError):
            connection.execute(statement, (str(new_uuid7()), entity_id, NOW))
        with pytest.raises(IntegrityError):
            connection.execute(
                "INSERT INTO review_queue (id,entity_type,entity_id,reason,priority,status,deduplication_key,created_at) VALUES (?,'personal_collection_item',?,'conflict','normal','pending','personal',?)",
                (str(new_uuid7()), entity_id, NOW),
            )
        with pytest.raises(IntegrityError):
            connection.execute(
                "INSERT INTO review_queue (id,entity_type,entity_id,reason,priority,status,deduplication_key,created_at) VALUES (?,'game',?,'done','normal','approved','done',?)",
                (str(new_uuid7()), entity_id, NOW),
            )


def test_change_log_requires_valid_json(tmp_path: Path) -> None:
    _, database = migrated_database(tmp_path)
    with connect(database) as connection:
        run_id = seed_run(connection)
        with pytest.raises(IntegrityError):
            connection.execute(
                "INSERT INTO change_log (id,execution_run_id,entity_type,entity_id,new_value_json,change_type,changed_at) VALUES (?,?, 'game',?,'invalid','update',?)",
                (str(new_uuid7()), run_id, str(new_uuid7()), NOW),
            )

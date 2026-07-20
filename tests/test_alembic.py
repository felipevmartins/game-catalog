from pathlib import Path
from sqlite3 import IntegrityError, connect

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text

from game_catalog.domain.identifiers import new_uuid7


def migrated_database(tmp_path: Path) -> tuple[Config, Path]:
    config = Config("alembic.ini")
    database = tmp_path / "migration.db"
    config.set_main_option("sqlalchemy.url", f"sqlite:///{database}")
    command.upgrade(config, "head")
    return config, database


def test_alembic_upgrade_head_on_real_sqlite_file(tmp_path: Path) -> None:
    _, database = migrated_database(tmp_path)
    engine = create_engine(f"sqlite:///{database}")
    inspector = inspect(engine)

    assert database.exists()
    assert {"alembic_version", "schema_metadata", "execution_runs", "backups"} <= set(
        inspector.get_table_names()
    )
    assert {index["name"] for index in inspector.get_indexes("execution_runs")} == {
        "ix_execution_runs_execution_type_created_at",
        "ix_execution_runs_status_created_at",
    }
    assert {index["name"] for index in inspector.get_indexes("backups")} == {
        "ix_backups_backup_type_created_at",
        "ix_backups_integrity_status_created_at",
        "ix_backups_related_run_id",
        "ix_backups_sha256",
    }
    with engine.connect() as connection:
        metadata = connection.execute(text("SELECT * FROM schema_metadata")).mappings().one()
        assert metadata["id"] == 1
        assert metadata["schema_version"] == "0008_incremental_operations"
        assert metadata["minimum_app_version"] == "0.1.0"
    engine.dispose()


def test_foundation_constraints_and_circular_relationship(tmp_path: Path) -> None:
    _, database = migrated_database(tmp_path)
    run_id = str(new_uuid7())
    backup_id = str(new_uuid7())
    timestamp = "2026-07-20T22:00:00.000Z"

    with connect(database) as connection:
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute(
            """INSERT INTO execution_runs
            (id, execution_type, status, requested_by, dry_run, application_version,
             schema_version, created_at)
            VALUES (?, 'backup', 'queued', 'system', 0, '0.1.0', '0001_foundation', ?)""",
            (run_id, timestamp),
        )
        connection.execute(
            """INSERT INTO backups
            (id, backup_type, file_name, file_path, size_bytes, sha256, schema_version,
             application_version, integrity_status, related_run_id, created_at, retained)
            VALUES (?, 'operational', 'catalog.db', 'private/catalog.db', 1024, ?,
                    '0001_foundation', '0.1.0', 'valid', ?, ?, 0)""",
            (backup_id, "a" * 64, run_id, timestamp),
        )
        connection.execute(
            "UPDATE execution_runs SET backup_id = ? WHERE id = ?", (backup_id, run_id)
        )

        with pytest.raises(IntegrityError):
            connection.execute("DELETE FROM backups WHERE id = ?", (backup_id,))


def test_foundation_rejects_invalid_state_and_backup_manifest(tmp_path: Path) -> None:
    _, database = migrated_database(tmp_path)
    timestamp = "2026-07-20T22:00:00.000Z"
    with connect(database) as connection:
        connection.execute("PRAGMA foreign_keys=ON")
        with pytest.raises(IntegrityError):
            connection.execute(
                """INSERT INTO execution_runs
                (id, execution_type, status, requested_by, dry_run, application_version,
                 schema_version, created_at)
                VALUES (?, 'backup', 'running', 'system', 0, '0.1.0', '0001_foundation', ?)""",
                (str(new_uuid7()), timestamp),
            )
        with pytest.raises(IntegrityError):
            connection.execute(
                """INSERT INTO backups
                (id, backup_type, file_name, file_path, size_bytes, sha256, schema_version,
                 application_version, integrity_status, created_at, retained)
                VALUES (?, 'daily', '../catalog.db', 'private/catalog.db', -1, 'invalid',
                        '0001_foundation', '0.1.0', 'valid', ?, 1)""",
                (str(new_uuid7()), timestamp),
            )


def test_foundation_downgrade_removes_its_tables_from_empty_database(tmp_path: Path) -> None:
    config, database = migrated_database(tmp_path)

    command.downgrade(config, "base")

    remaining = set(inspect(create_engine(f"sqlite:///{database}")).get_table_names())
    assert "schema_metadata" not in remaining
    assert "execution_runs" not in remaining
    assert "backups" not in remaining

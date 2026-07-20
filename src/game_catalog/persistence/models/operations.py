"""Operational models introduced by migration 0001."""

from __future__ import annotations

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from game_catalog.persistence.base import Base

UUID7_ID_CHECK = (
    "length(id) = 36 "
    "AND substr(id, 9, 1) = '-' "
    "AND substr(id, 14, 1) = '-' "
    "AND substr(id, 19, 1) = '-' "
    "AND substr(id, 24, 1) = '-' "
    "AND id = lower(id) "
    "AND replace(id, '-', '') NOT GLOB '*[^0-9a-f]*' "
    "AND substr(id, 15, 1) = '7' "
    "AND substr(id, 20, 1) IN ('8', '9', 'a', 'b')"
)


class SchemaMetadata(Base):
    """Singleton containing schema/application compatibility metadata."""

    __tablename__ = "schema_metadata"
    __table_args__ = (CheckConstraint("id = 1", name="singleton_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    schema_version: Mapped[str] = mapped_column(Text)
    minimum_app_version: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[str] = mapped_column(Text)


class ExecutionRun(Base):
    """Unified state machine for relevant operations."""

    __tablename__ = "execution_runs"
    __table_args__ = (
        CheckConstraint(UUID7_ID_CHECK, name="id_uuid7"),
        CheckConstraint(
            "execution_type IN ('import', 'update', 'recalculate', 'export', 'backup', "
            "'restore', 'migration', 'merge', 'maintenance', 'manual_edit')",
            name="execution_type",
        ),
        CheckConstraint(
            "status IN ('queued', 'running', 'succeeded', 'succeeded_with_warnings', "
            "'failed', 'cancelled')",
            name="status",
        ),
        CheckConstraint(
            "requested_by IN ('cli', 'scheduler', 'migration', 'system')",
            name="requested_by",
        ),
        CheckConstraint("dry_run IN (0, 1)", name="dry_run_boolean"),
        CheckConstraint(
            "parameters_json IS NULL OR json_valid(parameters_json)",
            name="parameters_json",
        ),
        CheckConstraint(
            "summary_json IS NULL OR json_valid(summary_json)",
            name="summary_json",
        ),
        CheckConstraint(
            "status <> 'running' OR "
            "(started_at IS NOT NULL AND heartbeat_at IS NOT NULL AND finished_at IS NULL)",
            name="running_timestamps",
        ),
        CheckConstraint(
            "status NOT IN ('succeeded', 'succeeded_with_warnings', 'failed', 'cancelled') "
            "OR finished_at IS NOT NULL",
            name="terminal_finished_at",
        ),
        CheckConstraint(
            "status NOT IN ('queued', 'running') OR finished_at IS NULL",
            name="active_without_finished_at",
        ),
        Index("ix_execution_runs_status_created_at", "status", "created_at"),
        Index("ix_execution_runs_execution_type_created_at", "execution_type", "created_at"),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    execution_type: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text)
    requested_by: Mapped[str] = mapped_column(Text)
    dry_run: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")
    parameters_json: Mapped[str | None] = mapped_column(Text)
    application_version: Mapped[str] = mapped_column(Text)
    schema_version: Mapped[str] = mapped_column(Text)
    started_at: Mapped[str | None] = mapped_column(Text)
    heartbeat_at: Mapped[str | None] = mapped_column(Text)
    finished_at: Mapped[str | None] = mapped_column(Text)
    backup_id: Mapped[str | None] = mapped_column(
        Text, ForeignKey("backups.id", ondelete="RESTRICT")
    )
    summary_json: Mapped[str | None] = mapped_column(Text)
    error_summary_redacted: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[str] = mapped_column(Text)


class Backup(Base):
    """Private manifest for a backup artifact."""

    __tablename__ = "backups"
    __table_args__ = (
        CheckConstraint(UUID7_ID_CHECK, name="id_uuid7"),
        CheckConstraint(
            "backup_type IN ('operational', 'daily', 'weekly', 'monthly', 'release', "
            "'audit_snapshot')",
            name="backup_type",
        ),
        CheckConstraint("size_bytes >= 0", name="size_bytes_nonnegative"),
        CheckConstraint(
            "length(sha256) = 64 AND sha256 NOT GLOB '*[^0-9A-Fa-f]*'",
            name="sha256",
        ),
        CheckConstraint(
            "integrity_status IN ('pending', 'valid', 'invalid')",
            name="integrity_status",
        ),
        CheckConstraint("retained IN (0, 1)", name="retained_boolean"),
        CheckConstraint(
            "retained = 0 OR retention_reason IS NOT NULL",
            name="retained_reason",
        ),
        CheckConstraint(
            "instr(file_name, '/') = 0 AND instr(file_name, char(92)) = 0",
            name="file_name_only",
        ),
        Index("ix_backups_sha256", "sha256"),
        Index("ix_backups_backup_type_created_at", "backup_type", "created_at"),
        Index("ix_backups_integrity_status_created_at", "integrity_status", "created_at"),
        Index("ix_backups_related_run_id", "related_run_id"),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    backup_type: Mapped[str] = mapped_column(Text)
    file_name: Mapped[str] = mapped_column(Text)
    file_path: Mapped[str] = mapped_column(Text)
    size_bytes: Mapped[int] = mapped_column(Integer)
    sha256: Mapped[str] = mapped_column(String(64))
    schema_version: Mapped[str] = mapped_column(Text)
    application_version: Mapped[str] = mapped_column(Text)
    integrity_status: Mapped[str] = mapped_column(Text)
    related_run_id: Mapped[str | None] = mapped_column(
        Text, ForeignKey("execution_runs.id", ondelete="RESTRICT")
    )
    created_at: Mapped[str] = mapped_column(Text)
    verified_at: Mapped[str | None] = mapped_column(Text)
    retained: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")
    retention_reason: Mapped[str | None] = mapped_column(Text)
    deleted_at: Mapped[str | None] = mapped_column(Text)
    restored_at: Mapped[str | None] = mapped_column(Text)

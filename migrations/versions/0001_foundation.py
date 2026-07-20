"""Create operational foundation tables.

Revision ID: 0001_foundation
Revises:
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_foundation"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

UUID7_CHECK = (
    "length({column}) = 36 "
    "AND substr({column}, 9, 1) = '-' "
    "AND substr({column}, 14, 1) = '-' "
    "AND substr({column}, 19, 1) = '-' "
    "AND substr({column}, 24, 1) = '-' "
    "AND {column} = lower({column}) "
    "AND replace({column}, '-', '') NOT GLOB '*[^0-9a-f]*' "
    "AND substr({column}, 15, 1) = '7' "
    "AND substr({column}, 20, 1) IN ('8', '9', 'a', 'b')"
)


def upgrade() -> None:
    op.create_table(
        "schema_metadata",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("schema_version", sa.Text(), nullable=False),
        sa.Column("minimum_app_version", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.Text(), nullable=False),
        sa.CheckConstraint("id = 1", name="ck_schema_metadata_singleton_id"),
        sa.PrimaryKeyConstraint("id", name="pk_schema_metadata"),
    )

    op.create_table(
        "execution_runs",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("execution_type", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("requested_by", sa.Text(), nullable=False),
        sa.Column("dry_run", sa.Boolean(), server_default="0", nullable=False),
        sa.Column("parameters_json", sa.Text(), nullable=True),
        sa.Column("application_version", sa.Text(), nullable=False),
        sa.Column("schema_version", sa.Text(), nullable=False),
        sa.Column("started_at", sa.Text(), nullable=True),
        sa.Column("heartbeat_at", sa.Text(), nullable=True),
        sa.Column("finished_at", sa.Text(), nullable=True),
        sa.Column("backup_id", sa.Text(), nullable=True),
        sa.Column("summary_json", sa.Text(), nullable=True),
        sa.Column("error_summary_redacted", sa.Text(), nullable=True),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.CheckConstraint(UUID7_CHECK.format(column="id"), name="ck_execution_runs_id_uuid7"),
        sa.CheckConstraint(
            "execution_type IN ('import', 'update', 'recalculate', 'export', 'backup', "
            "'restore', 'migration', 'merge', 'maintenance', 'manual_edit')",
            name="ck_execution_runs_execution_type",
        ),
        sa.CheckConstraint(
            "status IN ('queued', 'running', 'succeeded', 'succeeded_with_warnings', "
            "'failed', 'cancelled')",
            name="ck_execution_runs_status",
        ),
        sa.CheckConstraint(
            "requested_by IN ('cli', 'scheduler', 'migration', 'system')",
            name="ck_execution_runs_requested_by",
        ),
        sa.CheckConstraint("dry_run IN (0, 1)", name="ck_execution_runs_dry_run_boolean"),
        sa.CheckConstraint(
            "parameters_json IS NULL OR json_valid(parameters_json)",
            name="ck_execution_runs_parameters_json",
        ),
        sa.CheckConstraint(
            "summary_json IS NULL OR json_valid(summary_json)",
            name="ck_execution_runs_summary_json",
        ),
        sa.CheckConstraint(
            "status <> 'running' OR "
            "(started_at IS NOT NULL AND heartbeat_at IS NOT NULL AND finished_at IS NULL)",
            name="ck_execution_runs_running_timestamps",
        ),
        sa.CheckConstraint(
            "status NOT IN ('succeeded', 'succeeded_with_warnings', 'failed', 'cancelled') "
            "OR finished_at IS NOT NULL",
            name="ck_execution_runs_terminal_finished_at",
        ),
        sa.CheckConstraint(
            "status NOT IN ('queued', 'running') OR finished_at IS NULL",
            name="ck_execution_runs_active_without_finished_at",
        ),
        sa.ForeignKeyConstraint(
            ["backup_id"],
            ["backups.id"],
            name="fk_execution_runs_backup_id_backups",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_execution_runs"),
    )
    op.create_index(
        "ix_execution_runs_status_created_at", "execution_runs", ["status", "created_at"]
    )
    op.create_index(
        "ix_execution_runs_execution_type_created_at",
        "execution_runs",
        ["execution_type", "created_at"],
    )

    op.create_table(
        "backups",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("backup_type", sa.Text(), nullable=False),
        sa.Column("file_name", sa.Text(), nullable=False),
        sa.Column("file_path", sa.Text(), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("schema_version", sa.Text(), nullable=False),
        sa.Column("application_version", sa.Text(), nullable=False),
        sa.Column("integrity_status", sa.Text(), nullable=False),
        sa.Column("related_run_id", sa.Text(), nullable=True),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.Column("verified_at", sa.Text(), nullable=True),
        sa.Column("retained", sa.Boolean(), server_default="0", nullable=False),
        sa.Column("retention_reason", sa.Text(), nullable=True),
        sa.Column("deleted_at", sa.Text(), nullable=True),
        sa.Column("restored_at", sa.Text(), nullable=True),
        sa.CheckConstraint(UUID7_CHECK.format(column="id"), name="ck_backups_id_uuid7"),
        sa.CheckConstraint(
            "backup_type IN ('operational', 'daily', 'weekly', 'monthly', 'release', "
            "'audit_snapshot')",
            name="ck_backups_backup_type",
        ),
        sa.CheckConstraint("size_bytes >= 0", name="ck_backups_size_bytes_nonnegative"),
        sa.CheckConstraint(
            "length(sha256) = 64 AND sha256 NOT GLOB '*[^0-9A-Fa-f]*'",
            name="ck_backups_sha256",
        ),
        sa.CheckConstraint(
            "integrity_status IN ('pending', 'valid', 'invalid')",
            name="ck_backups_integrity_status",
        ),
        sa.CheckConstraint("retained IN (0, 1)", name="ck_backups_retained_boolean"),
        sa.CheckConstraint(
            "retained = 0 OR retention_reason IS NOT NULL",
            name="ck_backups_retained_reason",
        ),
        sa.CheckConstraint(
            "instr(file_name, '/') = 0 AND instr(file_name, char(92)) = 0",
            name="ck_backups_file_name_only",
        ),
        sa.ForeignKeyConstraint(
            ["related_run_id"],
            ["execution_runs.id"],
            name="fk_backups_related_run_id_execution_runs",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_backups"),
    )
    op.create_index("ix_backups_sha256", "backups", ["sha256"])
    op.create_index("ix_backups_backup_type_created_at", "backups", ["backup_type", "created_at"])
    op.create_index(
        "ix_backups_integrity_status_created_at",
        "backups",
        ["integrity_status", "created_at"],
    )
    op.create_index("ix_backups_related_run_id", "backups", ["related_run_id"])

    op.execute(
        sa.text(
            "INSERT INTO schema_metadata "
            "(id, schema_version, minimum_app_version, updated_at) "
            "VALUES (1, '0001_foundation', '0.1.0', "
            "strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))"
        )
    )


def downgrade() -> None:
    op.drop_index("ix_backups_related_run_id", table_name="backups")
    op.drop_index("ix_backups_integrity_status_created_at", table_name="backups")
    op.drop_index("ix_backups_backup_type_created_at", table_name="backups")
    op.drop_index("ix_backups_sha256", table_name="backups")
    op.drop_index("ix_execution_runs_execution_type_created_at", table_name="execution_runs")
    op.drop_index("ix_execution_runs_status_created_at", table_name="execution_runs")
    op.drop_table("backups")
    op.drop_table("execution_runs")
    op.drop_table("schema_metadata")

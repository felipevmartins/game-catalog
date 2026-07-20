"""Create incremental task queue, review queue and change log.

Revision ID: 0008_incremental_operations
Revises: 0007_hardware_and_playability
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0008_incremental_operations"
down_revision: str | None = "0007_hardware_and_playability"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def uuid7(column: str = "id") -> str:
    return (
        f"length({column})=36 AND substr({column},9,1)='-' "
        f"AND substr({column},14,1)='-' AND substr({column},19,1)='-' "
        f"AND substr({column},24,1)='-' AND {column}=lower({column}) "
        f"AND replace({column},'-','') NOT GLOB '*[^0-9a-f]*' "
        f"AND substr({column},15,1)='7' AND substr({column},20,1) IN ('8','9','a','b')"
    )


def upgrade() -> None:
    op.create_table(
        "run_tasks",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column(
            "execution_run_id",
            sa.Text(),
            sa.ForeignKey("execution_runs.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("task_type", sa.Text(), nullable=False),
        sa.Column("entity_type", sa.Text()),
        sa.Column("entity_id", sa.Text()),
        sa.Column("source_id", sa.Text(), sa.ForeignKey("sources.id", ondelete="RESTRICT")),
        sa.Column("priority", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("idempotency_policy", sa.Text(), nullable=False),
        sa.Column("scheduled_for", sa.Text(), nullable=False),
        sa.Column("attempt_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("max_attempts", sa.Integer(), server_default="3", nullable=False),
        sa.Column("deduplication_key", sa.Text(), nullable=False),
        sa.Column("lock_owner", sa.Text()),
        sa.Column("lock_token", sa.Text()),
        sa.Column("locked_at", sa.Text()),
        sa.Column("lock_expires_at", sa.Text()),
        sa.Column("last_error_redacted", sa.Text()),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.Text(), nullable=False),
        sa.Column("finished_at", sa.Text()),
        sa.CheckConstraint(uuid7(), name="ck_run_tasks_id_uuid7"),
        sa.CheckConstraint(
            "entity_id IS NULL OR " + uuid7("entity_id"), name="ck_run_tasks_entity_id_uuid7"
        ),
        sa.CheckConstraint(
            "lock_token IS NULL OR " + uuid7("lock_token"), name="ck_run_tasks_lock_token_uuid7"
        ),
        sa.CheckConstraint(
            "task_type IN ('collect','normalize','apply','recalculate_lock','recalculate_playability','verify','other')",
            name="ck_run_tasks_type",
        ),
        sa.CheckConstraint(
            "priority IN ('critical','high','normal','low')", name="ck_run_tasks_priority"
        ),
        sa.CheckConstraint(
            "status IN ('pending','running','succeeded','failed','dead_letter','cancelled')",
            name="ck_run_tasks_status",
        ),
        sa.CheckConstraint(
            "idempotency_policy IN ('idempotent','review_required')",
            name="ck_run_tasks_idempotency",
        ),
        sa.CheckConstraint("attempt_count>=0 AND max_attempts>0", name="ck_run_tasks_attempts"),
        sa.CheckConstraint(
            "status='running' OR lock_token IS NULL", name="ck_run_tasks_nonrunning_lock"
        ),
        sa.CheckConstraint(
            "status<>'running' OR (lock_owner IS NOT NULL AND lock_token IS NOT NULL AND locked_at IS NOT NULL AND lock_expires_at IS NOT NULL AND finished_at IS NULL)",
            name="ck_run_tasks_running_lock",
        ),
        sa.CheckConstraint(
            "status NOT IN ('succeeded','failed','dead_letter','cancelled') OR finished_at IS NOT NULL",
            name="ck_run_tasks_terminal_finished",
        ),
        sa.CheckConstraint(
            "status IN ('succeeded','failed','dead_letter','cancelled') OR finished_at IS NULL",
            name="ck_run_tasks_active_unfinished",
        ),
    )
    op.create_index(
        "uq_run_tasks_active_deduplication",
        "run_tasks",
        ["deduplication_key"],
        unique=True,
        sqlite_where=sa.text("status IN ('pending','running')"),
    )
    op.create_index("ix_run_tasks_status_scheduled", "run_tasks", ["status", "scheduled_for"])
    op.create_index("ix_run_tasks_status_lock_expires", "run_tasks", ["status", "lock_expires_at"])
    op.create_index("ix_run_tasks_execution_run_id", "run_tasks", ["execution_run_id"])
    op.create_index("ix_run_tasks_entity", "run_tasks", ["entity_type", "entity_id"])

    op.create_table(
        "review_queue",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("entity_type", sa.Text(), nullable=False),
        sa.Column("entity_id", sa.Text(), nullable=False),
        sa.Column("field_name", sa.Text()),
        sa.Column("current_value_json", sa.Text()),
        sa.Column("candidate_value_json", sa.Text()),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column(
            "source_reference_id",
            sa.Text(),
            sa.ForeignKey("source_references.id", ondelete="RESTRICT"),
        ),
        sa.Column("priority", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("deduplication_key", sa.Text(), nullable=False),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.Column("reviewed_at", sa.Text()),
        sa.Column("reviewed_by", sa.Text()),
        sa.Column("review_notes", sa.Text()),
        sa.CheckConstraint(uuid7(), name="ck_review_queue_id_uuid7"),
        sa.CheckConstraint(uuid7("entity_id"), name="ck_review_queue_entity_id_uuid7"),
        sa.CheckConstraint(
            "entity_type IN ('game','game_edition','release','product','game_content','franchise','company','platform','manufacturer','ecosystem','region','hardware_model','accessory_model','source','external_id','execution_run')",
            name="ck_review_queue_entity_type",
        ),
        sa.CheckConstraint(
            "current_value_json IS NULL OR json_valid(current_value_json)",
            name="ck_review_queue_current_json",
        ),
        sa.CheckConstraint(
            "candidate_value_json IS NULL OR json_valid(candidate_value_json)",
            name="ck_review_queue_candidate_json",
        ),
        sa.CheckConstraint(
            "priority IN ('critical','high','normal','low')", name="ck_review_queue_priority"
        ),
        sa.CheckConstraint(
            "status IN ('pending','approved','rejected','deferred','cancelled')",
            name="ck_review_queue_status",
        ),
        sa.CheckConstraint(
            "status='pending' OR reviewed_at IS NOT NULL", name="ck_review_queue_reviewed_at"
        ),
    )
    op.create_index(
        "uq_review_queue_active_deduplication",
        "review_queue",
        ["deduplication_key"],
        unique=True,
        sqlite_where=sa.text("status IN ('pending','deferred')"),
    )
    op.create_index(
        "ix_review_queue_status_priority_created",
        "review_queue",
        ["status", "priority", "created_at"],
    )
    op.create_index("ix_review_queue_entity", "review_queue", ["entity_type", "entity_id"])
    op.create_index("ix_review_queue_source_reference_id", "review_queue", ["source_reference_id"])

    op.create_table(
        "change_log",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column(
            "execution_run_id",
            sa.Text(),
            sa.ForeignKey("execution_runs.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("entity_type", sa.Text(), nullable=False),
        sa.Column("entity_id", sa.Text(), nullable=False),
        sa.Column("field_name", sa.Text()),
        sa.Column("old_value_json", sa.Text()),
        sa.Column("new_value_json", sa.Text()),
        sa.Column("change_type", sa.Text(), nullable=False),
        sa.Column(
            "source_reference_id",
            sa.Text(),
            sa.ForeignKey("source_references.id", ondelete="RESTRICT"),
        ),
        sa.Column("changed_at", sa.Text(), nullable=False),
        sa.Column("notes", sa.Text()),
        sa.CheckConstraint(uuid7(), name="ck_change_log_id_uuid7"),
        sa.CheckConstraint(uuid7("entity_id"), name="ck_change_log_entity_id_uuid7"),
        sa.CheckConstraint(
            "old_value_json IS NULL OR json_valid(old_value_json)", name="ck_change_log_old_json"
        ),
        sa.CheckConstraint(
            "new_value_json IS NULL OR json_valid(new_value_json)", name="ck_change_log_new_json"
        ),
        sa.CheckConstraint(
            "change_type IN ('insert','update','soft_delete','merge','recalculate')",
            name="ck_change_log_type",
        ),
    )
    op.create_index("ix_change_log_execution_run_id", "change_log", ["execution_run_id"])
    op.create_index("ix_change_log_entity", "change_log", ["entity_type", "entity_id"])
    op.create_index("ix_change_log_changed_at", "change_log", ["changed_at"])
    op.execute(
        "UPDATE schema_metadata SET schema_version='0008_incremental_operations', updated_at=strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id=1"
    )


def downgrade() -> None:
    for table in ("change_log", "review_queue", "run_tasks"):
        op.drop_table(table)
    op.execute(
        "UPDATE schema_metadata SET schema_version='0007_hardware_and_playability', updated_at=strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id=1"
    )

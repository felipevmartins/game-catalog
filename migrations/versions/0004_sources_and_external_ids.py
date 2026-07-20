"""Create provenance and external identifier tables.

Revision ID: 0004_sources_and_external_ids
Revises: 0003_game_identity
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004_sources_and_external_ids"
down_revision: str | None = "0003_game_identity"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

EXTERNAL_ENTITIES = (
    ("game", "games"),
    ("edition", "game_editions"),
    ("release", "releases"),
    ("platform", "platforms"),
    ("company", "companies"),
    ("franchise", "franchises"),
    ("product", "products"),
)


def uuid7(column: str = "id") -> str:
    return (
        f"length({column})=36 AND substr({column},9,1)='-' "
        f"AND substr({column},14,1)='-' AND substr({column},19,1)='-' "
        f"AND substr({column},24,1)='-' AND {column}=lower({column}) "
        f"AND replace({column},'-','') NOT GLOB '*[^0-9a-f]*' "
        f"AND substr({column},15,1)='7' "
        f"AND substr({column},20,1) IN ('8','9','a','b')"
    )


def upgrade() -> None:
    op.create_table(
        "sources",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("code", sa.Text(), nullable=False, unique=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("source_type", sa.Text(), nullable=False),
        sa.Column("integration_type", sa.Text(), nullable=False),
        sa.Column("base_url", sa.Text()),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("default_confidence", sa.Text(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("credential_required", sa.Boolean(), nullable=False),
        sa.Column("terms_url", sa.Text()),
        sa.Column("terms_reviewed_at", sa.Text()),
        sa.Column("contract_version", sa.Text()),
        sa.Column("license_name", sa.Text()),
        sa.Column("attribution_text", sa.Text()),
        sa.Column("redistribution_policy", sa.Text(), nullable=False),
        sa.Column("default_ttl_days", sa.Integer()),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.Text(), nullable=False),
        sa.CheckConstraint(uuid7(), name="ck_sources_id_uuid7"),
        sa.CheckConstraint(
            "source_type IN ('official','store','database','collaborative',"
            "'review_aggregator','duration_aggregator','archive','press','community',"
            "'manual','other')",
            name="ck_sources_source_type",
        ),
        sa.CheckConstraint("priority BETWEEN 0 AND 100", name="ck_sources_priority"),
        sa.CheckConstraint(
            "enabled IN (0,1) AND credential_required IN (0,1)", name="ck_sources_booleans"
        ),
        sa.CheckConstraint(
            "default_ttl_days IS NULL OR default_ttl_days >= 0", name="ck_sources_ttl"
        ),
        sa.CheckConstraint(
            "default_confidence IN ('high','medium','low')", name="ck_sources_confidence"
        ),
        sa.CheckConstraint(
            "integration_type IN ('api','sparql','manual','file','permitted_http','none')",
            name="ck_sources_integration_type",
        ),
        sa.CheckConstraint(
            "redistribution_policy IN "
            "('allowed','attribution_required','restricted','prohibited','unknown')",
            name="ck_sources_redistribution",
        ),
    )
    op.create_table(
        "source_references",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column(
            "source_id", sa.Text(), sa.ForeignKey("sources.id", ondelete="RESTRICT"), nullable=False
        ),
        sa.Column("source_record_id", sa.Text()),
        sa.Column("source_url", sa.Text()),
        sa.Column("retrieved_at", sa.Text(), nullable=False),
        sa.Column("verified_at", sa.Text()),
        sa.Column("valid_until", sa.Text()),
        sa.Column("content_hash", sa.Text()),
        sa.Column("source_contract_version", sa.Text()),
        sa.Column("notes", sa.Text()),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.CheckConstraint(uuid7(), name="ck_source_references_id_uuid7"),
        sa.CheckConstraint(
            "source_record_id IS NOT NULL OR source_url IS NOT NULL",
            name="ck_source_references_locator",
        ),
    )
    op.create_index("ix_source_references_source_id", "source_references", ["source_id"])
    op.create_index("ix_source_references_valid_until", "source_references", ["valid_until"])
    op.create_index("ix_source_references_verified_at", "source_references", ["verified_at"])
    op.create_index(
        "uq_source_references_record_hash",
        "source_references",
        ["source_id", "source_record_id", sa.text("COALESCE(content_hash,'')")],
        unique=True,
        sqlite_where=sa.text("source_record_id IS NOT NULL"),
    )

    op.create_table(
        "record_source_links",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("entity_type", sa.Text(), nullable=False),
        sa.Column("entity_id", sa.Text(), nullable=False),
        sa.Column(
            "source_reference_id",
            sa.Text(),
            sa.ForeignKey("source_references.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("link_role", sa.Text(), nullable=False),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.CheckConstraint(uuid7(), name="ck_record_source_links_id_uuid7"),
        sa.CheckConstraint(uuid7("entity_id"), name="ck_record_source_links_entity_id_uuid7"),
        sa.CheckConstraint(
            "link_role IN ('primary','supporting','historical')", name="ck_record_source_links_role"
        ),
        sa.UniqueConstraint(
            "entity_type",
            "entity_id",
            "source_reference_id",
            "link_role",
            name="uq_record_source_links_identity",
        ),
    )
    op.create_index(
        "ix_record_source_links_entity", "record_source_links", ["entity_type", "entity_id"]
    )
    op.create_index(
        "ix_record_source_links_source_reference_id", "record_source_links", ["source_reference_id"]
    )
    op.create_index(
        "uq_record_source_links_primary",
        "record_source_links",
        ["entity_type", "entity_id"],
        unique=True,
        sqlite_where=sa.text("link_role='primary'"),
    )

    op.create_table(
        "catalog_assertions",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("entity_type", sa.Text(), nullable=False),
        sa.Column("entity_id", sa.Text(), nullable=False),
        sa.Column("field_name", sa.Text(), nullable=False),
        sa.Column("value_json", sa.Text(), nullable=False),
        sa.Column("raw_value_json", sa.Text()),
        sa.Column(
            "source_reference_id",
            sa.Text(),
            sa.ForeignKey("source_references.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("confidence", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("is_manual_override", sa.Boolean(), server_default="0", nullable=False),
        sa.Column("observed_at", sa.Text(), nullable=False),
        sa.Column("last_verified_at", sa.Text()),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.Text(), nullable=False),
        sa.CheckConstraint(uuid7(), name="ck_catalog_assertions_id_uuid7"),
        sa.CheckConstraint(uuid7("entity_id"), name="ck_catalog_assertions_entity_id_uuid7"),
        sa.CheckConstraint(
            "json_valid(value_json) AND (raw_value_json IS NULL OR json_valid(raw_value_json))",
            name="ck_catalog_assertions_json",
        ),
        sa.CheckConstraint(
            "confidence IN ('high','medium','low')", name="ck_catalog_assertions_confidence"
        ),
        sa.CheckConstraint(
            "status IN ('candidate','accepted','rejected','superseded','conflict')",
            name="ck_catalog_assertions_status",
        ),
        sa.CheckConstraint(
            "is_manual_override IN (0,1) AND (is_manual_override=0 OR status='accepted')",
            name="ck_catalog_assertions_manual",
        ),
        sa.UniqueConstraint(
            "entity_type",
            "entity_id",
            "field_name",
            "source_reference_id",
            "value_json",
            name="uq_catalog_assertions_identity",
        ),
    )
    op.create_index(
        "ix_catalog_assertions_lookup",
        "catalog_assertions",
        ["entity_type", "entity_id", "field_name", "status"],
    )
    op.create_index(
        "ix_catalog_assertions_source_reference_id", "catalog_assertions", ["source_reference_id"]
    )
    op.create_index(
        "ix_catalog_assertions_last_verified_at", "catalog_assertions", ["last_verified_at"]
    )
    op.create_index(
        "uq_catalog_assertions_accepted",
        "catalog_assertions",
        ["entity_type", "entity_id", "field_name"],
        unique=True,
        sqlite_where=sa.text("status='accepted'"),
    )

    with op.batch_alter_table("game_aliases") as batch:
        batch.create_foreign_key(
            "fk_game_aliases_source_reference_id_source_references",
            "source_references",
            ["source_reference_id"],
            ["id"],
            ondelete="RESTRICT",
        )

    for prefix, parent_table in EXTERNAL_ENTITIES:
        table = f"{prefix}_external_ids"
        parent_column = f"{prefix}_id"
        op.create_table(
            table,
            sa.Column("id", sa.Text(), primary_key=True),
            sa.Column(
                parent_column,
                sa.Text(),
                sa.ForeignKey(f"{parent_table}.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column(
                "source_id",
                sa.Text(),
                sa.ForeignKey("sources.id", ondelete="RESTRICT"),
                nullable=False,
            ),
            sa.Column("external_id", sa.Text(), nullable=False),
            sa.Column("context", sa.Text(), server_default="global", nullable=False),
            sa.Column("is_primary", sa.Boolean(), server_default="0", nullable=False),
            sa.Column("created_at", sa.Text(), nullable=False),
            sa.Column("updated_at", sa.Text(), nullable=False),
            sa.CheckConstraint(uuid7(), name=f"ck_{table}_id_uuid7"),
            sa.CheckConstraint("length(trim(external_id)) > 0", name=f"ck_{table}_external_id"),
            sa.CheckConstraint("length(trim(context)) > 0", name=f"ck_{table}_context"),
            sa.CheckConstraint("is_primary IN (0,1)", name=f"ck_{table}_is_primary"),
            sa.UniqueConstraint(
                "source_id", "external_id", "context", name=f"uq_{table}_source_external_context"
            ),
        )
        op.create_index(f"ix_{table}_{parent_column}", table, [parent_column])
        op.create_index(
            f"ix_{table}_source_external_context", table, ["source_id", "external_id", "context"]
        )
        op.create_index(
            f"uq_{table}_primary",
            table,
            [parent_column, "source_id", "context"],
            unique=True,
            sqlite_where=sa.text("is_primary=1"),
        )
    op.execute(
        "UPDATE schema_metadata SET schema_version='0004_sources_and_external_ids', "
        "updated_at=strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id=1"
    )


def downgrade() -> None:
    for prefix, _ in reversed(EXTERNAL_ENTITIES):
        op.drop_table(f"{prefix}_external_ids")
    with op.batch_alter_table("game_aliases") as batch:
        batch.drop_constraint(
            "fk_game_aliases_source_reference_id_source_references", type_="foreignkey"
        )
    op.drop_table("catalog_assertions")
    op.drop_table("record_source_links")
    op.drop_table("source_references")
    op.drop_table("sources")
    op.execute(
        "UPDATE schema_metadata SET schema_version='0003_game_identity', "
        "updated_at=strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id=1"
    )

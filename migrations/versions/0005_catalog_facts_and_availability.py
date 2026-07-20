"""Create catalog facts, availability history and platform lock state.

Revision ID: 0005_catalog_facts_and_availability
Revises: 0004_sources_and_external_ids
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005_catalog_facts_and_availability"
down_revision: str | None = "0004_sources_and_external_ids"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def uuid7(column: str = "id") -> str:
    return (
        f"length({column})=36 AND substr({column},9,1)='-' "
        f"AND substr({column},14,1)='-' AND substr({column},19,1)='-' "
        f"AND substr({column},24,1)='-' AND {column}=lower({column}) "
        f"AND replace({column},'-','') NOT GLOB '*[^0-9a-f]*' "
        f"AND substr({column},15,1)='7' "
        f"AND substr({column},20,1) IN ('8','9','a','b')"
    )


def partial_date(prefix: str) -> str:
    y, m, d, p, q = (
        f"{prefix}_{suffix}" for suffix in ("year", "month", "day", "precision", "qualifier")
    )
    return (
        f"({p}='unknown' AND {y} IS NULL AND {m} IS NULL AND {d} IS NULL AND {q} IS NULL) OR "
        f"({p}='year' AND {y} IS NOT NULL AND {m} IS NULL AND {d} IS NULL) OR "
        f"({p}='month' AND {y} IS NOT NULL AND {m} IS NOT NULL AND {m} BETWEEN 1 AND 12 AND {d} IS NULL) OR "
        f"({p}='day' AND {y} IS NOT NULL AND {m} IS NOT NULL AND {m} BETWEEN 1 AND 12 AND {d} BETWEEN 1 AND 31)"
    )


def upgrade() -> None:
    op.create_table(
        "franchise_ownerships",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column(
            "franchise_id",
            sa.Text(),
            sa.ForeignKey("franchises.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "owner_company_id",
            sa.Text(),
            sa.ForeignKey("companies.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("ownership_type", sa.Text(), nullable=False),
        sa.Column("is_current", sa.Boolean(), server_default="0", nullable=False),
        *[
            sa.Column(
                f"valid_{side}_{part}",
                sa.Integer() if part in ("year", "month", "day") else sa.Text(),
                nullable=False if part == "precision" else True,
            )
            for side in ("from", "to")
            for part in ("year", "month", "day", "precision", "qualifier")
        ],
        sa.Column(
            "source_reference_id",
            sa.Text(),
            sa.ForeignKey("source_references.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("notes", sa.Text()),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.Text(), nullable=False),
        sa.CheckConstraint(uuid7(), name="ck_franchise_ownerships_id_uuid7"),
        sa.CheckConstraint(
            "ownership_type IN ('ip_owner','license_holder','other')",
            name="ck_franchise_ownerships_type",
        ),
        sa.CheckConstraint("is_current IN (0,1)", name="ck_franchise_ownerships_current"),
        sa.CheckConstraint(partial_date("valid_from"), name="ck_franchise_ownerships_valid_from"),
        sa.CheckConstraint(partial_date("valid_to"), name="ck_franchise_ownerships_valid_to"),
        sa.CheckConstraint(
            "is_current=0 OR valid_to_precision='unknown'",
            name="ck_franchise_ownerships_current_open",
        ),
        sa.UniqueConstraint(
            "franchise_id",
            "owner_company_id",
            "ownership_type",
            "source_reference_id",
            name="uq_franchise_ownerships_identity",
        ),
    )
    for column in ("franchise_id", "owner_company_id", "ownership_type", "is_current"):
        op.create_index(f"ix_franchise_ownerships_{column}", "franchise_ownerships", [column])
    op.create_index(
        "uq_franchise_ownerships_current_ip_owner",
        "franchise_ownerships",
        ["franchise_id"],
        unique=True,
        sqlite_where=sa.text("ownership_type='ip_owner' AND is_current=1"),
    )

    op.create_table(
        "game_companies",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column(
            "game_id", sa.Text(), sa.ForeignKey("games.id", ondelete="RESTRICT"), nullable=False
        ),
        sa.Column("edition_id", sa.Text(), sa.ForeignKey("game_editions.id", ondelete="RESTRICT")),
        sa.Column("release_id", sa.Text(), sa.ForeignKey("releases.id", ondelete="RESTRICT")),
        sa.Column(
            "company_id",
            sa.Text(),
            sa.ForeignKey("companies.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("role", sa.Text(), nullable=False),
        sa.Column(
            "source_reference_id",
            sa.Text(),
            sa.ForeignKey("source_references.id", ondelete="RESTRICT"),
        ),
        sa.Column("notes", sa.Text()),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.CheckConstraint(uuid7(), name="ck_game_companies_id_uuid7"),
        sa.CheckConstraint(
            "release_id IS NULL OR edition_id IS NOT NULL",
            name="ck_game_companies_release_requires_edition",
        ),
        sa.CheckConstraint(
            "role IN ('developer','publisher','original_publisher','port_developer','support_studio','distributor','current_ip_owner','other')",
            name="ck_game_companies_role",
        ),
    )
    for column in ("game_id", "edition_id", "release_id", "company_id"):
        op.create_index(f"ix_game_companies_{column}", "game_companies", [column])
    op.create_index(
        "uq_game_companies_identity",
        "game_companies",
        [
            "game_id",
            sa.text("COALESCE(edition_id,'')"),
            sa.text("COALESCE(release_id,'')"),
            "company_id",
            "role",
        ],
        unique=True,
    )

    op.create_table(
        "game_scores",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column(
            "release_id",
            sa.Text(),
            sa.ForeignKey("releases.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "source_id", sa.Text(), sa.ForeignKey("sources.id", ondelete="RESTRICT"), nullable=False
        ),
        sa.Column("score_value", sa.Numeric()),
        sa.Column("review_count", sa.Integer()),
        sa.Column(
            "source_reference_id",
            sa.Text(),
            sa.ForeignKey("source_references.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("retrieved_at", sa.Text(), nullable=False),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.Text(), nullable=False),
        sa.CheckConstraint(uuid7(), name="ck_game_scores_id_uuid7"),
        sa.CheckConstraint(
            "score_value IS NULL OR score_value BETWEEN 0 AND 100", name="ck_game_scores_value"
        ),
        sa.CheckConstraint(
            "review_count IS NULL OR review_count >= 0", name="ck_game_scores_reviews"
        ),
        sa.UniqueConstraint("release_id", "source_id", name="uq_game_scores_release_source"),
    )
    op.create_index("ix_game_scores_release_id", "game_scores", ["release_id"])
    op.create_index("ix_game_scores_source_id", "game_scores", ["source_id"])
    op.create_table(
        "game_primary_scores",
        sa.Column(
            "game_id", sa.Text(), sa.ForeignKey("games.id", ondelete="CASCADE"), primary_key=True
        ),
        sa.Column(
            "score_id",
            sa.Text(),
            sa.ForeignKey("game_scores.id", ondelete="RESTRICT"),
            nullable=False,
            unique=True,
        ),
        sa.Column("selection_reason", sa.Text(), nullable=False),
        sa.Column("selected_at", sa.Text(), nullable=False),
        sa.Column(
            "source_reference_id",
            sa.Text(),
            sa.ForeignKey("source_references.id", ondelete="RESTRICT"),
        ),
    )
    op.create_index("ix_game_primary_scores_score_id", "game_primary_scores", ["score_id"])

    op.create_table(
        "game_lengths",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column(
            "game_id", sa.Text(), sa.ForeignKey("games.id", ondelete="RESTRICT"), nullable=False
        ),
        sa.Column(
            "source_id", sa.Text(), sa.ForeignKey("sources.id", ondelete="RESTRICT"), nullable=False
        ),
        sa.Column("main_story_minutes", sa.Integer()),
        sa.Column("main_extra_minutes", sa.Integer()),
        sa.Column("completionist_minutes", sa.Integer()),
        sa.Column("not_applicable", sa.Boolean(), server_default="0", nullable=False),
        sa.Column(
            "source_reference_id",
            sa.Text(),
            sa.ForeignKey("source_references.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("retrieved_at", sa.Text(), nullable=False),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.Text(), nullable=False),
        sa.CheckConstraint(uuid7(), name="ck_game_lengths_id_uuid7"),
        sa.CheckConstraint(
            "(main_story_minutes IS NULL OR main_story_minutes>=0) AND (main_extra_minutes IS NULL OR main_extra_minutes>=0) AND (completionist_minutes IS NULL OR completionist_minutes>=0)",
            name="ck_game_lengths_nonnegative",
        ),
        sa.CheckConstraint(
            "not_applicable IN (0,1) AND (not_applicable=0 OR (main_story_minutes IS NULL AND main_extra_minutes IS NULL AND completionist_minutes IS NULL))",
            name="ck_game_lengths_not_applicable",
        ),
        sa.UniqueConstraint("game_id", "source_id", name="uq_game_lengths_game_source"),
    )
    op.create_index("ix_game_lengths_game_id", "game_lengths", ["game_id"])
    op.create_index("ix_game_lengths_source_id", "game_lengths", ["source_id"])

    op.create_table(
        "availability_offers",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column(
            "release_id",
            sa.Text(),
            sa.ForeignKey("releases.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "access_platform_id",
            sa.Text(),
            sa.ForeignKey("platforms.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "provider_company_id", sa.Text(), sa.ForeignKey("companies.id", ondelete="RESTRICT")
        ),
        sa.Column("availability_type", sa.Text(), nullable=False),
        sa.Column(
            "region_id", sa.Text(), sa.ForeignKey("regions.id", ondelete="RESTRICT"), nullable=False
        ),
        sa.Column("offer_identity_key", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("is_current", sa.Boolean(), server_default="1", nullable=False),
        *[
            sa.Column(
                f"valid_{side}_{part}",
                sa.Integer() if part in ("year", "month", "day") else sa.Text(),
                nullable=False if part == "precision" else True,
            )
            for side in ("from", "to")
            for part in ("year", "month", "day", "precision", "qualifier")
        ],
        sa.Column("observed_at", sa.Text(), nullable=False),
        sa.Column("last_verified_at", sa.Text(), nullable=False),
        sa.Column("valid_until", sa.Text()),
        sa.Column(
            "source_reference_id",
            sa.Text(),
            sa.ForeignKey("source_references.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.Text(), nullable=False),
        sa.CheckConstraint(uuid7(), name="ck_availability_offers_id_uuid7"),
        sa.CheckConstraint(
            "availability_type IN ('digital_purchase','physical_distribution','subscription','streaming','backward_compatibility')",
            name="ck_availability_offers_type",
        ),
        sa.CheckConstraint(
            "status IN ('available','unavailable','unknown')", name="ck_availability_offers_status"
        ),
        sa.CheckConstraint("is_current IN (0,1)", name="ck_availability_offers_current"),
        sa.CheckConstraint(partial_date("valid_from"), name="ck_availability_offers_valid_from"),
        sa.CheckConstraint(partial_date("valid_to"), name="ck_availability_offers_valid_to"),
    )
    for name, columns in (
        ("release_id", ["release_id"]),
        ("access_platform_id", ["access_platform_id"]),
        ("current_status_valid", ["is_current", "status", "valid_until"]),
        ("region_id", ["region_id"]),
        ("offer_identity_key", ["offer_identity_key"]),
    ):
        op.create_index(f"ix_availability_offers_{name}", "availability_offers", columns)
    op.create_index(
        "uq_availability_offers_current",
        "availability_offers",
        ["offer_identity_key"],
        unique=True,
        sqlite_where=sa.text("is_current=1"),
    )

    op.create_table(
        "platform_lock_reasons",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("code", sa.Text(), nullable=False, unique=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("active", sa.Boolean(), server_default="1", nullable=False),
        sa.CheckConstraint(uuid7(), name="ck_platform_lock_reasons_id_uuid7"),
        sa.CheckConstraint("active IN (0,1)", name="ck_platform_lock_reasons_active"),
    )
    op.create_index("ix_platform_lock_reasons_active", "platform_lock_reasons", ["active"])
    op.create_table(
        "platform_lock_assessments",
        sa.Column(
            "game_id", sa.Text(), sa.ForeignKey("games.id", ondelete="CASCADE"), primary_key=True
        ),
        sa.Column("locked", sa.Boolean()),
        sa.Column("severity_level", sa.Integer()),
        sa.Column("justification", sa.Text()),
        sa.Column("minimum_official_hardware", sa.Text()),
        sa.Column("content_lost", sa.Boolean(), server_default="0", nullable=False),
        sa.Column("state", sa.Text(), nullable=False),
        sa.Column("rule_version", sa.Text()),
        sa.Column("input_version", sa.Text()),
        sa.Column("calculated_at", sa.Text()),
        sa.Column("stale_since", sa.Text()),
        sa.Column("last_error_redacted", sa.Text()),
        sa.CheckConstraint(
            "state IN ('dirty','recalculating','current','stale','failed')",
            name="ck_platform_lock_assessments_state",
        ),
        sa.CheckConstraint(
            "content_lost IN (0,1) AND (locked IS NULL OR locked IN (0,1))",
            name="ck_platform_lock_assessments_booleans",
        ),
        sa.CheckConstraint(
            "(locked IS NULL AND severity_level IS NULL) OR (locked=0 AND severity_level IS NULL) OR (locked=1 AND severity_level BETWEEN 1 AND 6)",
            name="ck_platform_lock_assessments_severity",
        ),
        sa.CheckConstraint(
            "state<>'current' OR (calculated_at IS NOT NULL AND rule_version IS NOT NULL AND input_version IS NOT NULL AND locked IS NOT NULL)",
            name="ck_platform_lock_assessments_current",
        ),
    )
    op.create_index("ix_platform_lock_assessments_state", "platform_lock_assessments", ["state"])
    op.create_index(
        "ix_platform_lock_assessments_severity_level",
        "platform_lock_assessments",
        ["severity_level"],
    )
    op.create_table(
        "game_platform_lock_reasons",
        sa.Column(
            "game_id",
            sa.Text(),
            sa.ForeignKey("platform_lock_assessments.game_id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "reason_id",
            sa.Text(),
            sa.ForeignKey("platform_lock_reasons.id", ondelete="RESTRICT"),
            primary_key=True,
        ),
        sa.Column("is_primary", sa.Boolean(), server_default="0", nullable=False),
        sa.Column("notes", sa.Text()),
        sa.CheckConstraint("is_primary IN (0,1)", name="ck_game_platform_lock_reasons_primary"),
    )
    op.create_index(
        "ix_game_platform_lock_reasons_reason_id", "game_platform_lock_reasons", ["reason_id"]
    )
    op.create_index(
        "uq_game_platform_lock_reasons_primary",
        "game_platform_lock_reasons",
        ["game_id"],
        unique=True,
        sqlite_where=sa.text("is_primary=1"),
    )

    op.execute("""CREATE TRIGGER trg_game_companies_chain_insert BEFORE INSERT ON game_companies BEGIN
      SELECT CASE WHEN NEW.edition_id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM game_editions e WHERE e.id=NEW.edition_id AND e.game_id=NEW.game_id) THEN RAISE(ABORT,'edition does not belong to game') END;
      SELECT CASE WHEN NEW.release_id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM releases r WHERE r.id=NEW.release_id AND r.edition_id=NEW.edition_id) THEN RAISE(ABORT,'release does not belong to edition') END;
    END""")
    op.execute("""CREATE TRIGGER trg_game_companies_chain_update BEFORE UPDATE OF game_id,edition_id,release_id ON game_companies BEGIN
      SELECT CASE WHEN NEW.edition_id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM game_editions e WHERE e.id=NEW.edition_id AND e.game_id=NEW.game_id) THEN RAISE(ABORT,'edition does not belong to game') END;
      SELECT CASE WHEN NEW.release_id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM releases r WHERE r.id=NEW.release_id AND r.edition_id=NEW.edition_id) THEN RAISE(ABORT,'release does not belong to edition') END;
    END""")
    for action in ("INSERT", "UPDATE OF game_id,score_id"):
        suffix = "insert" if action == "INSERT" else "update"
        op.execute(f"""CREATE TRIGGER trg_game_primary_scores_chain_{suffix} BEFORE {action} ON game_primary_scores BEGIN
          SELECT CASE WHEN NOT EXISTS (SELECT 1 FROM game_scores s JOIN releases r ON r.id=s.release_id JOIN game_editions e ON e.id=r.edition_id WHERE s.id=NEW.score_id AND e.game_id=NEW.game_id) THEN RAISE(ABORT,'score does not belong to game') END;
        END""")
    op.execute(
        "UPDATE schema_metadata SET schema_version='0005_catalog_facts_and_availability', updated_at=strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id=1"
    )


def downgrade() -> None:
    for trigger in (
        "trg_game_primary_scores_chain_update",
        "trg_game_primary_scores_chain_insert",
        "trg_game_companies_chain_update",
        "trg_game_companies_chain_insert",
    ):
        op.execute(f"DROP TRIGGER IF EXISTS {trigger}")
    for table in (
        "game_platform_lock_reasons",
        "platform_lock_assessments",
        "platform_lock_reasons",
        "availability_offers",
        "game_lengths",
        "game_primary_scores",
        "game_scores",
        "game_companies",
        "franchise_ownerships",
    ):
        op.drop_table(table)
    op.execute(
        "UPDATE schema_metadata SET schema_version='0004_sources_and_external_ids', updated_at=strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id=1"
    )

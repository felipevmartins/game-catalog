"""Create the private personal game collection.

Revision ID: 0006_personal_collection
Revises: 0005_catalog_facts_and_availability
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006_personal_collection"
down_revision: str | None = "0005_catalog_facts_and_availability"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "personal_collection_items",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column(
            "game_id", sa.Text(), sa.ForeignKey("games.id", ondelete="RESTRICT"), nullable=False
        ),
        sa.Column("edition_id", sa.Text(), sa.ForeignKey("game_editions.id", ondelete="RESTRICT")),
        sa.Column("release_id", sa.Text(), sa.ForeignKey("releases.id", ondelete="RESTRICT")),
        sa.Column("product_id", sa.Text(), sa.ForeignKey("products.id", ondelete="RESTRICT")),
        sa.Column("ownership_status", sa.Text(), nullable=False),
        sa.Column("ownership_format", sa.Text(), nullable=False),
        sa.Column("media_condition", sa.Text()),
        sa.Column("box_condition", sa.Text()),
        sa.Column("completeness", sa.Text()),
        sa.Column("acquisition_date", sa.Text()),
        sa.Column("purchase_amount_minor", sa.Integer()),
        sa.Column("purchase_currency_code", sa.Text()),
        sa.Column("acquired_from", sa.Text()),
        sa.Column("loaned_to", sa.Text()),
        sa.Column("loaned_at", sa.Text()),
        sa.Column("loan_due_date", sa.Text()),
        sa.Column("sale_date", sa.Text()),
        sa.Column("sale_amount_minor", sa.Integer()),
        sa.Column("sale_currency_code", sa.Text()),
        sa.Column("personal_score", sa.Numeric()),
        sa.Column("played", sa.Boolean(), server_default="0", nullable=False),
        sa.Column("completed", sa.Boolean(), server_default="0", nullable=False),
        sa.Column("private_notes", sa.Text()),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.Text(), nullable=False),
        sa.CheckConstraint(
            "length(id)=36 AND substr(id,9,1)='-' AND substr(id,14,1)='-' "
            "AND substr(id,19,1)='-' AND substr(id,24,1)='-' "
            "AND id=lower(id) AND substr(id,15,1)='7' "
            "AND substr(id,20,1) IN ('8','9','a','b') "
            "AND replace(id,'-','') NOT GLOB '*[^0-9a-f]*'",
            name="ck_personal_collection_items_id_uuid7",
        ),
        sa.CheckConstraint(
            "acquisition_date IS NULL OR date(acquisition_date)=acquisition_date",
            name="ck_personal_collection_items_acquisition_date",
        ),
        sa.CheckConstraint(
            "loaned_at IS NULL OR date(loaned_at)=loaned_at",
            name="ck_personal_collection_items_loaned_at",
        ),
        sa.CheckConstraint(
            "loan_due_date IS NULL OR date(loan_due_date)=loan_due_date",
            name="ck_personal_collection_items_loan_due_date",
        ),
        sa.CheckConstraint(
            "sale_date IS NULL OR date(sale_date)=sale_date",
            name="ck_personal_collection_items_sale_date",
        ),
        sa.CheckConstraint(
            "ownership_status IN ('owned','loaned_out','sold','lost','disposed','wishlist')",
            name="ck_personal_collection_items_status",
        ),
        sa.CheckConstraint(
            "ownership_format IN ('physical','digital','license','unknown')",
            name="ck_personal_collection_items_format",
        ),
        sa.CheckConstraint(
            "media_condition IS NULL OR media_condition IN ('sealed','like_new','good','fair','poor','damaged','not_applicable')",
            name="ck_personal_collection_items_media_condition",
        ),
        sa.CheckConstraint(
            "box_condition IS NULL OR box_condition IN ('sealed','like_new','good','fair','poor','damaged','not_applicable')",
            name="ck_personal_collection_items_box_condition",
        ),
        sa.CheckConstraint(
            "completeness IS NULL OR completeness IN ('complete','missing_manual','missing_box','loose','unknown','not_applicable')",
            name="ck_personal_collection_items_completeness",
        ),
        sa.CheckConstraint(
            "(purchase_amount_minor IS NULL)=(purchase_currency_code IS NULL) AND (purchase_amount_minor IS NULL OR purchase_amount_minor>=0)",
            name="ck_personal_collection_items_purchase_money",
        ),
        sa.CheckConstraint(
            "(sale_amount_minor IS NULL)=(sale_currency_code IS NULL) AND (sale_amount_minor IS NULL OR sale_amount_minor>=0)",
            name="ck_personal_collection_items_sale_money",
        ),
        sa.CheckConstraint(
            "purchase_currency_code IS NULL OR (length(purchase_currency_code)=3 AND purchase_currency_code=upper(purchase_currency_code) AND purchase_currency_code NOT GLOB '*[^A-Z]*')",
            name="ck_personal_collection_items_purchase_currency",
        ),
        sa.CheckConstraint(
            "sale_currency_code IS NULL OR (length(sale_currency_code)=3 AND sale_currency_code=upper(sale_currency_code) AND sale_currency_code NOT GLOB '*[^A-Z]*')",
            name="ck_personal_collection_items_sale_currency",
        ),
        sa.CheckConstraint(
            "ownership_status<>'loaned_out' OR (loaned_to IS NOT NULL AND loaned_at IS NOT NULL)",
            name="ck_personal_collection_items_loan",
        ),
        sa.CheckConstraint(
            "played IN (0,1) AND completed IN (0,1) AND (completed=0 OR played=1)",
            name="ck_personal_collection_items_played",
        ),
        sa.CheckConstraint(
            "personal_score IS NULL OR personal_score BETWEEN 0 AND 10",
            name="ck_personal_collection_items_score",
        ),
        sa.CheckConstraint(
            "release_id IS NULL OR edition_id IS NOT NULL",
            name="ck_personal_collection_items_release_edition",
        ),
        sa.CheckConstraint(
            "product_id IS NULL OR release_id IS NOT NULL",
            name="ck_personal_collection_items_product_release",
        ),
    )
    for column in ("game_id", "edition_id", "release_id", "product_id", "ownership_status"):
        op.create_index(
            f"ix_personal_collection_items_{column}", "personal_collection_items", [column]
        )
    chain_sql = """
      SELECT CASE WHEN NEW.edition_id IS NOT NULL AND NOT EXISTS
        (SELECT 1 FROM game_editions e WHERE e.id=NEW.edition_id AND e.game_id=NEW.game_id)
        THEN RAISE(ABORT,'edition does not belong to game') END;
      SELECT CASE WHEN NEW.release_id IS NOT NULL AND NOT EXISTS
        (SELECT 1 FROM releases r WHERE r.id=NEW.release_id AND r.edition_id=NEW.edition_id)
        THEN RAISE(ABORT,'release does not belong to edition') END;
      SELECT CASE WHEN NEW.product_id IS NOT NULL AND NOT EXISTS
        (SELECT 1 FROM products p WHERE p.id=NEW.product_id AND p.release_id=NEW.release_id)
        THEN RAISE(ABORT,'product does not belong to release') END;
    """
    op.execute(
        f"CREATE TRIGGER trg_personal_collection_chain_insert BEFORE INSERT ON personal_collection_items BEGIN {chain_sql} END"
    )
    op.execute(
        f"CREATE TRIGGER trg_personal_collection_chain_update BEFORE UPDATE OF game_id,edition_id,release_id,product_id ON personal_collection_items BEGIN {chain_sql} END"
    )
    op.execute(
        "UPDATE schema_metadata SET schema_version='0006_personal_collection', updated_at=strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id=1"
    )


def downgrade() -> None:
    count = (
        op.get_bind()
        .execute(sa.text("SELECT count(*) FROM personal_collection_items"))
        .scalar_one()
    )
    if count:
        raise RuntimeError(
            "0006 downgrade requires an empty personal collection after explicit backup/export"
        )
    op.execute("DROP TRIGGER IF EXISTS trg_personal_collection_chain_update")
    op.execute("DROP TRIGGER IF EXISTS trg_personal_collection_chain_insert")
    op.drop_table("personal_collection_items")
    op.execute(
        "UPDATE schema_metadata SET schema_version='0005_catalog_facts_and_availability', updated_at=strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id=1"
    )

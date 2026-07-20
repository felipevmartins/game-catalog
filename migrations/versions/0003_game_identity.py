"""Create the canonical game identity chain.

Revision ID: 0003_game_identity
Revises: 0002_reference_catalog
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003_game_identity"
down_revision: str | None = "0002_reference_catalog"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def uuid7(column: str = "id") -> str:
    return (
        f"length({column})=36 AND substr({column},9,1)='-' AND substr({column},14,1)='-' "
        f"AND substr({column},19,1)='-' AND substr({column},24,1)='-' "
        f"AND {column}=lower({column}) "
        f"AND replace({column},'-','') NOT GLOB '*[^0-9a-f]*' "
        f"AND substr({column},15,1)='7' AND substr({column},20,1) IN ('8','9','a','b')"
    )


def discriminator(column: str = "identity_discriminator") -> str:
    return f"length(trim({column})) > 0"


def upgrade() -> None:
    op.create_table(
        "games",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("canonical_title", sa.Text(), nullable=False),
        sa.Column("normalized_title", sa.Text(), nullable=False),
        sa.Column("franchise_id", sa.Text(), nullable=True),
        sa.Column("game_type", sa.Text(), nullable=False),
        sa.Column("campaign_focus", sa.Text(), nullable=False),
        sa.Column("online_only", sa.Boolean(), server_default="0", nullable=False),
        sa.Column("regional_only", sa.Boolean(), server_default="0", nullable=False),
        sa.Column("historically_relevant", sa.Boolean(), server_default="0", nullable=False),
        sa.Column("collector_relevant", sa.Boolean(), server_default="0", nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.Text(), nullable=False),
        sa.Column("deleted_at", sa.Text(), nullable=True),
        sa.CheckConstraint(uuid7(), name="ck_games_id_uuid7"),
        sa.CheckConstraint(
            "game_type IN ('main','spin_off','remake','reboot','compilation',"
            "'standalone_expansion','other')",
            name="ck_games_game_type",
        ),
        sa.CheckConstraint(
            "campaign_focus IN ('primary','significant','minor','none','unknown')",
            name="ck_games_campaign_focus",
        ),
        sa.CheckConstraint(
            "online_only IN (0,1) AND regional_only IN (0,1) "
            "AND historically_relevant IN (0,1) AND collector_relevant IN (0,1)",
            name="ck_games_booleans",
        ),
        sa.ForeignKeyConstraint(
            ["franchise_id"],
            ["franchises.id"],
            ondelete="RESTRICT",
            name="fk_games_franchise_id_franchises",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_games"),
    )
    op.create_index("ix_games_normalized_title", "games", ["normalized_title"])
    op.create_index("ix_games_franchise_id", "games", ["franchise_id"])
    op.create_index("ix_games_game_type", "games", ["game_type"])

    op.create_table(
        "game_editions",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("game_id", sa.Text(), nullable=False),
        sa.Column("identity_discriminator", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("normalized_name", sa.Text(), nullable=False),
        sa.Column("edition_type", sa.Text(), nullable=False),
        sa.Column("is_definitive", sa.Boolean(), server_default="0", nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.Text(), nullable=False),
        sa.Column("deleted_at", sa.Text(), nullable=True),
        sa.CheckConstraint(uuid7(), name="ck_game_editions_id_uuid7"),
        sa.CheckConstraint(discriminator(), name="ck_game_editions_discriminator"),
        sa.CheckConstraint(
            "edition_type IN ('original','remaster','enhanced','directors_cut','definitive',"
            "'complete','goty','technical_variant','regional_variant','other')",
            name="ck_game_editions_edition_type",
        ),
        sa.CheckConstraint("is_definitive IN (0,1)", name="ck_game_editions_is_definitive"),
        sa.ForeignKeyConstraint(
            ["game_id"], ["games.id"], ondelete="RESTRICT", name="fk_game_editions_game_id_games"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_game_editions"),
    )
    op.create_index("ix_game_editions_game_id", "game_editions", ["game_id"])
    op.create_index("ix_game_editions_edition_type", "game_editions", ["edition_type"])
    op.create_index("ix_game_editions_normalized_name", "game_editions", ["normalized_name"])
    op.create_index(
        "uq_game_editions_active_discriminator",
        "game_editions",
        ["game_id", "identity_discriminator"],
        unique=True,
        sqlite_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "uq_game_editions_active_original",
        "game_editions",
        ["game_id"],
        unique=True,
        sqlite_where=sa.text("edition_type='original' AND deleted_at IS NULL"),
    )

    op.create_table(
        "releases",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("edition_id", sa.Text(), nullable=False),
        sa.Column("platform_id", sa.Text(), nullable=False),
        sa.Column("region_id", sa.Text(), nullable=False),
        sa.Column("release_type", sa.Text(), nullable=False),
        sa.Column("identity_discriminator", sa.Text(), nullable=False),
        sa.Column("release_year", sa.Integer(), nullable=True),
        sa.Column("release_month", sa.Integer(), nullable=True),
        sa.Column("release_day", sa.Integer(), nullable=True),
        sa.Column("release_precision", sa.Text(), nullable=False),
        sa.Column("release_qualifier", sa.Text(), nullable=True),
        sa.Column("identity_key", sa.Text(), nullable=False),
        sa.Column("official", sa.Boolean(), server_default="1", nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.Text(), nullable=False),
        sa.Column("deleted_at", sa.Text(), nullable=True),
        sa.CheckConstraint(uuid7(), name="ck_releases_id_uuid7"),
        sa.CheckConstraint(discriminator(), name="ck_releases_discriminator"),
        sa.CheckConstraint("length(trim(identity_key)) > 0", name="ck_releases_identity_key"),
        sa.CheckConstraint(
            "release_type IN ('original','port','rerelease')", name="ck_releases_release_type"
        ),
        sa.CheckConstraint(
            "release_precision IN ('unknown','year','month','day')", name="ck_releases_precision"
        ),
        sa.CheckConstraint(
            "release_qualifier IS NULL OR release_qualifier IN ('circa','before','after')",
            name="ck_releases_qualifier",
        ),
        sa.CheckConstraint("official IN (0,1)", name="ck_releases_official"),
        sa.CheckConstraint(
            "release_year IS NULL OR release_year BETWEEN 1 AND 9999", name="ck_releases_year"
        ),
        sa.CheckConstraint(
            "release_month IS NULL OR release_month BETWEEN 1 AND 12", name="ck_releases_month"
        ),
        sa.CheckConstraint(
            "release_day IS NULL OR release_day BETWEEN 1 AND 31", name="ck_releases_day"
        ),
        sa.CheckConstraint(
            "(release_precision='unknown' AND release_year IS NULL AND release_month IS NULL "
            "AND release_day IS NULL AND release_qualifier IS NULL) OR "
            "(release_precision='year' AND release_year IS NOT NULL "
            "AND release_month IS NULL AND release_day IS NULL) OR "
            "(release_precision='month' AND release_year IS NOT NULL "
            "AND release_month IS NOT NULL AND release_day IS NULL) OR "
            "(release_precision='day' AND release_year IS NOT NULL "
            "AND release_month IS NOT NULL AND release_day IS NOT NULL)",
            name="ck_releases_partial_date",
        ),
        sa.ForeignKeyConstraint(["edition_id"], ["game_editions.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["platform_id"], ["platforms.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["region_id"], ["regions.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name="pk_releases"),
    )
    for name, columns in (
        ("ix_releases_edition_id", ["edition_id"]),
        ("ix_releases_platform_id", ["platform_id"]),
        ("ix_releases_platform_id_region_id", ["platform_id", "region_id"]),
        ("ix_releases_release_year", ["release_year"]),
    ):
        op.create_index(name, "releases", columns)
    op.create_index(
        "uq_releases_active_identity_key",
        "releases",
        ["identity_key"],
        unique=True,
        sqlite_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "uq_releases_active_structure",
        "releases",
        ["edition_id", "platform_id", "region_id", "identity_discriminator"],
        unique=True,
        sqlite_where=sa.text("deleted_at IS NULL"),
    )

    op.create_table(
        "products",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("release_id", sa.Text(), nullable=False),
        sa.Column("product_type", sa.Text(), nullable=False),
        sa.Column("media_format", sa.Text()),
        sa.Column("store_company_id", sa.Text()),
        sa.Column("sku", sa.Text()),
        sa.Column("region_id", sa.Text()),
        sa.Column("display_name", sa.Text()),
        sa.Column("identity_discriminator", sa.Text(), nullable=False),
        sa.Column("identity_key", sa.Text(), nullable=False),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.Text(), nullable=False),
        sa.Column("deleted_at", sa.Text()),
        sa.CheckConstraint(uuid7(), name="ck_products_id_uuid7"),
        sa.CheckConstraint(discriminator(), name="ck_products_discriminator"),
        sa.CheckConstraint("length(trim(identity_key)) > 0", name="ck_products_identity_key"),
        sa.CheckConstraint(
            "product_type IN ('physical','digital','license','single_release_bundle',"
            "'subscription_entitlement','other')",
            name="ck_products_product_type",
        ),
        sa.CheckConstraint(
            "media_format IS NULL OR "
            "media_format IN ('disc','cartridge','download','code','cloud','other')",
            name="ck_products_media_format",
        ),
        sa.ForeignKeyConstraint(["release_id"], ["releases.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["store_company_id"], ["companies.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["region_id"], ["regions.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name="pk_products"),
    )
    for column in ("release_id", "store_company_id", "sku", "region_id"):
        op.create_index(f"ix_products_{column}", "products", [column])
    op.create_index(
        "uq_products_active_identity_key",
        "products",
        ["identity_key"],
        unique=True,
        sqlite_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "uq_products_active_discriminator",
        "products",
        ["release_id", "identity_discriminator"],
        unique=True,
        sqlite_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "uq_products_active_store_sku",
        "products",
        ["store_company_id", "sku", sa.text("COALESCE(region_id,'')")],
        unique=True,
        sqlite_where=sa.text("sku IS NOT NULL AND deleted_at IS NULL"),
    )

    op.create_table(
        "game_aliases",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("game_id", sa.Text(), nullable=False),
        sa.Column("alias", sa.Text(), nullable=False),
        sa.Column("normalized_alias", sa.Text(), nullable=False),
        sa.Column("alias_type", sa.Text(), nullable=False),
        sa.Column("language_code", sa.Text()),
        sa.Column("region_id", sa.Text()),
        sa.Column("source_reference_id", sa.Text()),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.CheckConstraint(uuid7(), name="ck_game_aliases_id_uuid7"),
        sa.CheckConstraint(
            "alias_type IN ('regional_title','original_title','transliteration',"
            "'former_title','import_alias')",
            name="ck_game_aliases_alias_type",
        ),
        sa.ForeignKeyConstraint(["game_id"], ["games.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["region_id"], ["regions.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name="pk_game_aliases"),
    )
    for column in ("normalized_alias", "game_id", "region_id"):
        op.create_index(f"ix_game_aliases_{column}", "game_aliases", [column])
    op.create_index(
        "uq_game_aliases_identity",
        "game_aliases",
        [
            "game_id",
            "normalized_alias",
            "alias_type",
            sa.text("COALESCE(language_code,'')"),
            sa.text("COALESCE(region_id,'')"),
        ],
        unique=True,
    )

    op.create_table(
        "game_relations",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("source_game_id", sa.Text(), nullable=False),
        sa.Column("target_game_id", sa.Text(), nullable=False),
        sa.Column("relation_type", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Text(), nullable=False),
        sa.Column("notes", sa.Text()),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.Text(), nullable=False),
        sa.CheckConstraint(uuid7(), name="ck_game_relations_id_uuid7"),
        sa.CheckConstraint("source_game_id <> target_game_id", name="ck_game_relations_not_self"),
        sa.CheckConstraint(
            "relation_type IN ('remake_of','reboot_of','sequel_to','prequel_to','spin_off_of',"
            "'standalone_expansion_of','same_title_variant_of','compilation_contains',"
            "'spiritual_successor_of')",
            name="ck_game_relations_relation_type",
        ),
        sa.CheckConstraint(
            "confidence IN ('high','medium','low')", name="ck_game_relations_confidence"
        ),
        sa.ForeignKeyConstraint(["source_game_id"], ["games.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["target_game_id"], ["games.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name="pk_game_relations"),
        sa.UniqueConstraint(
            "source_game_id", "target_game_id", "relation_type", name="uq_game_relations_identity"
        ),
    )
    for column in ("source_game_id", "target_game_id", "relation_type"):
        op.create_index(f"ix_game_relations_{column}", "game_relations", [column])

    op.create_table(
        "game_contents",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("parent_game_id", sa.Text(), nullable=False),
        sa.Column("identity_discriminator", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("normalized_title", sa.Text(), nullable=False),
        sa.Column("content_type", sa.Text(), nullable=False),
        sa.Column("requires_base_game", sa.Boolean(), nullable=False),
        sa.Column("sequence_number", sa.Integer()),
        sa.Column("notes", sa.Text()),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.Text(), nullable=False),
        sa.Column("deleted_at", sa.Text()),
        sa.CheckConstraint(uuid7(), name="ck_game_contents_id_uuid7"),
        sa.CheckConstraint(discriminator(), name="ck_game_contents_discriminator"),
        sa.CheckConstraint(
            "content_type IN ('dlc','expansion','episode','campaign','add_on')",
            name="ck_game_contents_content_type",
        ),
        sa.CheckConstraint(
            "requires_base_game IN (0,1)", name="ck_game_contents_requires_base_game"
        ),
        sa.CheckConstraint(
            "sequence_number IS NULL OR sequence_number > 0", name="ck_game_contents_sequence"
        ),
        sa.ForeignKeyConstraint(["parent_game_id"], ["games.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name="pk_game_contents"),
    )
    for column in ("parent_game_id", "content_type", "normalized_title"):
        op.create_index(f"ix_game_contents_{column}", "game_contents", [column])
    op.create_index(
        "uq_game_contents_active_discriminator",
        "game_contents",
        ["parent_game_id", "identity_discriminator"],
        unique=True,
        sqlite_where=sa.text("deleted_at IS NULL"),
    )
    op.execute(
        "UPDATE schema_metadata SET schema_version='0003_game_identity', "
        "updated_at=strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id=1"
    )


def downgrade() -> None:
    for table in (
        "game_contents",
        "game_relations",
        "game_aliases",
        "products",
        "releases",
        "game_editions",
        "games",
    ):
        op.drop_table(table)
    op.execute(
        "UPDATE schema_metadata SET schema_version='0002_reference_catalog', "
        "updated_at=strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id=1"
    )

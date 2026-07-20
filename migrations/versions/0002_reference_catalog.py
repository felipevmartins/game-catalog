"""Create reference catalog tables.

Revision ID: 0002_reference_catalog
Revises: 0001_foundation
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_reference_catalog"
down_revision: str | None = "0001_foundation"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def uuid7_check(column: str = "id") -> str:
    return (
        f"length({column}) = 36 AND substr({column}, 9, 1) = '-' "
        f"AND substr({column}, 14, 1) = '-' AND substr({column}, 19, 1) = '-' "
        f"AND substr({column}, 24, 1) = '-' AND {column} = lower({column}) "
        f"AND replace({column}, '-', '') NOT GLOB '*[^0-9a-f]*' "
        f"AND substr({column}, 15, 1) = '7' "
        f"AND substr({column}, 20, 1) IN ('8', '9', 'a', 'b')"
    )


def common_entity_columns() -> list[sa.Column[object]]:
    return [
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("normalized_name", sa.Text(), nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        "regions",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("code", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("region_type", sa.Text(), nullable=False),
        sa.Column("parent_region_id", sa.Text(), nullable=True),
        sa.Column("active", sa.Boolean(), server_default="1", nullable=False),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.Text(), nullable=False),
        sa.CheckConstraint(uuid7_check(), name="ck_regions_id_uuid7"),
        sa.CheckConstraint(
            "(length(code) = 2 AND code = upper(code) "
            "AND code NOT GLOB '*[^A-Z]*') OR code IN ('WORLD', 'EU', 'NA', 'OTHER')",
            name="ck_regions_code",
        ),
        sa.CheckConstraint(
            "region_type IN ('country', 'market', 'global', 'other')",
            name="ck_regions_region_type",
        ),
        sa.CheckConstraint("active IN (0, 1)", name="ck_regions_active_boolean"),
        sa.CheckConstraint(
            "parent_region_id IS NULL OR parent_region_id <> id",
            name="ck_regions_parent_not_self",
        ),
        sa.ForeignKeyConstraint(
            ["parent_region_id"],
            ["regions.id"],
            name="fk_regions_parent_region_id_regions",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_regions"),
        sa.UniqueConstraint("code", name="uq_regions_code"),
    )
    op.create_index("ix_regions_region_type", "regions", ["region_type"])
    op.create_index("ix_regions_parent_region_id", "regions", ["parent_region_id"])
    op.create_index("ix_regions_active", "regions", ["active"])

    op.create_table(
        "manufacturers",
        *common_entity_columns(),
        sa.Column("country_code", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.Text(), nullable=False),
        sa.Column("deleted_at", sa.Text(), nullable=True),
        sa.CheckConstraint(uuid7_check(), name="ck_manufacturers_id_uuid7"),
        sa.CheckConstraint(
            "country_code IS NULL OR "
            "(length(country_code) = 2 AND country_code = upper(country_code) "
            "AND country_code NOT GLOB '*[^A-Z]*')",
            name="ck_manufacturers_country_code",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_manufacturers"),
    )
    op.create_index("ix_manufacturers_normalized_name", "manufacturers", ["normalized_name"])
    op.create_index(
        "uq_manufacturers_active_normalized_name",
        "manufacturers",
        ["normalized_name"],
        unique=True,
        sqlite_where=sa.text("deleted_at IS NULL"),
    )

    op.create_table(
        "ecosystems",
        *common_entity_columns(),
        sa.Column("manufacturer_id", sa.Text(), nullable=True),
        sa.Column("ecosystem_type", sa.Text(), nullable=False),
        sa.Column("parent_ecosystem_id", sa.Text(), nullable=True),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.Text(), nullable=False),
        sa.Column("deleted_at", sa.Text(), nullable=True),
        sa.CheckConstraint(uuid7_check(), name="ck_ecosystems_id_uuid7"),
        sa.CheckConstraint(
            "ecosystem_type IN ('console_family', 'pc', 'arcade', 'mobile', 'cloud', 'other')",
            name="ck_ecosystems_ecosystem_type",
        ),
        sa.CheckConstraint(
            "parent_ecosystem_id IS NULL OR parent_ecosystem_id <> id",
            name="ck_ecosystems_parent_not_self",
        ),
        sa.ForeignKeyConstraint(
            ["manufacturer_id"],
            ["manufacturers.id"],
            name="fk_ecosystems_manufacturer_id_manufacturers",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["parent_ecosystem_id"],
            ["ecosystems.id"],
            name="fk_ecosystems_parent_ecosystem_id_ecosystems",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_ecosystems"),
    )
    op.create_index("ix_ecosystems_manufacturer_id", "ecosystems", ["manufacturer_id"])
    op.create_index("ix_ecosystems_parent_ecosystem_id", "ecosystems", ["parent_ecosystem_id"])
    op.create_index(
        "uq_ecosystems_active_normalized_name",
        "ecosystems",
        ["normalized_name"],
        unique=True,
        sqlite_where=sa.text("deleted_at IS NULL"),
    )

    op.create_table(
        "companies",
        *common_entity_columns(),
        sa.Column("company_type", sa.Text(), nullable=False),
        sa.Column("parent_company_id", sa.Text(), nullable=True),
        sa.Column("country_code", sa.Text(), nullable=True),
        sa.Column("website", sa.Text(), nullable=True),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.Text(), nullable=False),
        sa.Column("deleted_at", sa.Text(), nullable=True),
        sa.CheckConstraint(uuid7_check(), name="ck_companies_id_uuid7"),
        sa.CheckConstraint(
            "company_type IN ('developer', 'publisher', 'platform_holder', 'distributor', "
            "'store', 'holding', 'other')",
            name="ck_companies_company_type",
        ),
        sa.CheckConstraint(
            "parent_company_id IS NULL OR parent_company_id <> id",
            name="ck_companies_parent_not_self",
        ),
        sa.CheckConstraint(
            "country_code IS NULL OR "
            "(length(country_code) = 2 AND country_code = upper(country_code) "
            "AND country_code NOT GLOB '*[^A-Z]*')",
            name="ck_companies_country_code",
        ),
        sa.ForeignKeyConstraint(
            ["parent_company_id"],
            ["companies.id"],
            name="fk_companies_parent_company_id_companies",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_companies"),
    )
    op.create_index("ix_companies_normalized_name", "companies", ["normalized_name"])
    op.create_index("ix_companies_parent_company_id", "companies", ["parent_company_id"])
    op.create_index("ix_companies_company_type", "companies", ["company_type"])
    op.create_index(
        "uq_companies_active_identity",
        "companies",
        ["normalized_name", sa.text("COALESCE(country_code, '')")],
        unique=True,
        sqlite_where=sa.text("deleted_at IS NULL"),
    )

    op.create_table(
        "franchises",
        *common_entity_columns(),
        sa.Column("parent_franchise_id", sa.Text(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("status_reason", sa.Text(), nullable=True),
        sa.Column("official_end_confirmed", sa.Boolean(), server_default="0", nullable=False),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.Text(), nullable=False),
        sa.Column("deleted_at", sa.Text(), nullable=True),
        sa.CheckConstraint(uuid7_check(), name="ck_franchises_id_uuid7"),
        sa.CheckConstraint(
            "status IN ('active', 'hiatus', 'officially_ended', 'unknown')",
            name="ck_franchises_status",
        ),
        sa.CheckConstraint(
            "official_end_confirmed IN (0, 1)", name="ck_franchises_official_end_boolean"
        ),
        sa.CheckConstraint(
            "parent_franchise_id IS NULL OR parent_franchise_id <> id",
            name="ck_franchises_parent_not_self",
        ),
        sa.CheckConstraint(
            "status <> 'officially_ended' OR official_end_confirmed = 1",
            name="ck_franchises_official_end_confirmed",
        ),
        sa.ForeignKeyConstraint(
            ["parent_franchise_id"],
            ["franchises.id"],
            name="fk_franchises_parent_franchise_id_franchises",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_franchises"),
    )
    op.create_index("ix_franchises_parent_franchise_id", "franchises", ["parent_franchise_id"])
    op.create_index("ix_franchises_status", "franchises", ["status"])
    op.create_index(
        "uq_franchises_active_identity",
        "franchises",
        ["normalized_name", sa.text("COALESCE(parent_franchise_id, '')")],
        unique=True,
        sqlite_where=sa.text("deleted_at IS NULL"),
    )

    op.create_table(
        "franchise_ecosystems",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("franchise_id", sa.Text(), nullable=False),
        sa.Column("ecosystem_id", sa.Text(), nullable=False),
        sa.Column("association_type", sa.Text(), nullable=False),
        sa.Column("valid_from_year", sa.Integer(), nullable=True),
        sa.Column("valid_to_year", sa.Integer(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.CheckConstraint(uuid7_check(), name="ck_franchise_ecosystems_id_uuid7"),
        sa.CheckConstraint(
            "association_type IN ('first_party', 'second_party', 'owned_ip', 'historical', "
            "'strong_association', 'other')",
            name="ck_franchise_ecosystems_association_type",
        ),
        sa.CheckConstraint(
            "valid_to_year IS NULL OR valid_from_year IS NULL OR valid_to_year >= valid_from_year",
            name="ck_franchise_ecosystems_year_range",
        ),
        sa.ForeignKeyConstraint(
            ["franchise_id"],
            ["franchises.id"],
            name="fk_franchise_ecosystems_franchise_id_franchises",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["ecosystem_id"],
            ["ecosystems.id"],
            name="fk_franchise_ecosystems_ecosystem_id_ecosystems",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_franchise_ecosystems"),
    )
    op.create_index(
        "ix_franchise_ecosystems_ecosystem_id", "franchise_ecosystems", ["ecosystem_id"]
    )
    op.create_index(
        "ix_franchise_ecosystems_franchise_id", "franchise_ecosystems", ["franchise_id"]
    )
    op.create_index(
        "uq_franchise_ecosystems_identity",
        "franchise_ecosystems",
        [
            "franchise_id",
            "ecosystem_id",
            "association_type",
            sa.text("COALESCE(valid_from_year, -1)"),
        ],
        unique=True,
    )

    op.create_table(
        "platforms",
        *common_entity_columns(),
        sa.Column("manufacturer_id", sa.Text(), nullable=True),
        sa.Column("ecosystem_id", sa.Text(), nullable=True),
        sa.Column("platform_type", sa.Text(), nullable=False),
        sa.Column("release_year", sa.Integer(), nullable=True),
        sa.Column("discontinuation_year", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.Text(), nullable=False),
        sa.Column("deleted_at", sa.Text(), nullable=True),
        sa.CheckConstraint(uuid7_check(), name="ck_platforms_id_uuid7"),
        sa.CheckConstraint(
            "platform_type IN ('home_console', 'portable_console', 'hybrid_console', 'pc', "
            "'arcade', 'mobile', 'cloud', 'other')",
            name="ck_platforms_platform_type",
        ),
        sa.CheckConstraint(
            "discontinuation_year IS NULL OR release_year IS NULL "
            "OR discontinuation_year >= release_year",
            name="ck_platforms_year_range",
        ),
        sa.ForeignKeyConstraint(
            ["manufacturer_id"],
            ["manufacturers.id"],
            name="fk_platforms_manufacturer_id_manufacturers",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["ecosystem_id"],
            ["ecosystems.id"],
            name="fk_platforms_ecosystem_id_ecosystems",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_platforms"),
    )
    op.create_index("ix_platforms_manufacturer_id", "platforms", ["manufacturer_id"])
    op.create_index("ix_platforms_ecosystem_id", "platforms", ["ecosystem_id"])
    op.create_index("ix_platforms_platform_type", "platforms", ["platform_type"])
    op.create_index(
        "uq_platforms_active_normalized_name",
        "platforms",
        ["normalized_name"],
        unique=True,
        sqlite_where=sa.text("deleted_at IS NULL"),
    )

    op.execute(
        "UPDATE schema_metadata SET schema_version = '0002_reference_catalog', "
        "updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now') WHERE id = 1"
    )


def downgrade() -> None:
    op.drop_table("platforms")
    op.drop_table("franchise_ecosystems")
    op.drop_table("franchises")
    op.drop_table("companies")
    op.drop_table("ecosystems")
    op.drop_table("manufacturers")
    op.drop_table("regions")
    op.execute(
        "UPDATE schema_metadata SET schema_version = '0001_foundation', "
        "updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now') WHERE id = 1"
    )

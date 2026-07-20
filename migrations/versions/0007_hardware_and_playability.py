"""Create hardware catalog, personal units, requirements and playability.

Revision ID: 0007_hardware_and_playability
Revises: 0006_personal_collection
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0007_hardware_and_playability"
down_revision: str | None = "0006_personal_collection"
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


def upgrade() -> None:
    op.create_table(
        "hardware_models",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("platform_id", sa.Text(), sa.ForeignKey("platforms.id", ondelete="RESTRICT")),
        sa.Column(
            "manufacturer_id", sa.Text(), sa.ForeignKey("manufacturers.id", ondelete="RESTRICT")
        ),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("normalized_name", sa.Text(), nullable=False),
        sa.Column("model_code", sa.Text()),
        sa.Column("hardware_type", sa.Text(), nullable=False),
        sa.Column("introduced_year", sa.Integer()),
        sa.Column("discontinued_year", sa.Integer()),
        sa.Column("notes", sa.Text()),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.Text(), nullable=False),
        sa.Column("deleted_at", sa.Text()),
        sa.CheckConstraint(uuid7(), name="ck_hardware_models_id_uuid7"),
        sa.CheckConstraint(
            "hardware_type IN ('console','handheld','pc','streaming_device','adapter','other')",
            name="ck_hardware_models_type",
        ),
        sa.CheckConstraint(
            "discontinued_year IS NULL OR introduced_year IS NULL OR discontinued_year>=introduced_year",
            name="ck_hardware_models_years",
        ),
    )
    for column in ("platform_id", "manufacturer_id", "normalized_name"):
        op.create_index(f"ix_hardware_models_{column}", "hardware_models", [column])
    op.create_index(
        "uq_hardware_models_active_identity",
        "hardware_models",
        [
            sa.text("COALESCE(manufacturer_id,'')"),
            "normalized_name",
            sa.text("COALESCE(model_code,'')"),
        ],
        unique=True,
        sqlite_where=sa.text("deleted_at IS NULL"),
    )

    op.create_table(
        "hardware_model_external_ids",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column(
            "hardware_model_id",
            sa.Text(),
            sa.ForeignKey("hardware_models.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "source_id", sa.Text(), sa.ForeignKey("sources.id", ondelete="RESTRICT"), nullable=False
        ),
        sa.Column("external_id", sa.Text(), nullable=False),
        sa.Column("context", sa.Text(), server_default="global", nullable=False),
        sa.Column("is_primary", sa.Boolean(), server_default="0", nullable=False),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.Text(), nullable=False),
        sa.CheckConstraint(uuid7(), name="ck_hardware_model_external_ids_id_uuid7"),
        sa.CheckConstraint(
            "length(trim(external_id))>0 AND length(trim(context))>0 AND is_primary IN (0,1)",
            name="ck_hardware_model_external_ids_values",
        ),
        sa.UniqueConstraint(
            "source_id",
            "external_id",
            "context",
            name="uq_hardware_model_external_ids_source_external_context",
        ),
    )
    op.create_index(
        "ix_hardware_model_external_ids_hardware_model_id",
        "hardware_model_external_ids",
        ["hardware_model_id"],
    )
    op.create_index(
        "ix_hardware_model_external_ids_source_external_context",
        "hardware_model_external_ids",
        ["source_id", "external_id", "context"],
    )
    op.create_index(
        "uq_hardware_model_external_ids_primary",
        "hardware_model_external_ids",
        ["hardware_model_id", "source_id", "context"],
        unique=True,
        sqlite_where=sa.text("is_primary=1"),
    )

    op.create_table(
        "personal_hardware_units",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column(
            "hardware_model_id",
            sa.Text(),
            sa.ForeignKey("hardware_models.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("ownership_status", sa.Text(), nullable=False),
        sa.Column("working_status", sa.Text(), nullable=False),
        sa.Column("serial_number", sa.Text()),
        sa.Column("nickname", sa.Text()),
        sa.Column("storage_capacity_gb", sa.Integer()),
        sa.Column("acquisition_date", sa.Text()),
        sa.Column("purchase_amount_minor", sa.Integer()),
        sa.Column("purchase_currency_code", sa.Text()),
        sa.Column("sale_amount_minor", sa.Integer()),
        sa.Column("sale_currency_code", sa.Text()),
        sa.Column("sale_date", sa.Text()),
        sa.Column("acquired_from", sa.Text()),
        sa.Column("location", sa.Text()),
        sa.Column("private_notes", sa.Text()),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.Text(), nullable=False),
        sa.CheckConstraint(uuid7(), name="ck_personal_hardware_units_id_uuid7"),
        sa.CheckConstraint(
            "ownership_status IN ('owned','loaned_in','sold','lost','disposed')",
            name="ck_personal_hardware_units_ownership",
        ),
        sa.CheckConstraint(
            "working_status IN ('working','partially_working','under_repair','defective','for_parts')",
            name="ck_personal_hardware_units_working",
        ),
        sa.CheckConstraint(
            "storage_capacity_gb IS NULL OR storage_capacity_gb>=0",
            name="ck_personal_hardware_units_storage",
        ),
        sa.CheckConstraint(
            "(purchase_amount_minor IS NULL)=(purchase_currency_code IS NULL) AND (purchase_amount_minor IS NULL OR purchase_amount_minor>=0)",
            name="ck_personal_hardware_units_purchase",
        ),
        sa.CheckConstraint(
            "(sale_amount_minor IS NULL)=(sale_currency_code IS NULL) AND (sale_amount_minor IS NULL OR sale_amount_minor>=0)",
            name="ck_personal_hardware_units_sale",
        ),
    )
    for column in ("hardware_model_id", "ownership_status", "working_status"):
        op.create_index(f"ix_personal_hardware_units_{column}", "personal_hardware_units", [column])
    op.create_index(
        "uq_personal_hardware_units_serial",
        "personal_hardware_units",
        ["hardware_model_id", "serial_number"],
        unique=True,
        sqlite_where=sa.text("serial_number IS NOT NULL"),
    )

    op.create_table(
        "accessory_models",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column(
            "manufacturer_id", sa.Text(), sa.ForeignKey("manufacturers.id", ondelete="RESTRICT")
        ),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("normalized_name", sa.Text(), nullable=False),
        sa.Column("accessory_type", sa.Text(), nullable=False),
        sa.Column("model_code", sa.Text()),
        sa.Column("notes", sa.Text()),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.Text(), nullable=False),
        sa.Column("deleted_at", sa.Text()),
        sa.CheckConstraint(uuid7(), name="ck_accessory_models_id_uuid7"),
        sa.CheckConstraint(
            "accessory_type IN ('controller','motion_sensor','camera','adapter','storage','network','arcade_controller','other')",
            name="ck_accessory_models_type",
        ),
    )
    for column in ("manufacturer_id", "accessory_type", "normalized_name"):
        op.create_index(f"ix_accessory_models_{column}", "accessory_models", [column])
    op.create_index(
        "uq_accessory_models_active_identity",
        "accessory_models",
        [
            sa.text("COALESCE(manufacturer_id,'')"),
            "normalized_name",
            sa.text("COALESCE(model_code,'')"),
        ],
        unique=True,
        sqlite_where=sa.text("deleted_at IS NULL"),
    )

    op.create_table(
        "accessory_platforms",
        sa.Column(
            "accessory_model_id",
            sa.Text(),
            sa.ForeignKey("accessory_models.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "platform_id",
            sa.Text(),
            sa.ForeignKey("platforms.id", ondelete="RESTRICT"),
            primary_key=True,
        ),
        sa.Column("support_level", sa.Text(), nullable=False),
        sa.Column(
            "required_adapter_model_id",
            sa.Text(),
            sa.ForeignKey("accessory_models.id", ondelete="RESTRICT"),
        ),
        sa.Column("notes", sa.Text()),
        sa.CheckConstraint(
            "support_level IN ('full','partial','adapter_required')",
            name="ck_accessory_platforms_support",
        ),
        sa.CheckConstraint(
            "support_level<>'adapter_required' OR required_adapter_model_id IS NOT NULL",
            name="ck_accessory_platforms_adapter_required",
        ),
        sa.CheckConstraint(
            "required_adapter_model_id IS NULL OR required_adapter_model_id<>accessory_model_id",
            name="ck_accessory_platforms_adapter_not_self",
        ),
    )
    op.create_index("ix_accessory_platforms_platform_id", "accessory_platforms", ["platform_id"])

    op.create_table(
        "personal_accessory_units",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column(
            "accessory_model_id",
            sa.Text(),
            sa.ForeignKey("accessory_models.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("ownership_status", sa.Text(), nullable=False),
        sa.Column("working_status", sa.Text(), nullable=False),
        sa.Column("serial_number", sa.Text()),
        sa.Column("acquisition_date", sa.Text()),
        sa.Column("purchase_amount_minor", sa.Integer()),
        sa.Column("purchase_currency_code", sa.Text()),
        sa.Column("sale_amount_minor", sa.Integer()),
        sa.Column("sale_currency_code", sa.Text()),
        sa.Column("sale_date", sa.Text()),
        sa.Column("location", sa.Text()),
        sa.Column("private_notes", sa.Text()),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.Text(), nullable=False),
        sa.CheckConstraint(uuid7(), name="ck_personal_accessory_units_id_uuid7"),
        sa.CheckConstraint(
            "ownership_status IN ('owned','loaned_in','sold','lost','disposed')",
            name="ck_personal_accessory_units_ownership",
        ),
        sa.CheckConstraint(
            "working_status IN ('working','partially_working','under_repair','defective','for_parts')",
            name="ck_personal_accessory_units_working",
        ),
        sa.CheckConstraint(
            "(purchase_amount_minor IS NULL)=(purchase_currency_code IS NULL) AND (purchase_amount_minor IS NULL OR purchase_amount_minor>=0)",
            name="ck_personal_accessory_units_purchase",
        ),
        sa.CheckConstraint(
            "(sale_amount_minor IS NULL)=(sale_currency_code IS NULL) AND (sale_amount_minor IS NULL OR sale_amount_minor>=0)",
            name="ck_personal_accessory_units_sale",
        ),
    )
    for column in ("accessory_model_id", "ownership_status", "working_status"):
        op.create_index(
            f"ix_personal_accessory_units_{column}", "personal_accessory_units", [column]
        )
    op.create_index(
        "uq_personal_accessory_units_serial",
        "personal_accessory_units",
        ["accessory_model_id", "serial_number"],
        unique=True,
        sqlite_where=sa.text("serial_number IS NOT NULL"),
    )

    op.create_table(
        "personal_capabilities",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("capability_code", sa.Text(), nullable=False),
        sa.Column(
            "provider_company_id", sa.Text(), sa.ForeignKey("companies.id", ondelete="RESTRICT")
        ),
        sa.Column("platform_id", sa.Text(), sa.ForeignKey("platforms.id", ondelete="RESTRICT")),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("valid_until", sa.Text()),
        sa.Column("private_notes", sa.Text()),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.Text(), nullable=False),
        sa.CheckConstraint(uuid7(), name="ck_personal_capabilities_id_uuid7"),
        sa.CheckConstraint(
            "capability_code IN ('network_access','active_subscription','online_account','other')",
            name="ck_personal_capabilities_code",
        ),
        sa.CheckConstraint(
            "status IN ('available','unavailable','unknown')",
            name="ck_personal_capabilities_status",
        ),
    )
    for name, columns in (
        ("capability_code", ["capability_code"]),
        ("provider_company_id", ["provider_company_id"]),
        ("platform_id", ["platform_id"]),
        ("status_valid_until", ["status", "valid_until"]),
    ):
        op.create_index(f"ix_personal_capabilities_{name}", "personal_capabilities", columns)
    op.create_index(
        "uq_personal_capabilities_identity",
        "personal_capabilities",
        [
            "capability_code",
            sa.text("COALESCE(provider_company_id,'')"),
            sa.text("COALESCE(platform_id,'')"),
        ],
        unique=True,
    )

    op.create_table(
        "hardware_compatibility_rules",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column(
            "source_hardware_model_id",
            sa.Text(),
            sa.ForeignKey("hardware_models.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "target_platform_id",
            sa.Text(),
            sa.ForeignKey("platforms.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("compatibility_type", sa.Text(), nullable=False),
        sa.Column("scope", sa.Text(), nullable=False),
        sa.Column(
            "source_reference_id",
            sa.Text(),
            sa.ForeignKey("source_references.id", ondelete="RESTRICT"),
        ),
        sa.Column("notes", sa.Text()),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.Text(), nullable=False),
        sa.CheckConstraint(uuid7(), name="ck_hardware_compatibility_rules_id_uuid7"),
        sa.CheckConstraint(
            "compatibility_type IN ('native','backward_compatible','official_emulation')",
            name="ck_hardware_compatibility_rules_type",
        ),
        sa.CheckConstraint(
            "scope IN ('full','partial','selected_titles')",
            name="ck_hardware_compatibility_rules_scope",
        ),
        sa.UniqueConstraint(
            "source_hardware_model_id",
            "target_platform_id",
            "compatibility_type",
            "scope",
            name="uq_hardware_compatibility_rules_identity",
        ),
    )
    op.create_index(
        "ix_hardware_compatibility_rules_source",
        "hardware_compatibility_rules",
        ["source_hardware_model_id"],
    )
    op.create_index(
        "ix_hardware_compatibility_rules_target",
        "hardware_compatibility_rules",
        ["target_platform_id"],
    )
    op.create_table(
        "compatibility_rule_releases",
        sa.Column(
            "compatibility_rule_id",
            sa.Text(),
            sa.ForeignKey("hardware_compatibility_rules.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "release_id",
            sa.Text(),
            sa.ForeignKey("releases.id", ondelete="RESTRICT"),
            primary_key=True,
        ),
        sa.Column("support_level", sa.Text(), nullable=False),
        sa.Column("notes", sa.Text()),
        sa.CheckConstraint(
            "support_level IN ('full','partial')", name="ck_compatibility_rule_releases_support"
        ),
    )
    op.create_index(
        "ix_compatibility_rule_releases_release_id", "compatibility_rule_releases", ["release_id"]
    )

    op.create_table(
        "game_requirement_groups",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column(
            "release_id",
            sa.Text(),
            sa.ForeignKey("releases.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("group_operator", sa.Text(), nullable=False),
        sa.Column("mandatory", sa.Boolean(), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.Text(), nullable=False),
        sa.CheckConstraint(uuid7(), name="ck_game_requirement_groups_id_uuid7"),
        sa.CheckConstraint(
            "group_operator IN ('all_of','any_of')", name="ck_game_requirement_groups_operator"
        ),
        sa.CheckConstraint("mandatory IN (0,1)", name="ck_game_requirement_groups_mandatory"),
    )
    op.create_index(
        "ix_game_requirement_groups_release_id", "game_requirement_groups", ["release_id"]
    )
    op.create_index(
        "ix_game_requirement_groups_mandatory", "game_requirement_groups", ["mandatory"]
    )
    op.create_table(
        "game_hardware_requirements",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column(
            "group_id",
            sa.Text(),
            sa.ForeignKey("game_requirement_groups.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "hardware_model_id", sa.Text(), sa.ForeignKey("hardware_models.id", ondelete="RESTRICT")
        ),
        sa.Column(
            "accessory_model_id",
            sa.Text(),
            sa.ForeignKey("accessory_models.id", ondelete="RESTRICT"),
        ),
        sa.Column("capability_code", sa.Text()),
        sa.Column(
            "capability_provider_company_id",
            sa.Text(),
            sa.ForeignKey("companies.id", ondelete="RESTRICT"),
        ),
        sa.Column(
            "capability_platform_id", sa.Text(), sa.ForeignKey("platforms.id", ondelete="RESTRICT")
        ),
        sa.Column("minimum_quantity", sa.Integer(), server_default="1", nullable=False),
        sa.Column("minimum_value", sa.Integer()),
        sa.Column("notes", sa.Text()),
        sa.CheckConstraint(uuid7(), name="ck_game_hardware_requirements_id_uuid7"),
        sa.CheckConstraint(
            "(hardware_model_id IS NOT NULL)+(accessory_model_id IS NOT NULL)+(capability_code IS NOT NULL)=1",
            name="ck_game_hardware_requirements_one_target",
        ),
        sa.CheckConstraint(
            "capability_code IS NOT NULL OR (capability_provider_company_id IS NULL AND capability_platform_id IS NULL)",
            name="ck_game_hardware_requirements_capability_context",
        ),
        sa.CheckConstraint(
            "capability_code IS NULL OR capability_code IN ('storage_gb','network_access','active_subscription','online_account','other')",
            name="ck_game_hardware_requirements_capability_code",
        ),
        sa.CheckConstraint(
            "minimum_quantity>0 AND (minimum_value IS NULL OR minimum_value>=0)",
            name="ck_game_hardware_requirements_minimums",
        ),
    )
    for column in (
        "group_id",
        "hardware_model_id",
        "accessory_model_id",
        "capability_code",
        "capability_provider_company_id",
        "capability_platform_id",
    ):
        op.create_index(
            f"ix_game_hardware_requirements_{column}", "game_hardware_requirements", [column]
        )

    op.create_table(
        "personal_playability",
        sa.Column(
            "release_id",
            sa.Text(),
            sa.ForeignKey("releases.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("playable_now", sa.Boolean()),
        sa.Column("compatibility_level", sa.Text()),
        sa.Column("missing_requirements_json", sa.Text()),
        sa.Column("state", sa.Text(), nullable=False),
        sa.Column("rule_version", sa.Text()),
        sa.Column("input_version", sa.Text()),
        sa.Column("calculated_at", sa.Text()),
        sa.Column("stale_since", sa.Text()),
        sa.Column("last_error_redacted", sa.Text()),
        sa.CheckConstraint(
            "playable_now IS NULL OR playable_now IN (0,1)", name="ck_personal_playability_playable"
        ),
        sa.CheckConstraint(
            "compatibility_level IS NULL OR compatibility_level IN ('full','partial','none','unknown')",
            name="ck_personal_playability_level",
        ),
        sa.CheckConstraint(
            "missing_requirements_json IS NULL OR json_valid(missing_requirements_json)",
            name="ck_personal_playability_json",
        ),
        sa.CheckConstraint(
            "state IN ('dirty','recalculating','current','stale','failed')",
            name="ck_personal_playability_state",
        ),
        sa.CheckConstraint(
            "state<>'current' OR (calculated_at IS NOT NULL AND rule_version IS NOT NULL AND input_version IS NOT NULL AND playable_now IS NOT NULL AND compatibility_level IS NOT NULL)",
            name="ck_personal_playability_current",
        ),
    )
    op.create_index("ix_personal_playability_state", "personal_playability", ["state"])
    op.create_index(
        "ix_personal_playability_playable_now", "personal_playability", ["playable_now"]
    )
    op.execute(
        "UPDATE schema_metadata SET schema_version='0007_hardware_and_playability', updated_at=strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id=1"
    )


def downgrade() -> None:
    personal_tables = (
        "personal_hardware_units",
        "personal_accessory_units",
        "personal_capabilities",
    )
    if any(
        op.get_bind().execute(sa.text(f"SELECT count(*) FROM {table}")).scalar_one()
        for table in personal_tables
    ):
        raise RuntimeError(
            "0007 downgrade requires explicit backup/export and empty personal hardware data"
        )
    for table in (
        "personal_playability",
        "game_hardware_requirements",
        "game_requirement_groups",
        "compatibility_rule_releases",
        "hardware_compatibility_rules",
        "personal_capabilities",
        "personal_accessory_units",
        "accessory_platforms",
        "accessory_models",
        "personal_hardware_units",
        "hardware_model_external_ids",
        "hardware_models",
    ):
        op.drop_table(table)
    op.execute(
        "UPDATE schema_metadata SET schema_version='0006_personal_collection', updated_at=strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id=1"
    )

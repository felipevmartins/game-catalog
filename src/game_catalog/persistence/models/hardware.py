"""Hardware, requirements and calculated playability mappings."""

from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from game_catalog.persistence.base import Base


class HardwareModel(Base):
    __tablename__ = "hardware_models"
    id: Mapped[str] = mapped_column(Text, primary_key=True)
    platform_id: Mapped[str | None] = mapped_column(Text, ForeignKey("platforms.id"))
    manufacturer_id: Mapped[str | None] = mapped_column(Text, ForeignKey("manufacturers.id"))
    name: Mapped[str] = mapped_column(Text)
    normalized_name: Mapped[str] = mapped_column(Text)
    model_code: Mapped[str | None] = mapped_column(Text)
    hardware_type: Mapped[str] = mapped_column(Text)
    introduced_year: Mapped[int | None] = mapped_column(Integer)
    discontinued_year: Mapped[int | None] = mapped_column(Integer)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[str] = mapped_column(Text)
    deleted_at: Mapped[str | None] = mapped_column(Text)


class HardwareModelExternalId(Base):
    __tablename__ = "hardware_model_external_ids"
    id: Mapped[str] = mapped_column(Text, primary_key=True)
    hardware_model_id: Mapped[str] = mapped_column(Text, ForeignKey("hardware_models.id"))
    source_id: Mapped[str] = mapped_column(Text, ForeignKey("sources.id"))
    external_id: Mapped[str] = mapped_column(Text)
    context: Mapped[str] = mapped_column(Text, default="global", server_default="global")
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")
    created_at: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[str] = mapped_column(Text)


class PersonalHardwareUnit(Base):
    __tablename__ = "personal_hardware_units"
    id: Mapped[str] = mapped_column(Text, primary_key=True)
    hardware_model_id: Mapped[str] = mapped_column(Text, ForeignKey("hardware_models.id"))
    ownership_status: Mapped[str] = mapped_column(Text)
    working_status: Mapped[str] = mapped_column(Text)
    serial_number: Mapped[str | None] = mapped_column(Text)
    nickname: Mapped[str | None] = mapped_column(Text)
    storage_capacity_gb: Mapped[int | None] = mapped_column(Integer)
    acquisition_date: Mapped[str | None] = mapped_column(Text)
    purchase_amount_minor: Mapped[int | None] = mapped_column(Integer)
    purchase_currency_code: Mapped[str | None] = mapped_column(Text)
    sale_amount_minor: Mapped[int | None] = mapped_column(Integer)
    sale_currency_code: Mapped[str | None] = mapped_column(Text)
    sale_date: Mapped[str | None] = mapped_column(Text)
    acquired_from: Mapped[str | None] = mapped_column(Text)
    location: Mapped[str | None] = mapped_column(Text)
    private_notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[str] = mapped_column(Text)


class AccessoryModel(Base):
    __tablename__ = "accessory_models"
    id: Mapped[str] = mapped_column(Text, primary_key=True)
    manufacturer_id: Mapped[str | None] = mapped_column(Text, ForeignKey("manufacturers.id"))
    name: Mapped[str] = mapped_column(Text)
    normalized_name: Mapped[str] = mapped_column(Text)
    accessory_type: Mapped[str] = mapped_column(Text)
    model_code: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[str] = mapped_column(Text)
    deleted_at: Mapped[str | None] = mapped_column(Text)


class AccessoryPlatform(Base):
    __tablename__ = "accessory_platforms"
    accessory_model_id: Mapped[str] = mapped_column(
        Text, ForeignKey("accessory_models.id"), primary_key=True
    )
    platform_id: Mapped[str] = mapped_column(Text, ForeignKey("platforms.id"), primary_key=True)
    support_level: Mapped[str] = mapped_column(Text)
    required_adapter_model_id: Mapped[str | None] = mapped_column(
        Text, ForeignKey("accessory_models.id")
    )
    notes: Mapped[str | None] = mapped_column(Text)


class PersonalAccessoryUnit(Base):
    __tablename__ = "personal_accessory_units"
    id: Mapped[str] = mapped_column(Text, primary_key=True)
    accessory_model_id: Mapped[str] = mapped_column(Text, ForeignKey("accessory_models.id"))
    ownership_status: Mapped[str] = mapped_column(Text)
    working_status: Mapped[str] = mapped_column(Text)
    serial_number: Mapped[str | None] = mapped_column(Text)
    acquisition_date: Mapped[str | None] = mapped_column(Text)
    purchase_amount_minor: Mapped[int | None] = mapped_column(Integer)
    purchase_currency_code: Mapped[str | None] = mapped_column(Text)
    sale_amount_minor: Mapped[int | None] = mapped_column(Integer)
    sale_currency_code: Mapped[str | None] = mapped_column(Text)
    sale_date: Mapped[str | None] = mapped_column(Text)
    location: Mapped[str | None] = mapped_column(Text)
    private_notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[str] = mapped_column(Text)


class PersonalCapability(Base):
    __tablename__ = "personal_capabilities"
    id: Mapped[str] = mapped_column(Text, primary_key=True)
    capability_code: Mapped[str] = mapped_column(Text)
    provider_company_id: Mapped[str | None] = mapped_column(Text, ForeignKey("companies.id"))
    platform_id: Mapped[str | None] = mapped_column(Text, ForeignKey("platforms.id"))
    status: Mapped[str] = mapped_column(Text)
    valid_until: Mapped[str | None] = mapped_column(Text)
    private_notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[str] = mapped_column(Text)


class HardwareCompatibilityRule(Base):
    __tablename__ = "hardware_compatibility_rules"
    id: Mapped[str] = mapped_column(Text, primary_key=True)
    source_hardware_model_id: Mapped[str] = mapped_column(Text, ForeignKey("hardware_models.id"))
    target_platform_id: Mapped[str] = mapped_column(Text, ForeignKey("platforms.id"))
    compatibility_type: Mapped[str] = mapped_column(Text)
    scope: Mapped[str] = mapped_column(Text)
    source_reference_id: Mapped[str | None] = mapped_column(
        Text, ForeignKey("source_references.id")
    )
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[str] = mapped_column(Text)


class CompatibilityRuleRelease(Base):
    __tablename__ = "compatibility_rule_releases"
    compatibility_rule_id: Mapped[str] = mapped_column(
        Text, ForeignKey("hardware_compatibility_rules.id"), primary_key=True
    )
    release_id: Mapped[str] = mapped_column(Text, ForeignKey("releases.id"), primary_key=True)
    support_level: Mapped[str] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)


class GameRequirementGroup(Base):
    __tablename__ = "game_requirement_groups"
    id: Mapped[str] = mapped_column(Text, primary_key=True)
    release_id: Mapped[str] = mapped_column(Text, ForeignKey("releases.id"))
    group_operator: Mapped[str] = mapped_column(Text)
    mandatory: Mapped[bool] = mapped_column(Boolean)
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[str] = mapped_column(Text)


class GameHardwareRequirement(Base):
    __tablename__ = "game_hardware_requirements"
    id: Mapped[str] = mapped_column(Text, primary_key=True)
    group_id: Mapped[str] = mapped_column(Text, ForeignKey("game_requirement_groups.id"))
    hardware_model_id: Mapped[str | None] = mapped_column(Text, ForeignKey("hardware_models.id"))
    accessory_model_id: Mapped[str | None] = mapped_column(Text, ForeignKey("accessory_models.id"))
    capability_code: Mapped[str | None] = mapped_column(Text)
    capability_provider_company_id: Mapped[str | None] = mapped_column(
        Text, ForeignKey("companies.id")
    )
    capability_platform_id: Mapped[str | None] = mapped_column(Text, ForeignKey("platforms.id"))
    minimum_quantity: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    minimum_value: Mapped[int | None] = mapped_column(Integer)
    notes: Mapped[str | None] = mapped_column(Text)


class PersonalPlayability(Base):
    __tablename__ = "personal_playability"
    release_id: Mapped[str] = mapped_column(Text, ForeignKey("releases.id"), primary_key=True)
    playable_now: Mapped[bool | None] = mapped_column(Boolean)
    compatibility_level: Mapped[str | None] = mapped_column(Text)
    missing_requirements_json: Mapped[str | None] = mapped_column(Text)
    state: Mapped[str] = mapped_column(Text)
    rule_version: Mapped[str | None] = mapped_column(Text)
    input_version: Mapped[str | None] = mapped_column(Text)
    calculated_at: Mapped[str | None] = mapped_column(Text)
    stale_since: Mapped[str | None] = mapped_column(Text)
    last_error_redacted: Mapped[str | None] = mapped_column(Text)

"""Catalog fact, availability and derived platform-lock mappings."""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column

from game_catalog.persistence.base import Base


class FranchiseOwnership(Base):
    __tablename__ = "franchise_ownerships"
    id: Mapped[str] = mapped_column(Text, primary_key=True)
    franchise_id: Mapped[str] = mapped_column(
        Text, ForeignKey("franchises.id", ondelete="RESTRICT")
    )
    owner_company_id: Mapped[str] = mapped_column(
        Text, ForeignKey("companies.id", ondelete="RESTRICT")
    )
    ownership_type: Mapped[str] = mapped_column(Text)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")
    valid_from_year: Mapped[int | None] = mapped_column(Integer)
    valid_from_month: Mapped[int | None] = mapped_column(Integer)
    valid_from_day: Mapped[int | None] = mapped_column(Integer)
    valid_from_precision: Mapped[str] = mapped_column(Text)
    valid_from_qualifier: Mapped[str | None] = mapped_column(Text)
    valid_to_year: Mapped[int | None] = mapped_column(Integer)
    valid_to_month: Mapped[int | None] = mapped_column(Integer)
    valid_to_day: Mapped[int | None] = mapped_column(Integer)
    valid_to_precision: Mapped[str] = mapped_column(Text)
    valid_to_qualifier: Mapped[str | None] = mapped_column(Text)
    source_reference_id: Mapped[str] = mapped_column(
        Text, ForeignKey("source_references.id", ondelete="RESTRICT")
    )
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[str] = mapped_column(Text)


class GameCompany(Base):
    __tablename__ = "game_companies"
    id: Mapped[str] = mapped_column(Text, primary_key=True)
    game_id: Mapped[str] = mapped_column(Text, ForeignKey("games.id", ondelete="RESTRICT"))
    edition_id: Mapped[str | None] = mapped_column(
        Text, ForeignKey("game_editions.id", ondelete="RESTRICT")
    )
    release_id: Mapped[str | None] = mapped_column(
        Text, ForeignKey("releases.id", ondelete="RESTRICT")
    )
    company_id: Mapped[str] = mapped_column(Text, ForeignKey("companies.id", ondelete="RESTRICT"))
    role: Mapped[str] = mapped_column(Text)
    source_reference_id: Mapped[str | None] = mapped_column(
        Text, ForeignKey("source_references.id", ondelete="RESTRICT")
    )
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[str] = mapped_column(Text)


class GameScore(Base):
    __tablename__ = "game_scores"
    id: Mapped[str] = mapped_column(Text, primary_key=True)
    release_id: Mapped[str] = mapped_column(Text, ForeignKey("releases.id", ondelete="RESTRICT"))
    source_id: Mapped[str] = mapped_column(Text, ForeignKey("sources.id", ondelete="RESTRICT"))
    score_value: Mapped[Decimal | None] = mapped_column(Numeric)
    review_count: Mapped[int | None] = mapped_column(Integer)
    source_reference_id: Mapped[str] = mapped_column(
        Text, ForeignKey("source_references.id", ondelete="RESTRICT")
    )
    retrieved_at: Mapped[str] = mapped_column(Text)
    created_at: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[str] = mapped_column(Text)


class GamePrimaryScore(Base):
    __tablename__ = "game_primary_scores"
    game_id: Mapped[str] = mapped_column(
        Text, ForeignKey("games.id", ondelete="CASCADE"), primary_key=True
    )
    score_id: Mapped[str] = mapped_column(
        Text, ForeignKey("game_scores.id", ondelete="RESTRICT"), unique=True
    )
    selection_reason: Mapped[str] = mapped_column(Text)
    selected_at: Mapped[str] = mapped_column(Text)
    source_reference_id: Mapped[str | None] = mapped_column(
        Text, ForeignKey("source_references.id", ondelete="RESTRICT")
    )


class GameLength(Base):
    __tablename__ = "game_lengths"
    id: Mapped[str] = mapped_column(Text, primary_key=True)
    game_id: Mapped[str] = mapped_column(Text, ForeignKey("games.id", ondelete="RESTRICT"))
    source_id: Mapped[str] = mapped_column(Text, ForeignKey("sources.id", ondelete="RESTRICT"))
    main_story_minutes: Mapped[int | None] = mapped_column(Integer)
    main_extra_minutes: Mapped[int | None] = mapped_column(Integer)
    completionist_minutes: Mapped[int | None] = mapped_column(Integer)
    not_applicable: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")
    source_reference_id: Mapped[str] = mapped_column(
        Text, ForeignKey("source_references.id", ondelete="RESTRICT")
    )
    retrieved_at: Mapped[str] = mapped_column(Text)
    created_at: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[str] = mapped_column(Text)


class AvailabilityOffer(Base):
    __tablename__ = "availability_offers"
    id: Mapped[str] = mapped_column(Text, primary_key=True)
    release_id: Mapped[str] = mapped_column(Text, ForeignKey("releases.id", ondelete="RESTRICT"))
    access_platform_id: Mapped[str] = mapped_column(
        Text, ForeignKey("platforms.id", ondelete="RESTRICT")
    )
    provider_company_id: Mapped[str | None] = mapped_column(
        Text, ForeignKey("companies.id", ondelete="RESTRICT")
    )
    availability_type: Mapped[str] = mapped_column(Text)
    region_id: Mapped[str] = mapped_column(Text, ForeignKey("regions.id", ondelete="RESTRICT"))
    offer_identity_key: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text)
    is_current: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1")
    valid_from_year: Mapped[int | None] = mapped_column(Integer)
    valid_from_month: Mapped[int | None] = mapped_column(Integer)
    valid_from_day: Mapped[int | None] = mapped_column(Integer)
    valid_from_precision: Mapped[str] = mapped_column(Text)
    valid_from_qualifier: Mapped[str | None] = mapped_column(Text)
    valid_to_year: Mapped[int | None] = mapped_column(Integer)
    valid_to_month: Mapped[int | None] = mapped_column(Integer)
    valid_to_day: Mapped[int | None] = mapped_column(Integer)
    valid_to_precision: Mapped[str] = mapped_column(Text)
    valid_to_qualifier: Mapped[str | None] = mapped_column(Text)
    observed_at: Mapped[str] = mapped_column(Text)
    last_verified_at: Mapped[str] = mapped_column(Text)
    valid_until: Mapped[str | None] = mapped_column(Text)
    source_reference_id: Mapped[str] = mapped_column(
        Text, ForeignKey("source_references.id", ondelete="RESTRICT")
    )
    created_at: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[str] = mapped_column(Text)


class PlatformLockReason(Base):
    __tablename__ = "platform_lock_reasons"
    id: Mapped[str] = mapped_column(Text, primary_key=True)
    code: Mapped[str] = mapped_column(Text, unique=True)
    name: Mapped[str] = mapped_column(Text)
    description: Mapped[str] = mapped_column(Text)
    active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1")


class PlatformLockAssessment(Base):
    __tablename__ = "platform_lock_assessments"
    game_id: Mapped[str] = mapped_column(
        Text, ForeignKey("games.id", ondelete="CASCADE"), primary_key=True
    )
    locked: Mapped[bool | None] = mapped_column(Boolean)
    severity_level: Mapped[int | None] = mapped_column(Integer)
    justification: Mapped[str | None] = mapped_column(Text)
    minimum_official_hardware: Mapped[str | None] = mapped_column(Text)
    content_lost: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")
    state: Mapped[str] = mapped_column(Text)
    rule_version: Mapped[str | None] = mapped_column(Text)
    input_version: Mapped[str | None] = mapped_column(Text)
    calculated_at: Mapped[str | None] = mapped_column(Text)
    stale_since: Mapped[str | None] = mapped_column(Text)
    last_error_redacted: Mapped[str | None] = mapped_column(Text)


class GamePlatformLockReason(Base):
    __tablename__ = "game_platform_lock_reasons"
    game_id: Mapped[str] = mapped_column(
        Text, ForeignKey("platform_lock_assessments.game_id", ondelete="CASCADE"), primary_key=True
    )
    reason_id: Mapped[str] = mapped_column(
        Text, ForeignKey("platform_lock_reasons.id", ondelete="RESTRICT"), primary_key=True
    )
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")
    notes: Mapped[str | None] = mapped_column(Text)

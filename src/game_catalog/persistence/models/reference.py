"""Reference catalog models introduced by migration 0002."""

from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, Index, Integer, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from game_catalog.persistence.base import Base


class Region(Base):
    __tablename__ = "regions"
    __table_args__ = (
        Index("ix_regions_region_type", "region_type"),
        Index("ix_regions_parent_region_id", "parent_region_id"),
        Index("ix_regions_active", "active"),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    code: Mapped[str] = mapped_column(Text, unique=True)
    name: Mapped[str] = mapped_column(Text)
    region_type: Mapped[str] = mapped_column(Text)
    parent_region_id: Mapped[str | None] = mapped_column(
        Text, ForeignKey("regions.id", ondelete="RESTRICT")
    )
    active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1")
    created_at: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[str] = mapped_column(Text)


class Manufacturer(Base):
    __tablename__ = "manufacturers"
    __table_args__ = (
        Index("ix_manufacturers_normalized_name", "normalized_name"),
        Index(
            "uq_manufacturers_active_normalized_name",
            "normalized_name",
            unique=True,
            sqlite_where=text("deleted_at IS NULL"),
        ),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    name: Mapped[str] = mapped_column(Text)
    normalized_name: Mapped[str] = mapped_column(Text)
    country_code: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[str] = mapped_column(Text)
    deleted_at: Mapped[str | None] = mapped_column(Text)


class Ecosystem(Base):
    __tablename__ = "ecosystems"
    __table_args__ = (
        Index("ix_ecosystems_manufacturer_id", "manufacturer_id"),
        Index("ix_ecosystems_parent_ecosystem_id", "parent_ecosystem_id"),
        Index(
            "uq_ecosystems_active_normalized_name",
            "normalized_name",
            unique=True,
            sqlite_where=text("deleted_at IS NULL"),
        ),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    name: Mapped[str] = mapped_column(Text)
    normalized_name: Mapped[str] = mapped_column(Text)
    manufacturer_id: Mapped[str | None] = mapped_column(
        Text, ForeignKey("manufacturers.id", ondelete="RESTRICT")
    )
    ecosystem_type: Mapped[str] = mapped_column(Text)
    parent_ecosystem_id: Mapped[str | None] = mapped_column(
        Text, ForeignKey("ecosystems.id", ondelete="RESTRICT")
    )
    created_at: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[str] = mapped_column(Text)
    deleted_at: Mapped[str | None] = mapped_column(Text)


class Company(Base):
    __tablename__ = "companies"
    __table_args__ = (
        Index("ix_companies_normalized_name", "normalized_name"),
        Index("ix_companies_parent_company_id", "parent_company_id"),
        Index("ix_companies_company_type", "company_type"),
        Index(
            "uq_companies_active_identity",
            "normalized_name",
            text("COALESCE(country_code, '')"),
            unique=True,
            sqlite_where=text("deleted_at IS NULL"),
        ),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    name: Mapped[str] = mapped_column(Text)
    normalized_name: Mapped[str] = mapped_column(Text)
    company_type: Mapped[str] = mapped_column(Text)
    parent_company_id: Mapped[str | None] = mapped_column(
        Text, ForeignKey("companies.id", ondelete="RESTRICT")
    )
    country_code: Mapped[str | None] = mapped_column(Text)
    website: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[str] = mapped_column(Text)
    deleted_at: Mapped[str | None] = mapped_column(Text)


class Franchise(Base):
    __tablename__ = "franchises"
    __table_args__ = (
        Index("ix_franchises_parent_franchise_id", "parent_franchise_id"),
        Index("ix_franchises_status", "status"),
        Index(
            "uq_franchises_active_identity",
            "normalized_name",
            text("COALESCE(parent_franchise_id, '')"),
            unique=True,
            sqlite_where=text("deleted_at IS NULL"),
        ),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    name: Mapped[str] = mapped_column(Text)
    normalized_name: Mapped[str] = mapped_column(Text)
    parent_franchise_id: Mapped[str | None] = mapped_column(
        Text, ForeignKey("franchises.id", ondelete="RESTRICT")
    )
    status: Mapped[str] = mapped_column(Text)
    status_reason: Mapped[str | None] = mapped_column(Text)
    official_end_confirmed: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")
    created_at: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[str] = mapped_column(Text)
    deleted_at: Mapped[str | None] = mapped_column(Text)


class FranchiseEcosystem(Base):
    __tablename__ = "franchise_ecosystems"
    __table_args__ = (
        Index("ix_franchise_ecosystems_ecosystem_id", "ecosystem_id"),
        Index("ix_franchise_ecosystems_franchise_id", "franchise_id"),
        Index(
            "uq_franchise_ecosystems_identity",
            "franchise_id",
            "ecosystem_id",
            "association_type",
            text("COALESCE(valid_from_year, -1)"),
            unique=True,
        ),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    franchise_id: Mapped[str] = mapped_column(Text, ForeignKey("franchises.id", ondelete="CASCADE"))
    ecosystem_id: Mapped[str] = mapped_column(
        Text, ForeignKey("ecosystems.id", ondelete="RESTRICT")
    )
    association_type: Mapped[str] = mapped_column(Text)
    valid_from_year: Mapped[int | None] = mapped_column(Integer)
    valid_to_year: Mapped[int | None] = mapped_column(Integer)
    notes: Mapped[str | None] = mapped_column(Text)


class Platform(Base):
    __tablename__ = "platforms"
    __table_args__ = (
        Index("ix_platforms_manufacturer_id", "manufacturer_id"),
        Index("ix_platforms_ecosystem_id", "ecosystem_id"),
        Index("ix_platforms_platform_type", "platform_type"),
        Index(
            "uq_platforms_active_normalized_name",
            "normalized_name",
            unique=True,
            sqlite_where=text("deleted_at IS NULL"),
        ),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    name: Mapped[str] = mapped_column(Text)
    normalized_name: Mapped[str] = mapped_column(Text)
    manufacturer_id: Mapped[str | None] = mapped_column(
        Text, ForeignKey("manufacturers.id", ondelete="RESTRICT")
    )
    ecosystem_id: Mapped[str | None] = mapped_column(
        Text, ForeignKey("ecosystems.id", ondelete="RESTRICT")
    )
    platform_type: Mapped[str] = mapped_column(Text)
    release_year: Mapped[int | None] = mapped_column(Integer)
    discontinuation_year: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[str] = mapped_column(Text)
    deleted_at: Mapped[str | None] = mapped_column(Text)

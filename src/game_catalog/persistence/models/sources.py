"""Source provenance and external identifier mappings."""

from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from game_catalog.persistence.base import Base


class Source(Base):
    __tablename__ = "sources"
    id: Mapped[str] = mapped_column(Text, primary_key=True)
    code: Mapped[str] = mapped_column(Text, unique=True)
    name: Mapped[str] = mapped_column(Text)
    source_type: Mapped[str] = mapped_column(Text)
    integration_type: Mapped[str] = mapped_column(Text)
    base_url: Mapped[str | None] = mapped_column(Text)
    priority: Mapped[int] = mapped_column(Integer)
    default_confidence: Mapped[str] = mapped_column(Text)
    enabled: Mapped[bool] = mapped_column(Boolean)
    credential_required: Mapped[bool] = mapped_column(Boolean)
    terms_url: Mapped[str | None] = mapped_column(Text)
    terms_reviewed_at: Mapped[str | None] = mapped_column(Text)
    contract_version: Mapped[str | None] = mapped_column(Text)
    license_name: Mapped[str | None] = mapped_column(Text)
    attribution_text: Mapped[str | None] = mapped_column(Text)
    redistribution_policy: Mapped[str] = mapped_column(Text)
    default_ttl_days: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[str] = mapped_column(Text)


class SourceReference(Base):
    __tablename__ = "source_references"
    id: Mapped[str] = mapped_column(Text, primary_key=True)
    source_id: Mapped[str] = mapped_column(Text, ForeignKey("sources.id", ondelete="RESTRICT"))
    source_record_id: Mapped[str | None] = mapped_column(Text)
    source_url: Mapped[str | None] = mapped_column(Text)
    retrieved_at: Mapped[str] = mapped_column(Text)
    verified_at: Mapped[str | None] = mapped_column(Text)
    valid_until: Mapped[str | None] = mapped_column(Text)
    content_hash: Mapped[str | None] = mapped_column(Text)
    source_contract_version: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[str] = mapped_column(Text)


class RecordSourceLink(Base):
    __tablename__ = "record_source_links"
    id: Mapped[str] = mapped_column(Text, primary_key=True)
    entity_type: Mapped[str] = mapped_column(Text)
    entity_id: Mapped[str] = mapped_column(Text)
    source_reference_id: Mapped[str] = mapped_column(
        Text, ForeignKey("source_references.id", ondelete="CASCADE")
    )
    link_role: Mapped[str] = mapped_column(Text)
    created_at: Mapped[str] = mapped_column(Text)


class CatalogAssertion(Base):
    __tablename__ = "catalog_assertions"
    id: Mapped[str] = mapped_column(Text, primary_key=True)
    entity_type: Mapped[str] = mapped_column(Text)
    entity_id: Mapped[str] = mapped_column(Text)
    field_name: Mapped[str] = mapped_column(Text)
    value_json: Mapped[str] = mapped_column(Text)
    raw_value_json: Mapped[str | None] = mapped_column(Text)
    source_reference_id: Mapped[str] = mapped_column(
        Text, ForeignKey("source_references.id", ondelete="RESTRICT")
    )
    confidence: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text)
    is_manual_override: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")
    observed_at: Mapped[str] = mapped_column(Text)
    last_verified_at: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[str] = mapped_column(Text)


class ExternalIdMixin:
    id: Mapped[str] = mapped_column(Text, primary_key=True)
    source_id: Mapped[str] = mapped_column(Text, ForeignKey("sources.id", ondelete="RESTRICT"))
    external_id: Mapped[str] = mapped_column(Text)
    context: Mapped[str] = mapped_column(Text, default="global", server_default="global")
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")
    created_at: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[str] = mapped_column(Text)


class GameExternalId(ExternalIdMixin, Base):
    __tablename__ = "game_external_ids"
    game_id: Mapped[str] = mapped_column(Text, ForeignKey("games.id", ondelete="CASCADE"))


class EditionExternalId(ExternalIdMixin, Base):
    __tablename__ = "edition_external_ids"
    edition_id: Mapped[str] = mapped_column(
        Text, ForeignKey("game_editions.id", ondelete="CASCADE")
    )


class ReleaseExternalId(ExternalIdMixin, Base):
    __tablename__ = "release_external_ids"
    release_id: Mapped[str] = mapped_column(Text, ForeignKey("releases.id", ondelete="CASCADE"))


class PlatformExternalId(ExternalIdMixin, Base):
    __tablename__ = "platform_external_ids"
    platform_id: Mapped[str] = mapped_column(Text, ForeignKey("platforms.id", ondelete="CASCADE"))


class CompanyExternalId(ExternalIdMixin, Base):
    __tablename__ = "company_external_ids"
    company_id: Mapped[str] = mapped_column(Text, ForeignKey("companies.id", ondelete="CASCADE"))


class FranchiseExternalId(ExternalIdMixin, Base):
    __tablename__ = "franchise_external_ids"
    franchise_id: Mapped[str] = mapped_column(Text, ForeignKey("franchises.id", ondelete="CASCADE"))


class ProductExternalId(ExternalIdMixin, Base):
    __tablename__ = "product_external_ids"
    product_id: Mapped[str] = mapped_column(Text, ForeignKey("products.id", ondelete="CASCADE"))

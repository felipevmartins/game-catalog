"""Canonical game identity model mappings."""

from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from game_catalog.persistence.base import Base


class Game(Base):
    __tablename__ = "games"
    id: Mapped[str] = mapped_column(Text, primary_key=True)
    canonical_title: Mapped[str] = mapped_column(Text)
    normalized_title: Mapped[str] = mapped_column(Text)
    franchise_id: Mapped[str | None] = mapped_column(
        Text, ForeignKey("franchises.id", ondelete="RESTRICT")
    )
    game_type: Mapped[str] = mapped_column(Text)
    campaign_focus: Mapped[str] = mapped_column(Text)
    online_only: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")
    regional_only: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")
    historically_relevant: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")
    collector_relevant: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[str] = mapped_column(Text)
    deleted_at: Mapped[str | None] = mapped_column(Text)


class GameEdition(Base):
    __tablename__ = "game_editions"
    id: Mapped[str] = mapped_column(Text, primary_key=True)
    game_id: Mapped[str] = mapped_column(Text, ForeignKey("games.id", ondelete="RESTRICT"))
    identity_discriminator: Mapped[str] = mapped_column(Text)
    name: Mapped[str] = mapped_column(Text)
    normalized_name: Mapped[str] = mapped_column(Text)
    edition_type: Mapped[str] = mapped_column(Text)
    is_definitive: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[str] = mapped_column(Text)
    deleted_at: Mapped[str | None] = mapped_column(Text)


class Release(Base):
    __tablename__ = "releases"
    id: Mapped[str] = mapped_column(Text, primary_key=True)
    edition_id: Mapped[str] = mapped_column(
        Text, ForeignKey("game_editions.id", ondelete="RESTRICT")
    )
    platform_id: Mapped[str] = mapped_column(Text, ForeignKey("platforms.id", ondelete="RESTRICT"))
    region_id: Mapped[str] = mapped_column(Text, ForeignKey("regions.id", ondelete="RESTRICT"))
    release_type: Mapped[str] = mapped_column(Text)
    identity_discriminator: Mapped[str] = mapped_column(Text)
    release_year: Mapped[int | None] = mapped_column(Integer)
    release_month: Mapped[int | None] = mapped_column(Integer)
    release_day: Mapped[int | None] = mapped_column(Integer)
    release_precision: Mapped[str] = mapped_column(Text)
    release_qualifier: Mapped[str | None] = mapped_column(Text)
    identity_key: Mapped[str] = mapped_column(Text)
    official: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1")
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[str] = mapped_column(Text)
    deleted_at: Mapped[str | None] = mapped_column(Text)


class Product(Base):
    __tablename__ = "products"
    id: Mapped[str] = mapped_column(Text, primary_key=True)
    release_id: Mapped[str] = mapped_column(Text, ForeignKey("releases.id", ondelete="RESTRICT"))
    product_type: Mapped[str] = mapped_column(Text)
    media_format: Mapped[str | None] = mapped_column(Text)
    store_company_id: Mapped[str | None] = mapped_column(
        Text, ForeignKey("companies.id", ondelete="RESTRICT")
    )
    sku: Mapped[str | None] = mapped_column(Text)
    region_id: Mapped[str | None] = mapped_column(
        Text, ForeignKey("regions.id", ondelete="RESTRICT")
    )
    display_name: Mapped[str | None] = mapped_column(Text)
    identity_discriminator: Mapped[str] = mapped_column(Text)
    identity_key: Mapped[str] = mapped_column(Text)
    created_at: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[str] = mapped_column(Text)
    deleted_at: Mapped[str | None] = mapped_column(Text)


class GameAlias(Base):
    __tablename__ = "game_aliases"
    id: Mapped[str] = mapped_column(Text, primary_key=True)
    game_id: Mapped[str] = mapped_column(Text, ForeignKey("games.id", ondelete="CASCADE"))
    alias: Mapped[str] = mapped_column(Text)
    normalized_alias: Mapped[str] = mapped_column(Text)
    alias_type: Mapped[str] = mapped_column(Text)
    language_code: Mapped[str | None] = mapped_column(Text)
    region_id: Mapped[str | None] = mapped_column(
        Text, ForeignKey("regions.id", ondelete="RESTRICT")
    )
    source_reference_id: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[str] = mapped_column(Text)


class GameRelation(Base):
    __tablename__ = "game_relations"
    id: Mapped[str] = mapped_column(Text, primary_key=True)
    source_game_id: Mapped[str] = mapped_column(Text, ForeignKey("games.id", ondelete="RESTRICT"))
    target_game_id: Mapped[str] = mapped_column(Text, ForeignKey("games.id", ondelete="RESTRICT"))
    relation_type: Mapped[str] = mapped_column(Text)
    confidence: Mapped[str] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[str] = mapped_column(Text)


class GameContent(Base):
    __tablename__ = "game_contents"
    id: Mapped[str] = mapped_column(Text, primary_key=True)
    parent_game_id: Mapped[str] = mapped_column(Text, ForeignKey("games.id", ondelete="RESTRICT"))
    identity_discriminator: Mapped[str] = mapped_column(Text)
    title: Mapped[str] = mapped_column(Text)
    normalized_title: Mapped[str] = mapped_column(Text)
    content_type: Mapped[str] = mapped_column(Text)
    requires_base_game: Mapped[bool] = mapped_column(Boolean)
    sequence_number: Mapped[int | None] = mapped_column(Integer)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[str] = mapped_column(Text)
    deleted_at: Mapped[str | None] = mapped_column(Text)

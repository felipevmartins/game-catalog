"""Private personal collection mappings."""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column

from game_catalog.persistence.base import Base


class PersonalCollectionItem(Base):
    __tablename__ = "personal_collection_items"
    id: Mapped[str] = mapped_column(Text, primary_key=True)
    game_id: Mapped[str] = mapped_column(Text, ForeignKey("games.id", ondelete="RESTRICT"))
    edition_id: Mapped[str | None] = mapped_column(
        Text, ForeignKey("game_editions.id", ondelete="RESTRICT")
    )
    release_id: Mapped[str | None] = mapped_column(
        Text, ForeignKey("releases.id", ondelete="RESTRICT")
    )
    product_id: Mapped[str | None] = mapped_column(
        Text, ForeignKey("products.id", ondelete="RESTRICT")
    )
    ownership_status: Mapped[str] = mapped_column(Text)
    ownership_format: Mapped[str] = mapped_column(Text)
    media_condition: Mapped[str | None] = mapped_column(Text)
    box_condition: Mapped[str | None] = mapped_column(Text)
    completeness: Mapped[str | None] = mapped_column(Text)
    acquisition_date: Mapped[str | None] = mapped_column(Text)
    purchase_amount_minor: Mapped[int | None] = mapped_column(Integer)
    purchase_currency_code: Mapped[str | None] = mapped_column(Text)
    acquired_from: Mapped[str | None] = mapped_column(Text)
    loaned_to: Mapped[str | None] = mapped_column(Text)
    loaned_at: Mapped[str | None] = mapped_column(Text)
    loan_due_date: Mapped[str | None] = mapped_column(Text)
    sale_date: Mapped[str | None] = mapped_column(Text)
    sale_amount_minor: Mapped[int | None] = mapped_column(Integer)
    sale_currency_code: Mapped[str | None] = mapped_column(Text)
    personal_score: Mapped[Decimal | None] = mapped_column(Numeric)
    played: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")
    completed: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")
    private_notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[str] = mapped_column(Text)

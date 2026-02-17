"""Restaurant model with PostGIS geography support."""

import uuid
from datetime import datetime

from geoalchemy2 import Geography
from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Restaurant(Base):
    __tablename__ = "restaurants"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    address: Mapped[str] = mapped_column(Text, nullable=False)
    location = mapped_column(
        Geography(geometry_type="POINT", srid=4326), nullable=False
    )
    google_place_id: Mapped[str | None] = mapped_column(
        String(300), unique=True, nullable=True
    )
    yelp_id: Mapped[str | None] = mapped_column(
        String(300), unique=True, nullable=True
    )
    slug: Mapped[str] = mapped_column(
        String(600), unique=True, nullable=False, index=True
    )

    has_dedicated_gf_menu: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false"
    )
    gf_item_count: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", index=True
    )
    gluten_mentioned_on_menu: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    menu_photos = relationship("MenuPhoto", back_populates="restaurant", lazy="selectin")
    menu_items = relationship("MenuItem", back_populates="restaurant", lazy="selectin")
    generated_gf_menus = relationship(
        "GeneratedGFMenu", back_populates="restaurant", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Restaurant(id={self.id}, name={self.name!r})>"

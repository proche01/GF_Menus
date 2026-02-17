"""Menu-related models: photos, items, and generated GF menus."""

import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class PhotoSource(str, PyEnum):
    GOOGLE = "google"
    YELP = "yelp"
    USER_UPLOAD = "user_upload"


class CrossContactRisk(str, PyEnum):
    NONE = "none"
    LOW = "low"
    HIGH = "high"


class MenuPhoto(Base):
    __tablename__ = "menu_photos"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    restaurant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("restaurants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source: Mapped[str] = mapped_column(
        Enum(PhotoSource, name="photo_source_enum", create_constraint=True),
        nullable=False,
    )
    s3_key: Mapped[str] = mapped_column(String(1000), nullable=False)
    photo_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    ocr_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    processed: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false"
    )
    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    restaurant = relationship("Restaurant", back_populates="menu_photos")
    menu_items = relationship("MenuItem", back_populates="source_photo")

    def __repr__(self) -> str:
        return f"<MenuPhoto(id={self.id}, source={self.source})>"


class MenuItem(Base):
    __tablename__ = "menu_items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    restaurant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("restaurants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_photo_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("menu_photos.id", ondelete="SET NULL"),
        nullable=True,
    )

    name: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    price: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)

    is_gluten_free: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false"
    )
    cross_contact_risk: Mapped[str] = mapped_column(
        Enum(CrossContactRisk, name="cross_contact_risk_enum", create_constraint=True),
        default=CrossContactRisk.HIGH,
        server_default="high",
    )
    gf_label_on_menu: Mapped[str | None] = mapped_column(String(100), nullable=True)
    confidence_score: Mapped[float] = mapped_column(
        Float, default=0.0, server_default="0.0"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    restaurant = relationship("Restaurant", back_populates="menu_items")
    source_photo = relationship("MenuPhoto", back_populates="menu_items")

    def __repr__(self) -> str:
        return f"<MenuItem(id={self.id}, name={self.name!r}, gf={self.is_gluten_free})>"


class GeneratedGFMenu(Base):
    __tablename__ = "generated_gf_menus"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    restaurant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("restaurants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sensitivity_profile: Mapped[str] = mapped_column(
        String(50), nullable=False, default="STRICT_CELIAC"
    )
    items: Mapped[dict] = mapped_column(JSON, nullable=False, default=list)
    strict_celiac_items: Mapped[dict | None] = mapped_column(
        JSON, nullable=True
    )
    item_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")

    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    restaurant = relationship("Restaurant", back_populates="generated_gf_menus")

    def __repr__(self) -> str:
        return (
            f"<GeneratedGFMenu(id={self.id}, "
            f"profile={self.sensitivity_profile}, count={self.item_count})>"
        )

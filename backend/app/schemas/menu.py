"""Pydantic schemas for menu-related request/response models."""

import uuid
from datetime import datetime

from pydantic import BaseModel


class MenuPhotoResponse(BaseModel):
    id: uuid.UUID
    restaurant_id: uuid.UUID
    source: str
    photo_url: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class MenuItemResponse(BaseModel):
    id: uuid.UUID
    restaurant_id: uuid.UUID
    name: str
    description: str | None = None
    price: float | None = None
    is_gluten_free: bool
    cross_contact_risk: str
    gf_label_on_menu: str | None = None
    confidence_score: float

    model_config = {"from_attributes": True}


class GeneratedGFMenuResponse(BaseModel):
    id: uuid.UUID
    restaurant_id: uuid.UUID
    sensitivity_profile: str
    items: list[MenuItemResponse]
    item_count: int
    generated_at: datetime

    model_config = {"from_attributes": True}


class MenuItemCreate(BaseModel):
    name: str
    description: str | None = None
    price: float | None = None
    is_gluten_free: bool = False
    cross_contact_risk: str = "high"
    gf_label_on_menu: str | None = None
    confidence_score: float = 0.0

"""Pydantic schemas for restaurant request/response models."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class RestaurantBase(BaseModel):
    name: str
    address: str
    latitude: float
    longitude: float


class RestaurantCreate(RestaurantBase):
    google_place_id: str | None = None
    yelp_id: str | None = None


class RestaurantResponse(RestaurantBase):
    id: uuid.UUID
    slug: str
    google_place_id: str | None = None
    yelp_id: str | None = None
    has_dedicated_gf_menu: bool = False
    gf_item_count: int = 0
    gluten_mentioned_on_menu: bool = False
    distance_km: float | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RestaurantListResponse(BaseModel):
    restaurants: list[RestaurantResponse]
    total: int
    page: int = 1
    page_size: int = 20


class RestaurantMapPin(BaseModel):
    id: uuid.UUID
    name: str
    latitude: float
    longitude: float
    gf_item_count: int
    has_dedicated_gf_menu: bool

    model_config = {"from_attributes": True}

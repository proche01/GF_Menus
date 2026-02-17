"""Pydantic schemas for search parameters."""

from enum import Enum

from pydantic import BaseModel, Field


class SortBy(str, Enum):
    DISTANCE = "distance"
    GF_ITEM_COUNT = "gf_item_count"


class SortOrder(str, Enum):
    ASC = "asc"
    DESC = "desc"


class RestaurantSearchQuery(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    radius_km: float = Field(default=10.0, ge=0.1, le=100.0)
    min_gf_items: int = Field(default=0, ge=0)
    has_dedicated_gf_menu: bool | None = None
    gluten_mentioned: bool | None = None
    sort_by: SortBy = SortBy.DISTANCE
    sort_order: SortOrder = SortOrder.ASC
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class MapBoundsQuery(BaseModel):
    north: float = Field(..., ge=-90, le=90)
    south: float = Field(..., ge=-90, le=90)
    east: float = Field(..., ge=-180, le=180)
    west: float = Field(..., ge=-180, le=180)

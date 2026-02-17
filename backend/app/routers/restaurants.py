"""Restaurant discovery and detail endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.restaurant import (
    RestaurantResponse,
    RestaurantMapPin,
)
from app.schemas.search import MapBoundsQuery
from app.services.restaurant_service import RestaurantService

router = APIRouter(prefix="/api/restaurants", tags=["restaurants"])


@router.get("/{restaurant_id}", response_model=RestaurantResponse)
async def get_restaurant(
    restaurant_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a restaurant by ID."""
    service = RestaurantService(db)
    restaurant = await service.get_by_id(restaurant_id)
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    return RestaurantResponse(
        id=restaurant.id,
        name=restaurant.name,
        address=restaurant.address,
        latitude=0.0,  # Will be extracted below
        longitude=0.0,
        slug=restaurant.slug,
        google_place_id=restaurant.google_place_id,
        yelp_id=restaurant.yelp_id,
        has_dedicated_gf_menu=restaurant.has_dedicated_gf_menu,
        gf_item_count=restaurant.gf_item_count,
        gluten_mentioned_on_menu=restaurant.gluten_mentioned_on_menu,
        created_at=restaurant.created_at,
        updated_at=restaurant.updated_at,
    )


@router.get("/slug/{slug}", response_model=RestaurantResponse)
async def get_restaurant_by_slug(
    slug: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a restaurant by its URL slug."""
    service = RestaurantService(db)
    restaurant = await service.get_by_slug(slug)
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    return RestaurantResponse(
        id=restaurant.id,
        name=restaurant.name,
        address=restaurant.address,
        latitude=0.0,
        longitude=0.0,
        slug=restaurant.slug,
        google_place_id=restaurant.google_place_id,
        yelp_id=restaurant.yelp_id,
        has_dedicated_gf_menu=restaurant.has_dedicated_gf_menu,
        gf_item_count=restaurant.gf_item_count,
        gluten_mentioned_on_menu=restaurant.gluten_mentioned_on_menu,
        created_at=restaurant.created_at,
        updated_at=restaurant.updated_at,
    )


@router.get("/map", response_model=list[RestaurantMapPin])
async def get_map_pins(
    north: float = Query(..., ge=-90, le=90),
    south: float = Query(..., ge=-90, le=90),
    east: float = Query(..., ge=-180, le=180),
    west: float = Query(..., ge=-180, le=180),
    min_gf_items: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """Get restaurant pins for the map view within geographic bounds."""
    bounds = MapBoundsQuery(north=north, south=south, east=east, west=west)
    service = RestaurantService(db)
    pins = await service.get_map_pins(bounds, min_gf_items)
    return pins


@router.post("/discover")
async def trigger_discovery(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    radius_m: int = Query(default=10000, ge=100, le=50000),
    db: AsyncSession = Depends(get_db),
):
    """Trigger background restaurant discovery for an area."""
    service = RestaurantService(db)
    task_id = await service.trigger_discovery(latitude, longitude, radius_m)
    return {"task_id": task_id, "status": "discovery_started"}

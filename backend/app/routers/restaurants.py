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


def _to_response(restaurant, latitude: float = 0.0, longitude: float = 0.0) -> RestaurantResponse:
    return RestaurantResponse(
        id=restaurant.id,
        name=restaurant.name,
        address=restaurant.address,
        latitude=latitude,
        longitude=longitude,
        slug=restaurant.slug,
        google_place_id=restaurant.google_place_id,
        yelp_id=restaurant.yelp_id,
        has_dedicated_gf_menu=restaurant.has_dedicated_gf_menu,
        gf_item_count=restaurant.gf_item_count,
        gluten_mentioned_on_menu=restaurant.gluten_mentioned_on_menu,
        created_at=restaurant.created_at,
        updated_at=restaurant.updated_at,
    )


# Static paths MUST be registered before /{restaurant_id} or FastAPI
# will try to parse "map" / "slug" / "discover" as UUIDs.


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
    return _to_response(restaurant)


@router.post("/discover")
async def trigger_discovery(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    radius_m: int = Query(default=1500, ge=100, le=50000),
    max_restaurants: int = Query(default=2, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
):
    """
    Trigger background restaurant discovery for an area.

    Defaults are intentionally conservative for free-tier API keys:
    small radius and a hard cap on how many restaurants enter the pipeline.
    """
    service = RestaurantService(db)
    task_id = await service.trigger_discovery(
        latitude, longitude, radius_m, max_restaurants=max_restaurants
    )
    return {
        "task_id": task_id,
        "status": "discovery_started",
        "radius_m": radius_m,
        "max_restaurants": max_restaurants,
    }


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
    return _to_response(restaurant)

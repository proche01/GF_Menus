"""Unified search with geo + filters + sorting."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.restaurant import RestaurantResponse, RestaurantListResponse
from app.services.search_service import SearchService

router = APIRouter(prefix="/api/search", tags=["search"])


@router.get("/restaurants", response_model=RestaurantListResponse)
async def search_restaurants(
    q: str | None = Query(default=None, description="Address or location text to geocode"),
    latitude: float | None = Query(default=None, ge=-90, le=90),
    longitude: float | None = Query(default=None, ge=-180, le=180),
    radius_km: float = Query(default=10.0, ge=0.1, le=100.0),
    min_gf_items: int = Query(default=0, ge=0),
    has_dedicated_gf_menu: bool | None = Query(default=None),
    gluten_mentioned: bool | None = Query(default=None),
    sort_by: str = Query(default="distance", regex="^(distance|gf_item_count)$"),
    sort_order: str = Query(default="asc", regex="^(asc|desc)$"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """
    Search for restaurants with optional text geocoding, geo filters, and sorting.

    Either provide `q` (address/location text) or `latitude`+`longitude`.
    If `q` is provided without coordinates, it will be geocoded automatically.
    """
    service = SearchService(db)
    results, total = await service.search_by_query(
        query=q,
        latitude=latitude,
        longitude=longitude,
        radius_km=radius_km,
        min_gf_items=min_gf_items,
        has_dedicated_gf_menu=has_dedicated_gf_menu,
        gluten_mentioned=gluten_mentioned,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size,
    )

    restaurants = []
    for row in results:
        r = row["restaurant"]
        restaurants.append(
            RestaurantResponse(
                id=r.id,
                name=r.name,
                address=r.address,
                latitude=0.0,
                longitude=0.0,
                slug=r.slug,
                google_place_id=r.google_place_id,
                yelp_id=r.yelp_id,
                has_dedicated_gf_menu=r.has_dedicated_gf_menu,
                gf_item_count=r.gf_item_count,
                gluten_mentioned_on_menu=r.gluten_mentioned_on_menu,
                distance_km=row.get("distance_km"),
                created_at=r.created_at,
                updated_at=r.updated_at,
            )
        )

    return RestaurantListResponse(
        restaurants=restaurants,
        total=total,
        page=page,
        page_size=page_size,
    )

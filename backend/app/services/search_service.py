"""Unified search service combining geo, filters, and geocoding."""

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.geocoding import GeocodingClient
from app.schemas.search import RestaurantSearchQuery
from app.services.restaurant_service import RestaurantService

logger = logging.getLogger(__name__)


class SearchService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.restaurant_service = RestaurantService(db)

    async def search_by_query(
        self,
        query: str | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
        radius_km: float = 10.0,
        min_gf_items: int = 0,
        has_dedicated_gf_menu: bool | None = None,
        gluten_mentioned: bool | None = None,
        sort_by: str = "distance",
        sort_order: str = "asc",
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[dict], int]:
        """
        Search for restaurants. If only a text query is provided,
        geocode it first to get coordinates.
        """
        # If we have a text query but no coordinates, geocode it
        if query and (latitude is None or longitude is None):
            geocoder = GeocodingClient()
            try:
                result = await geocoder.forward_geocode(query)
                if result:
                    latitude = result.latitude
                    longitude = result.longitude
                else:
                    return [], 0
            finally:
                await geocoder.close()

        if latitude is None or longitude is None:
            return [], 0

        params = RestaurantSearchQuery(
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

        return await self.restaurant_service.search(params)

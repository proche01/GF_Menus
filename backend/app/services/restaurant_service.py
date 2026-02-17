"""Restaurant service: CRUD, geo-search, and filtering logic."""

import uuid
import logging
from math import radians, cos

from sqlalchemy import select, func, text, and_, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.restaurant import Restaurant
from app.schemas.search import RestaurantSearchQuery, MapBoundsQuery

logger = logging.getLogger(__name__)


class RestaurantService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, restaurant_id: uuid.UUID) -> Restaurant | None:
        result = await self.db.execute(
            select(Restaurant).where(Restaurant.id == restaurant_id)
        )
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Restaurant | None:
        result = await self.db.execute(
            select(Restaurant).where(Restaurant.slug == slug)
        )
        return result.scalar_one_or_none()

    async def search(
        self, params: RestaurantSearchQuery
    ) -> tuple[list[dict], int]:
        """
        Search restaurants by location with filtering and sorting.
        Returns (list of restaurant dicts with distance, total count).
        """
        # PostGIS distance calculation in meters
        point = func.ST_SetSRID(
            func.ST_MakePoint(params.longitude, params.latitude), 4326
        )
        distance_col = func.ST_Distance(
            Restaurant.location, func.cast(point, func.Geography)
        ).label("distance_m")

        # Base query with distance
        query = select(Restaurant, distance_col)

        # Filter by radius
        radius_m = params.radius_km * 1000
        query = query.where(
            func.ST_DWithin(
                Restaurant.location,
                func.cast(point, func.Geography),
                radius_m,
            )
        )

        # Filter by min GF items
        if params.min_gf_items > 0:
            query = query.where(Restaurant.gf_item_count >= params.min_gf_items)

        # Filter by dedicated GF menu
        if params.has_dedicated_gf_menu is not None:
            query = query.where(
                Restaurant.has_dedicated_gf_menu == params.has_dedicated_gf_menu
            )

        # Filter by gluten mentioned
        if params.gluten_mentioned is not None:
            query = query.where(
                Restaurant.gluten_mentioned_on_menu == params.gluten_mentioned
            )

        # Count total (before pagination)
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Sorting
        if params.sort_by.value == "distance":
            order_col = distance_col
        else:
            order_col = Restaurant.gf_item_count

        if params.sort_order.value == "desc":
            query = query.order_by(order_col.desc())
        else:
            query = query.order_by(order_col.asc())

        # Pagination
        offset = (params.page - 1) * params.page_size
        query = query.offset(offset).limit(params.page_size)

        result = await self.db.execute(query)
        rows = result.all()

        restaurants = []
        for row in rows:
            restaurant = row[0]
            distance_m = row[1]
            restaurants.append({
                "restaurant": restaurant,
                "distance_km": round(distance_m / 1000, 2) if distance_m else None,
            })

        return restaurants, total

    async def get_map_pins(
        self, bounds: MapBoundsQuery, min_gf_items: int = 0
    ) -> list[dict]:
        """Get restaurant map pins within geographic bounds."""
        # Build bounding box polygon
        bbox = func.ST_MakeEnvelope(
            bounds.west, bounds.south, bounds.east, bounds.north, 4326
        )

        query = select(Restaurant).where(
            func.ST_Within(
                func.cast(Restaurant.location, func.Geometry),
                bbox,
            )
        )

        if min_gf_items > 0:
            query = query.where(Restaurant.gf_item_count >= min_gf_items)

        query = query.limit(200)  # Cap pins for performance

        result = await self.db.execute(query)
        restaurants = result.scalars().all()

        return [
            {
                "id": str(r.id),
                "name": r.name,
                "latitude": await self._extract_lat(r),
                "longitude": await self._extract_lng(r),
                "gf_item_count": r.gf_item_count,
                "has_dedicated_gf_menu": r.has_dedicated_gf_menu,
            }
            for r in restaurants
        ]

    async def _extract_lat(self, restaurant: Restaurant) -> float:
        """Extract latitude from PostGIS geography column."""
        result = await self.db.execute(
            select(func.ST_Y(func.cast(restaurant.location, func.Geometry)))
        )
        return result.scalar() or 0.0

    async def _extract_lng(self, restaurant: Restaurant) -> float:
        """Extract longitude from PostGIS geography column."""
        result = await self.db.execute(
            select(func.ST_X(func.cast(restaurant.location, func.Geometry)))
        )
        return result.scalar() or 0.0

    async def trigger_discovery(
        self, latitude: float, longitude: float, radius_m: int = 10000
    ) -> str:
        """Trigger the background discovery pipeline. Returns the Celery task ID."""
        from app.workers.tasks.discover import discover_restaurants_task

        task = discover_restaurants_task.delay(latitude, longitude, radius_m)
        return task.id

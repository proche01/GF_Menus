"""Restaurant service: CRUD, geo-search, and filtering logic."""

import uuid
import logging

from geoalchemy2 import Geography, Geometry
from sqlalchemy import cast, select, func
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
        # PostGIS geography point for distance calculations
        point = cast(
            func.ST_SetSRID(
                func.ST_MakePoint(params.longitude, params.latitude), 4326
            ),
            Geography,
        )
        distance_col = func.ST_Distance(Restaurant.location, point).label("distance_m")
        lat_col = func.ST_Y(cast(Restaurant.location, Geometry)).label("latitude")
        lng_col = func.ST_X(cast(Restaurant.location, Geometry)).label("longitude")

        query = select(Restaurant, distance_col, lat_col, lng_col)

        radius_m = params.radius_km * 1000
        query = query.where(func.ST_DWithin(Restaurant.location, point, radius_m))

        if params.min_gf_items > 0:
            query = query.where(Restaurant.gf_item_count >= params.min_gf_items)

        if params.has_dedicated_gf_menu is not None:
            query = query.where(
                Restaurant.has_dedicated_gf_menu == params.has_dedicated_gf_menu
            )

        if params.gluten_mentioned is not None:
            query = query.where(
                Restaurant.gluten_mentioned_on_menu == params.gluten_mentioned
            )

        count_query = select(func.count()).select_from(
            query.with_only_columns(Restaurant.id).order_by(None).subquery()
        )
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        if params.sort_by.value == "distance":
            order_col = distance_col
        else:
            order_col = Restaurant.gf_item_count

        if params.sort_order.value == "desc":
            query = query.order_by(order_col.desc())
        else:
            query = query.order_by(order_col.asc())

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
                "latitude": float(row[2]) if row[2] is not None else 0.0,
                "longitude": float(row[3]) if row[3] is not None else 0.0,
            })

        return restaurants, total

    async def get_map_pins(
        self, bounds: MapBoundsQuery, min_gf_items: int = 0
    ) -> list[dict]:
        """Get restaurant map pins within geographic bounds."""
        bbox = func.ST_MakeEnvelope(
            bounds.west, bounds.south, bounds.east, bounds.north, 4326
        )
        lat_col = func.ST_Y(cast(Restaurant.location, Geometry)).label("latitude")
        lng_col = func.ST_X(cast(Restaurant.location, Geometry)).label("longitude")

        query = select(Restaurant, lat_col, lng_col).where(
            func.ST_Within(cast(Restaurant.location, Geometry), bbox)
        )

        if min_gf_items > 0:
            query = query.where(Restaurant.gf_item_count >= min_gf_items)

        query = query.limit(200)

        result = await self.db.execute(query)
        rows = result.all()

        return [
            {
                "id": str(row[0].id),
                "name": row[0].name,
                "latitude": float(row[1]) if row[1] is not None else 0.0,
                "longitude": float(row[2]) if row[2] is not None else 0.0,
                "gf_item_count": row[0].gf_item_count,
                "has_dedicated_gf_menu": row[0].has_dedicated_gf_menu,
            }
            for row in rows
        ]

    async def trigger_discovery(
        self,
        latitude: float,
        longitude: float,
        radius_m: int = 1500,
        max_restaurants: int | None = None,
    ) -> str:
        """Trigger the background discovery pipeline. Returns the Celery task ID."""
        from app.config import get_settings
        from app.workers.tasks.discover import discover_restaurants_task

        settings = get_settings()
        cap = (
            max_restaurants
            if max_restaurants is not None
            else settings.discovery_max_restaurants
        )
        task = discover_restaurants_task.delay(latitude, longitude, radius_m, cap)
        return task.id

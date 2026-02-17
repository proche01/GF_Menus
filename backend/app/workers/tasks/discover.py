"""
Task: Discover restaurants in a geographic area via Google Places + Yelp.

Finds new restaurants and upserts them into the database, then chains
to the photo scraping task for each new restaurant.
"""

import asyncio
import logging
import re
import uuid

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.workers.celery_app import celery_app
from app.config import get_settings
from app.models.restaurant import Restaurant

logger = logging.getLogger(__name__)


def _slugify(name: str, address: str) -> str:
    """Generate a URL-friendly slug from restaurant name + city."""
    raw = f"{name} {address.split(',')[0] if ',' in address else address}"
    slug = re.sub(r"[^\w\s-]", "", raw.lower())
    slug = re.sub(r"[\s_]+", "-", slug).strip("-")
    return slug[:600]


def _get_sync_session():
    """Create a sync SQLAlchemy session for Celery tasks."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    settings = get_settings()
    engine = create_engine(settings.database_url_sync, pool_pre_ping=True)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def discover_restaurants_task(self, latitude: float, longitude: float, radius_m: int = 10000):
    """
    Discover restaurants near a location and store them in the database.
    Chains to scrape_photos for each newly discovered restaurant.
    """
    logger.info(
        "Discovering restaurants near (%s, %s) radius=%dm",
        latitude, longitude, radius_m,
    )

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        new_restaurant_ids = loop.run_until_complete(
            _discover_and_store(latitude, longitude, radius_m)
        )
        logger.info("Discovered %d new restaurants", len(new_restaurant_ids))

        # Chain to photo scraping for each new restaurant
        from app.workers.tasks.scrape_photos import scrape_restaurant_photos_task

        for rest_id in new_restaurant_ids:
            scrape_restaurant_photos_task.delay(str(rest_id))

        return {"new_restaurants": len(new_restaurant_ids), "ids": [str(r) for r in new_restaurant_ids]}

    except Exception as exc:
        logger.error("Discovery failed: %s", exc)
        raise self.retry(exc=exc)
    finally:
        loop.close()


async def _discover_and_store(
    latitude: float, longitude: float, radius_m: int
) -> list[uuid.UUID]:
    """Fetch from Google + Yelp and upsert into the DB."""
    from app.integrations.google_places import GooglePlacesClient
    from app.integrations.yelp import YelpClient

    new_ids: list[uuid.UUID] = []
    session = _get_sync_session()

    try:
        # Google Places
        google_client = GooglePlacesClient()
        try:
            results, _ = await google_client.nearby_search(
                latitude, longitude, radius_m
            )
            for place in results:
                existing = session.execute(
                    select(Restaurant).where(
                        Restaurant.google_place_id == place.place_id
                    )
                ).scalar_one_or_none()

                if existing is None:
                    restaurant = Restaurant(
                        name=place.name,
                        address=place.address,
                        location=f"SRID=4326;POINT({place.longitude} {place.latitude})",
                        google_place_id=place.place_id,
                        slug=_slugify(place.name, place.address),
                    )
                    session.add(restaurant)
                    session.flush()
                    new_ids.append(restaurant.id)
        finally:
            await google_client.close()

        # Yelp
        yelp_client = YelpClient()
        try:
            businesses = await yelp_client.search_businesses(
                latitude, longitude, radius_m
            )
            for biz in businesses:
                existing = session.execute(
                    select(Restaurant).where(Restaurant.yelp_id == biz.yelp_id)
                ).scalar_one_or_none()

                if existing is None:
                    # Check if same restaurant was already added via Google
                    name_match = session.execute(
                        select(Restaurant).where(
                            Restaurant.name == biz.name,
                            Restaurant.yelp_id.is_(None),
                        )
                    ).scalar_one_or_none()

                    if name_match:
                        name_match.yelp_id = biz.yelp_id
                    else:
                        restaurant = Restaurant(
                            name=biz.name,
                            address=biz.address,
                            location=f"SRID=4326;POINT({biz.longitude} {biz.latitude})",
                            yelp_id=biz.yelp_id,
                            slug=_slugify(biz.name, biz.address),
                        )
                        session.add(restaurant)
                        session.flush()
                        new_ids.append(restaurant.id)
        finally:
            await yelp_client.close()

        session.commit()

    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

    return new_ids

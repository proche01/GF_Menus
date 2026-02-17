"""
Task: Scrape menu photos for a restaurant from Google Places and Yelp.

Downloads photos and stores them in S3/MinIO, then chains to OCR processing.
"""

import asyncio
import logging
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.workers.celery_app import celery_app
from app.models.restaurant import Restaurant
from app.models.menu import MenuPhoto, PhotoSource
from app.services.storage import StorageService

logger = logging.getLogger(__name__)


def _get_sync_session():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.config import get_settings

    settings = get_settings()
    engine = create_engine(settings.database_url_sync, pool_pre_ping=True)
    return sessionmaker(bind=engine)()


@celery_app.task(bind=True, max_retries=3, default_retry_delay=120)
def scrape_restaurant_photos_task(self, restaurant_id: str):
    """
    Scrape menu photos for a restaurant from Google and Yelp.
    Stores them in S3 and creates MenuPhoto records.
    Then chains to OCR for each new photo.
    """
    logger.info("Scraping photos for restaurant %s", restaurant_id)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        photo_ids = loop.run_until_complete(_scrape_and_store(restaurant_id))
        logger.info("Scraped %d photos for restaurant %s", len(photo_ids), restaurant_id)

        # Chain to OCR for each photo
        from app.workers.tasks.ocr import ocr_menu_photo_task

        for photo_id in photo_ids:
            ocr_menu_photo_task.delay(str(photo_id))

        return {"photos_scraped": len(photo_ids)}

    except Exception as exc:
        logger.error("Photo scraping failed for %s: %s", restaurant_id, exc)
        raise self.retry(exc=exc)
    finally:
        loop.close()


async def _scrape_and_store(restaurant_id: str) -> list[uuid.UUID]:
    """Download photos from external APIs and store in S3."""
    from app.integrations.google_places import GooglePlacesClient
    from app.integrations.yelp import YelpClient

    session = _get_sync_session()
    storage = StorageService()
    storage.ensure_buckets()
    photo_ids: list[uuid.UUID] = []

    try:
        restaurant = session.execute(
            select(Restaurant).where(Restaurant.id == uuid.UUID(restaurant_id))
        ).scalar_one_or_none()

        if not restaurant:
            logger.warning("Restaurant %s not found", restaurant_id)
            return []

        # Google Places photos
        if restaurant.google_place_id:
            google_client = GooglePlacesClient()
            try:
                photos = await google_client.get_place_photos(restaurant.google_place_id)
                for photo in photos[:5]:  # Limit to 5 photos per source
                    try:
                        photo_bytes = await google_client.download_photo(
                            photo.photo_reference
                        )
                        if photo_bytes:
                            s3_key = f"google/{restaurant_id}/{uuid.uuid4()}.jpg"
                            storage.upload_photo(
                                photo_bytes, storage.bucket_raw, s3_key
                            )

                            menu_photo = MenuPhoto(
                                restaurant_id=restaurant.id,
                                source=PhotoSource.GOOGLE,
                                s3_key=s3_key,
                                photo_url=google_client.get_photo_url(
                                    photo.photo_reference
                                ),
                            )
                            session.add(menu_photo)
                            session.flush()
                            photo_ids.append(menu_photo.id)
                    except Exception as exc:
                        logger.warning("Failed to download Google photo: %s", exc)
            finally:
                await google_client.close()

        # Yelp photos
        if restaurant.yelp_id:
            yelp_client = YelpClient()
            try:
                biz = await yelp_client.get_business_details(restaurant.yelp_id)
                if biz and biz.photos:
                    for photo_url in biz.photos[:5]:
                        try:
                            photo_bytes = await yelp_client.download_photo(photo_url)
                            if photo_bytes:
                                s3_key = f"yelp/{restaurant_id}/{uuid.uuid4()}.jpg"
                                storage.upload_photo(
                                    photo_bytes, storage.bucket_raw, s3_key
                                )

                                menu_photo = MenuPhoto(
                                    restaurant_id=restaurant.id,
                                    source=PhotoSource.YELP,
                                    s3_key=s3_key,
                                    photo_url=photo_url,
                                )
                                session.add(menu_photo)
                                session.flush()
                                photo_ids.append(menu_photo.id)
                        except Exception as exc:
                            logger.warning("Failed to download Yelp photo: %s", exc)
            finally:
                await yelp_client.close()

        session.commit()

    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

    return photo_ids

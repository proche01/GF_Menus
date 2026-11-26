"""
Task: Run OCR on a menu photo via OpenAI Vision.

Extracts text and classified menu items from a stored photo.
Stores a JSON payload on MenuPhoto.ocr_text so classify can reuse
the Vision results without a second OpenAI call.
"""

import asyncio
import json
import logging
import uuid

from sqlalchemy import select

from app.workers.celery_app import celery_app
from app.models.menu import MenuPhoto
from app.services.storage import StorageService

logger = logging.getLogger(__name__)


def _get_sync_session():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.config import get_settings

    settings = get_settings()
    engine = create_engine(settings.database_url_sync, pool_pre_ping=True)
    return sessionmaker(bind=engine)()


@celery_app.task(bind=True, max_retries=2, default_retry_delay=180)
def ocr_menu_photo_task(self, photo_id: str):
    """
    Run OCR + item extraction on a menu photo.
    Stores structured OCR JSON on the MenuPhoto record,
    then chains to classification once ALL photos for the
    restaurant are processed (avoids N OpenAI classify calls).
    """
    logger.info("Running OCR on photo %s", photo_id)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        result = loop.run_until_complete(_run_ocr(photo_id))
        logger.info(
            "OCR extracted %d items from photo %s",
            result.get("item_count", 0),
            photo_id,
        )

        restaurant_id = result.get("restaurant_id")
        if restaurant_id and result.get("all_photos_done"):
            from app.workers.tasks.classify import classify_restaurant_menu_task

            classify_restaurant_menu_task.delay(restaurant_id)

        return result

    except Exception as exc:
        logger.error("OCR failed for photo %s: %s", photo_id, exc)
        raise self.retry(exc=exc)
    finally:
        loop.close()


async def _run_ocr(photo_id: str) -> dict:
    """Download photo from S3, send to OpenAI Vision, store OCR JSON."""
    from app.integrations.openai_vision import OpenAIVisionClient
    from datetime import datetime, timezone

    session = _get_sync_session()
    storage = StorageService()

    try:
        photo = session.execute(
            select(MenuPhoto).where(MenuPhoto.id == uuid.UUID(photo_id))
        ).scalar_one_or_none()

        if not photo:
            logger.warning("Photo %s not found", photo_id)
            return {"error": "Photo not found"}

        # Idempotent: skip if already processed (protects free-tier on retries)
        if photo.processed and photo.ocr_text:
            logger.info("Photo %s already processed; skipping Vision call", photo_id)
            pending = session.execute(
                select(MenuPhoto).where(
                    MenuPhoto.restaurant_id == photo.restaurant_id,
                    MenuPhoto.processed.is_(False),
                )
            ).scalars().all()
            return {
                "restaurant_id": str(photo.restaurant_id),
                "photo_id": photo_id,
                "item_count": 0,
                "skipped": True,
                "all_photos_done": len(pending) == 0,
            }

        # Download from S3
        photo_bytes = storage.download_photo(storage.bucket_raw, photo.s3_key)
        if not photo_bytes:
            logger.warning("Empty photo data for %s", photo_id)
            return {"error": "Empty photo data"}

        # Run OpenAI Vision OCR (already includes GF classification)
        vision_client = OpenAIVisionClient()
        ocr_result = await vision_client.analyze_menu_photo(photo_bytes)

        # Store structured payload so classify can reuse items without OpenAI
        payload = {
            "raw_text": ocr_result.raw_text,
            "has_gf_section": ocr_result.has_gf_section,
            "gluten_mentioned": ocr_result.gluten_mentioned,
            "items": [
                {
                    "name": item.name,
                    "description": item.description,
                    "price": item.price,
                    "is_gluten_free": item.is_gluten_free,
                    "cross_contact_risk": item.cross_contact_risk,
                    "gf_label_on_menu": item.gf_label_on_menu,
                    "confidence": item.confidence,
                    "reasoning": item.reasoning,
                }
                for item in ocr_result.items
            ],
        }
        photo.ocr_text = json.dumps(payload)
        photo.processed = True
        photo.processed_at = datetime.now(timezone.utc)
        session.commit()

        pending = session.execute(
            select(MenuPhoto).where(
                MenuPhoto.restaurant_id == photo.restaurant_id,
                MenuPhoto.processed.is_(False),
            )
        ).scalars().all()

        return {
            "restaurant_id": str(photo.restaurant_id),
            "photo_id": photo_id,
            "item_count": len(ocr_result.items),
            "has_gf_section": ocr_result.has_gf_section,
            "gluten_mentioned": ocr_result.gluten_mentioned,
            "all_photos_done": len(pending) == 0,
        }

    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

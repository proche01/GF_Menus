"""
Task: Classify all menu items for a restaurant and store results.

Reads OCR text from all processed photos for a restaurant,
runs the GF classifier, and upserts MenuItem records.
"""

import asyncio
import logging
import uuid

from sqlalchemy import select

from app.workers.celery_app import celery_app
from app.models.restaurant import Restaurant
from app.models.menu import MenuPhoto, MenuItem, CrossContactRisk

logger = logging.getLogger(__name__)


def _get_sync_session():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.config import get_settings

    settings = get_settings()
    engine = create_engine(settings.database_url_sync, pool_pre_ping=True)
    return sessionmaker(bind=engine)()


@celery_app.task(bind=True, max_retries=2, default_retry_delay=120)
def classify_restaurant_menu_task(self, restaurant_id: str):
    """
    Classify menu items for a restaurant using all processed photos.
    Stores MenuItem records and updates restaurant GF counts.
    Then chains to GF menu generation.
    """
    logger.info("Classifying menu for restaurant %s", restaurant_id)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        result = loop.run_until_complete(_classify_and_store(restaurant_id))
        logger.info(
            "Classified %d items for restaurant %s (%d GF)",
            result.get("total_items", 0),
            restaurant_id,
            result.get("gf_items", 0),
        )

        # Chain to GF menu generation
        from app.workers.tasks.generate_menu import generate_gf_menu_task

        generate_gf_menu_task.delay(restaurant_id)

        return result

    except Exception as exc:
        logger.error("Classification failed for %s: %s", restaurant_id, exc)
        raise self.retry(exc=exc)
    finally:
        loop.close()


async def _classify_and_store(restaurant_id: str) -> dict:
    """Run classification on all OCR text and store menu items."""
    from app.integrations.openai_vision import OpenAIVisionClient, ExtractedMenuItem
    from app.services.gf_analysis.classifier import classify_menu
    from app.services.gf_analysis.sensitivity_profiles import STRICT_CELIAC

    session = _get_sync_session()

    try:
        rest_uuid = uuid.UUID(restaurant_id)

        # Get all processed photos with OCR text
        photos = session.execute(
            select(MenuPhoto).where(
                MenuPhoto.restaurant_id == rest_uuid,
                MenuPhoto.processed.is_(True),
                MenuPhoto.ocr_text.isnot(None),
            )
        ).scalars().all()

        if not photos:
            logger.info("No processed photos found for restaurant %s", restaurant_id)
            return {"total_items": 0, "gf_items": 0}

        # Combine OCR text from all photos
        combined_text = "\n\n---\n\n".join(
            p.ocr_text for p in photos if p.ocr_text
        )

        # Use OpenAI to classify the combined text
        vision_client = OpenAIVisionClient()
        ocr_result = await vision_client.classify_text_menu(combined_text)

        # Clear existing menu items for this restaurant (re-classification)
        session.execute(
            MenuItem.__table__.delete().where(
                MenuItem.restaurant_id == rest_uuid
            )
        )

        # Store classified items
        gf_count = 0
        has_gf_section = ocr_result.has_gf_section
        gluten_mentioned = ocr_result.gluten_mentioned

        for extracted in ocr_result.items:
            menu_item = MenuItem(
                restaurant_id=rest_uuid,
                source_photo_id=photos[0].id,  # Link to first photo
                name=extracted.name,
                description=extracted.description,
                price=extracted.price,
                is_gluten_free=extracted.is_gluten_free,
                cross_contact_risk=CrossContactRisk(extracted.cross_contact_risk),
                gf_label_on_menu=extracted.gf_label_on_menu,
                confidence_score=extracted.confidence,
            )
            session.add(menu_item)
            if extracted.is_gluten_free:
                gf_count += 1

        # Update restaurant-level denormalized fields
        restaurant = session.execute(
            select(Restaurant).where(Restaurant.id == rest_uuid)
        ).scalar_one_or_none()

        if restaurant:
            restaurant.gf_item_count = gf_count
            restaurant.gluten_mentioned_on_menu = gluten_mentioned
            restaurant.has_dedicated_gf_menu = has_gf_section

        session.commit()

        return {
            "total_items": len(ocr_result.items),
            "gf_items": gf_count,
            "has_gf_section": has_gf_section,
            "gluten_mentioned": gluten_mentioned,
        }

    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

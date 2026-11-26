"""
Task: Classify all menu items for a restaurant and store results.

Reads structured OCR JSON from processed photos (produced by the Vision
task) and upserts MenuItem records WITHOUT a second OpenAI call.
Falls back to text classification only if OCR text is plain (legacy).
"""

import json
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
    Build MenuItem records from OCR Vision results already stored on photos.
    Then chains to GF menu generation.
    """
    logger.info("Classifying menu for restaurant %s", restaurant_id)

    try:
        result = _classify_and_store(restaurant_id)
        logger.info(
            "Classified %d items for restaurant %s (%d GF)",
            result.get("total_items", 0),
            restaurant_id,
            result.get("gf_items", 0),
        )

        from app.workers.tasks.generate_menu import generate_gf_menu_task

        generate_gf_menu_task.delay(restaurant_id)

        return result

    except Exception as exc:
        logger.error("Classification failed for %s: %s", restaurant_id, exc)
        raise self.retry(exc=exc)


def _parse_ocr_payload(ocr_text: str) -> dict | None:
    """Parse structured OCR JSON; return None for legacy plain text."""
    try:
        data = json.loads(ocr_text)
        if isinstance(data, dict) and "items" in data:
            return data
    except (json.JSONDecodeError, TypeError):
        pass
    return None


def _classify_and_store(restaurant_id: str) -> dict:
    """Aggregate OCR Vision items into MenuItem rows (no OpenAI by default)."""
    session = _get_sync_session()

    try:
        rest_uuid = uuid.UUID(restaurant_id)

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

        # Prefer structured Vision payloads (zero extra OpenAI cost)
        aggregated_items: list[dict] = []
        has_gf_section = False
        gluten_mentioned = False
        used_vision_payload = False

        for photo in photos:
            payload = _parse_ocr_payload(photo.ocr_text or "")
            if payload:
                used_vision_payload = True
                has_gf_section = has_gf_section or bool(payload.get("has_gf_section"))
                gluten_mentioned = gluten_mentioned or bool(
                    payload.get("gluten_mentioned")
                )
                for item in payload.get("items", []):
                    aggregated_items.append(item)

        if not used_vision_payload:
            # Legacy fallback: plain OCR text → one OpenAI text classify call
            logger.warning(
                "No structured OCR JSON for %s; falling back to OpenAI text classify",
                restaurant_id,
            )
            import asyncio
            from app.integrations.openai_vision import OpenAIVisionClient

            combined_text = "\n\n---\n\n".join(
                p.ocr_text for p in photos if p.ocr_text
            )
            vision_client = OpenAIVisionClient()
            loop = asyncio.new_event_loop()
            try:
                ocr_result = loop.run_until_complete(
                    vision_client.classify_text_menu(combined_text)
                )
            finally:
                loop.close()

            has_gf_section = ocr_result.has_gf_section
            gluten_mentioned = ocr_result.gluten_mentioned
            aggregated_items = [
                {
                    "name": item.name,
                    "description": item.description,
                    "price": item.price,
                    "is_gluten_free": item.is_gluten_free,
                    "cross_contact_risk": item.cross_contact_risk,
                    "gf_label_on_menu": item.gf_label_on_menu,
                    "confidence": item.confidence,
                }
                for item in ocr_result.items
            ]

        # Deduplicate by lowercase name (multiple photos may repeat items)
        seen: set[str] = set()
        unique_items: list[dict] = []
        for item in aggregated_items:
            key = (item.get("name") or "").strip().lower()
            if not key or key in seen:
                continue
            seen.add(key)
            unique_items.append(item)

        # Clear existing menu items for this restaurant (re-classification)
        session.execute(
            MenuItem.__table__.delete().where(MenuItem.restaurant_id == rest_uuid)
        )

        gf_count = 0
        for extracted in unique_items:
            risk = extracted.get("cross_contact_risk", "high")
            try:
                risk_enum = CrossContactRisk(risk)
            except ValueError:
                risk_enum = CrossContactRisk.HIGH

            menu_item = MenuItem(
                restaurant_id=rest_uuid,
                source_photo_id=photos[0].id,
                name=extracted.get("name", ""),
                description=extracted.get("description"),
                price=extracted.get("price"),
                is_gluten_free=bool(extracted.get("is_gluten_free", False)),
                cross_contact_risk=risk_enum,
                gf_label_on_menu=extracted.get("gf_label_on_menu"),
                confidence_score=float(extracted.get("confidence", 0.0) or 0.0),
            )
            session.add(menu_item)
            if menu_item.is_gluten_free:
                gf_count += 1

        restaurant = session.execute(
            select(Restaurant).where(Restaurant.id == rest_uuid)
        ).scalar_one_or_none()

        if restaurant:
            restaurant.gf_item_count = gf_count
            restaurant.gluten_mentioned_on_menu = gluten_mentioned
            restaurant.has_dedicated_gf_menu = has_gf_section

        session.commit()

        return {
            "total_items": len(unique_items),
            "gf_items": gf_count,
            "has_gf_section": has_gf_section,
            "gluten_mentioned": gluten_mentioned,
            "used_vision_payload": used_vision_payload,
        }

    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

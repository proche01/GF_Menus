"""
Task: Generate the final GF menu document for a restaurant.

Reads all classified MenuItem records, applies sensitivity profiles,
and stores GeneratedGFMenu records.
"""

import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import select

from app.workers.celery_app import celery_app
from app.models.restaurant import Restaurant
from app.models.menu import MenuItem, GeneratedGFMenu

logger = logging.getLogger(__name__)


def _get_sync_session():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.config import get_settings

    settings = get_settings()
    engine = create_engine(settings.database_url_sync, pool_pre_ping=True)
    return sessionmaker(bind=engine)()


@celery_app.task(bind=True, max_retries=2, default_retry_delay=60)
def generate_gf_menu_task(self, restaurant_id: str):
    """
    Generate GF menus for all sensitivity profiles from stored menu items.
    This is the final step in the ingestion pipeline.
    """
    logger.info("Generating GF menu for restaurant %s", restaurant_id)

    try:
        result = _generate_and_store(restaurant_id)
        logger.info(
            "Generated GF menus for restaurant %s: %s",
            restaurant_id,
            {k: v.safe_item_count for k, v in result.items()},
        )
        return {
            profile: {
                "safe_items": menu.safe_item_count,
                "total_items": menu.total_menu_items,
            }
            for profile, menu in result.items()
        }

    except Exception as exc:
        logger.error("GF menu generation failed for %s: %s", restaurant_id, exc)
        raise self.retry(exc=exc)


def _generate_and_store(restaurant_id: str) -> dict:
    """Build GF menus from classified items and store in DB."""
    from app.integrations.openai_vision import ExtractedMenuItem
    from app.services.gf_analysis.menu_generator import generate_multiple_profiles

    session = _get_sync_session()

    try:
        rest_uuid = uuid.UUID(restaurant_id)

        # Load all menu items
        items = session.execute(
            select(MenuItem).where(MenuItem.restaurant_id == rest_uuid)
        ).scalars().all()

        if not items:
            logger.info("No menu items found for restaurant %s", restaurant_id)
            return {}

        # Load restaurant for metadata
        restaurant = session.execute(
            select(Restaurant).where(Restaurant.id == rest_uuid)
        ).scalar_one_or_none()

        # Convert DB items to ExtractedMenuItem format for the generator
        extracted_items = [
            ExtractedMenuItem(
                name=item.name,
                description=item.description,
                price=float(item.price) if item.price else None,
                is_gluten_free=item.is_gluten_free,
                cross_contact_risk=item.cross_contact_risk.value
                if hasattr(item.cross_contact_risk, "value")
                else item.cross_contact_risk,
                gf_label_on_menu=item.gf_label_on_menu,
                confidence=item.confidence_score,
                reasoning="From database classification",
            )
            for item in items
        ]

        # Generate menus for all profiles
        menus = generate_multiple_profiles(
            extracted_items,
            profile_types=["STRICT_CELIAC", "STANDARD_GF"],
            has_gf_section=restaurant.has_dedicated_gf_menu if restaurant else False,
            gluten_mentioned=restaurant.gluten_mentioned_on_menu if restaurant else False,
        )

        # Clear existing generated menus
        session.execute(
            GeneratedGFMenu.__table__.delete().where(
                GeneratedGFMenu.restaurant_id == rest_uuid
            )
        )

        # Store generated menus
        for profile_type, menu in menus.items():
            gf_menu = GeneratedGFMenu(
                restaurant_id=rest_uuid,
                sensitivity_profile=profile_type,
                items=menu.safe_items,
                strict_celiac_items=(
                    menu.safe_items if profile_type == "STRICT_CELIAC" else None
                ),
                item_count=menu.safe_item_count,
                generated_at=datetime.now(timezone.utc),
            )
            session.add(gf_menu)

        session.commit()
        return menus

    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

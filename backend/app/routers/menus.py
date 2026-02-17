"""Menu photos and generated GF menu endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.menu import (
    MenuPhotoResponse,
    MenuItemResponse,
    GeneratedGFMenuResponse,
)
from app.services.menu_service import MenuService

router = APIRouter(prefix="/api/menus", tags=["menus"])


@router.get("/{restaurant_id}/photos", response_model=list[MenuPhotoResponse])
async def get_menu_photos(
    restaurant_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get all menu photos for a restaurant with presigned URLs."""
    service = MenuService(db)
    photos = await service.get_photos_with_urls(restaurant_id)
    return photos


@router.get("/{restaurant_id}/items", response_model=list[MenuItemResponse])
async def get_menu_items(
    restaurant_id: uuid.UUID,
    gf_only: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
):
    """Get menu items for a restaurant, optionally filtered to GF only."""
    service = MenuService(db)
    items = await service.get_items(restaurant_id, gf_only=gf_only)
    return [
        MenuItemResponse(
            id=item.id,
            restaurant_id=item.restaurant_id,
            name=item.name,
            description=item.description,
            price=float(item.price) if item.price else None,
            is_gluten_free=item.is_gluten_free,
            cross_contact_risk=(
                item.cross_contact_risk.value
                if hasattr(item.cross_contact_risk, "value")
                else item.cross_contact_risk
            ),
            gf_label_on_menu=item.gf_label_on_menu,
            confidence_score=item.confidence_score,
        )
        for item in items
    ]


@router.get("/{restaurant_id}/gf-menu")
async def get_generated_gf_menu(
    restaurant_id: uuid.UUID,
    sensitivity_profile: str = Query(default="STRICT_CELIAC"),
    db: AsyncSession = Depends(get_db),
):
    """Get the AI-generated GF menu for a restaurant and sensitivity profile."""
    service = MenuService(db)
    menu = await service.get_generated_menu(restaurant_id, sensitivity_profile)

    if not menu:
        raise HTTPException(
            status_code=404,
            detail=(
                f"No generated GF menu found for restaurant {restaurant_id} "
                f"with profile {sensitivity_profile}. "
                "The menu may not have been processed yet."
            ),
        )

    return {
        "id": str(menu.id),
        "restaurant_id": str(menu.restaurant_id),
        "sensitivity_profile": menu.sensitivity_profile,
        "items": menu.items,
        "item_count": menu.item_count,
        "generated_at": menu.generated_at.isoformat() if menu.generated_at else None,
    }


@router.get("/{restaurant_id}/safe-count")
async def get_safe_item_count(
    restaurant_id: uuid.UUID,
    sensitivity_profile: str = Query(default="STRICT_CELIAC"),
    db: AsyncSession = Depends(get_db),
):
    """Get just the count of safe items for quick display."""
    service = MenuService(db)
    count = await service.get_safe_item_count(restaurant_id, sensitivity_profile)
    return {
        "restaurant_id": str(restaurant_id),
        "sensitivity_profile": sensitivity_profile,
        "safe_item_count": count,
    }

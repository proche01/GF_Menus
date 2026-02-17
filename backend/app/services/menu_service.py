"""Menu service: photos, items, and generated GF menus."""

import uuid
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.menu import MenuPhoto, MenuItem, GeneratedGFMenu
from app.services.storage import StorageService

logger = logging.getLogger(__name__)


class MenuService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self._storage: StorageService | None = None

    @property
    def storage(self) -> StorageService:
        if self._storage is None:
            self._storage = StorageService()
        return self._storage

    async def get_photos(self, restaurant_id: uuid.UUID) -> list[MenuPhoto]:
        """Get all menu photos for a restaurant."""
        result = await self.db.execute(
            select(MenuPhoto)
            .where(MenuPhoto.restaurant_id == restaurant_id)
            .order_by(MenuPhoto.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_photos_with_urls(self, restaurant_id: uuid.UUID) -> list[dict]:
        """Get photos with presigned S3 URLs."""
        photos = await self.get_photos(restaurant_id)
        results = []
        for photo in photos:
            url = photo.photo_url or self.storage.get_photo_url(
                self.storage.bucket_raw, photo.s3_key
            )
            results.append({
                "id": str(photo.id),
                "restaurant_id": str(photo.restaurant_id),
                "source": photo.source.value if hasattr(photo.source, "value") else photo.source,
                "photo_url": url,
                "created_at": photo.created_at.isoformat() if photo.created_at else None,
            })
        return results

    async def get_items(
        self,
        restaurant_id: uuid.UUID,
        gf_only: bool = False,
    ) -> list[MenuItem]:
        """Get menu items, optionally filtered to GF-only."""
        query = select(MenuItem).where(
            MenuItem.restaurant_id == restaurant_id
        )
        if gf_only:
            query = query.where(MenuItem.is_gluten_free.is_(True))

        query = query.order_by(
            MenuItem.is_gluten_free.desc(),
            MenuItem.confidence_score.desc(),
            MenuItem.name,
        )

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_generated_menu(
        self,
        restaurant_id: uuid.UUID,
        sensitivity_profile: str = "STRICT_CELIAC",
    ) -> GeneratedGFMenu | None:
        """Get the generated GF menu for a profile."""
        result = await self.db.execute(
            select(GeneratedGFMenu).where(
                GeneratedGFMenu.restaurant_id == restaurant_id,
                GeneratedGFMenu.sensitivity_profile == sensitivity_profile,
            )
        )
        return result.scalar_one_or_none()

    async def get_safe_item_count(
        self,
        restaurant_id: uuid.UUID,
        sensitivity_profile: str = "STRICT_CELIAC",
    ) -> int:
        """Get the count of safe items for a profile."""
        menu = await self.get_generated_menu(restaurant_id, sensitivity_profile)
        if menu:
            return menu.item_count
        return 0

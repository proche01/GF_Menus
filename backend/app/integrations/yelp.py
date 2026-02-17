"""Yelp Fusion API integration for restaurant discovery and photos."""

import logging
from dataclasses import dataclass

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)

YELP_BASE = "https://api.yelp.com/v3"
BUSINESS_SEARCH_URL = f"{YELP_BASE}/businesses/search"
BUSINESS_DETAIL_URL = f"{YELP_BASE}/businesses"


@dataclass
class YelpBusiness:
    yelp_id: str
    name: str
    address: str
    latitude: float
    longitude: float
    categories: list[str]
    rating: float | None = None
    review_count: int = 0
    image_url: str | None = None
    photos: list[str] | None = None


class YelpClient:
    """Client for the Yelp Fusion API with retry logic."""

    def __init__(self, api_key: str | None = None):
        settings = get_settings()
        self.api_key = api_key or settings.yelp_api_key
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(30.0),
                limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
        return self._client

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def search_businesses(
        self,
        latitude: float,
        longitude: float,
        radius_m: int = 10000,
        term: str = "restaurant",
        limit: int = 50,
        offset: int = 0,
    ) -> list[YelpBusiness]:
        """Search for restaurants near a location."""
        client = await self._get_client()

        params = {
            "latitude": latitude,
            "longitude": longitude,
            "radius": min(radius_m, 40000),  # Yelp max is 40km
            "term": term,
            "categories": "restaurants",
            "limit": min(limit, 50),
            "offset": offset,
        }

        for attempt in range(3):
            try:
                resp = await client.get(BUSINESS_SEARCH_URL, params=params)
                resp.raise_for_status()
                data = resp.json()
                break
            except (httpx.HTTPStatusError, httpx.RequestError) as exc:
                logger.warning(
                    "Yelp search attempt %d failed: %s", attempt + 1, exc
                )
                if attempt == 2:
                    raise

        results: list[YelpBusiness] = []
        for biz in data.get("businesses", []):
            coords = biz.get("coordinates", {})
            location = biz.get("location", {})
            address_parts = [
                location.get("address1", ""),
                location.get("city", ""),
                location.get("state", ""),
                location.get("zip_code", ""),
            ]
            results.append(
                YelpBusiness(
                    yelp_id=biz["id"],
                    name=biz.get("name", ""),
                    address=", ".join(p for p in address_parts if p),
                    latitude=coords.get("latitude", 0.0),
                    longitude=coords.get("longitude", 0.0),
                    categories=[
                        c.get("title", "") for c in biz.get("categories", [])
                    ],
                    rating=biz.get("rating"),
                    review_count=biz.get("review_count", 0),
                    image_url=biz.get("image_url"),
                )
            )

        return results

    async def get_business_details(self, yelp_id: str) -> YelpBusiness | None:
        """Get full business details including photos."""
        client = await self._get_client()

        for attempt in range(3):
            try:
                resp = await client.get(f"{BUSINESS_DETAIL_URL}/{yelp_id}")
                resp.raise_for_status()
                biz = resp.json()
                break
            except (httpx.HTTPStatusError, httpx.RequestError) as exc:
                logger.warning(
                    "Yelp details attempt %d failed: %s", attempt + 1, exc
                )
                if attempt == 2:
                    raise

        coords = biz.get("coordinates", {})
        location = biz.get("location", {})
        address_parts = [
            location.get("address1", ""),
            location.get("city", ""),
            location.get("state", ""),
            location.get("zip_code", ""),
        ]
        return YelpBusiness(
            yelp_id=biz["id"],
            name=biz.get("name", ""),
            address=", ".join(p for p in address_parts if p),
            latitude=coords.get("latitude", 0.0),
            longitude=coords.get("longitude", 0.0),
            categories=[c.get("title", "") for c in biz.get("categories", [])],
            rating=biz.get("rating"),
            review_count=biz.get("review_count", 0),
            image_url=biz.get("image_url"),
            photos=biz.get("photos", []),
        )

    async def download_photo(self, photo_url: str) -> bytes:
        """Download a photo by URL."""
        client = await self._get_client()
        for attempt in range(3):
            try:
                resp = await client.get(photo_url, follow_redirects=True)
                resp.raise_for_status()
                return resp.content
            except (httpx.HTTPStatusError, httpx.RequestError) as exc:
                logger.warning(
                    "Yelp photo download attempt %d failed: %s",
                    attempt + 1,
                    exc,
                )
                if attempt == 2:
                    raise
        return b""

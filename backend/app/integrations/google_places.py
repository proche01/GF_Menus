"""Google Places API integration for restaurant discovery and menu photos."""

import logging
from dataclasses import dataclass

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)

NEARBY_SEARCH_URL = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
PLACE_DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"
PLACE_PHOTO_URL = "https://maps.googleapis.com/maps/api/place/photo"


@dataclass
class PlaceResult:
    place_id: str
    name: str
    address: str
    latitude: float
    longitude: float
    types: list[str]
    rating: float | None = None
    price_level: int | None = None


@dataclass
class PlacePhoto:
    photo_reference: str
    width: int
    height: int


class GooglePlacesClient:
    """Client for Google Places API with retry logic and caching hooks."""

    def __init__(self, api_key: str | None = None):
        settings = get_settings()
        self.api_key = api_key or settings.google_places_api_key
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(30.0),
                limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
            )
        return self._client

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def nearby_search(
        self,
        latitude: float,
        longitude: float,
        radius_m: int = 10000,
        keyword: str = "restaurant",
        page_token: str | None = None,
    ) -> tuple[list[PlaceResult], str | None]:
        """
        Search for restaurants near a location.
        Returns (results, next_page_token).
        """
        client = await self._get_client()

        params: dict = {
            "key": self.api_key,
            "location": f"{latitude},{longitude}",
            "radius": radius_m,
            "keyword": keyword,
            "type": "restaurant",
        }
        if page_token:
            params["pagetoken"] = page_token

        for attempt in range(3):
            try:
                resp = await client.get(NEARBY_SEARCH_URL, params=params)
                resp.raise_for_status()
                data = resp.json()
                break
            except (httpx.HTTPStatusError, httpx.RequestError) as exc:
                logger.warning(
                    "Google Places nearby_search attempt %d failed: %s",
                    attempt + 1,
                    exc,
                )
                if attempt == 2:
                    raise

        results: list[PlaceResult] = []
        for place in data.get("results", []):
            loc = place.get("geometry", {}).get("location", {})
            results.append(
                PlaceResult(
                    place_id=place["place_id"],
                    name=place.get("name", ""),
                    address=place.get("vicinity", ""),
                    latitude=loc.get("lat", 0.0),
                    longitude=loc.get("lng", 0.0),
                    types=place.get("types", []),
                    rating=place.get("rating"),
                    price_level=place.get("price_level"),
                )
            )

        next_token = data.get("next_page_token")
        return results, next_token

    async def get_place_details(self, place_id: str) -> dict:
        """Get full details for a place including photos."""
        client = await self._get_client()

        params = {
            "key": self.api_key,
            "place_id": place_id,
            "fields": "name,formatted_address,geometry,photos,opening_hours,website,url,types",
        }

        for attempt in range(3):
            try:
                resp = await client.get(PLACE_DETAILS_URL, params=params)
                resp.raise_for_status()
                return resp.json().get("result", {})
            except (httpx.HTTPStatusError, httpx.RequestError) as exc:
                logger.warning(
                    "Google Places details attempt %d failed: %s",
                    attempt + 1,
                    exc,
                )
                if attempt == 2:
                    raise
        return {}

    async def get_place_photos(self, place_id: str) -> list[PlacePhoto]:
        """Extract photo references from place details."""
        details = await self.get_place_details(place_id)
        photos: list[PlacePhoto] = []
        for p in details.get("photos", []):
            photos.append(
                PlacePhoto(
                    photo_reference=p["photo_reference"],
                    width=p.get("width", 0),
                    height=p.get("height", 0),
                )
            )
        return photos

    def get_photo_url(self, photo_reference: str, max_width: int = 1600) -> str:
        """Build a direct URL to download a place photo."""
        return (
            f"{PLACE_PHOTO_URL}"
            f"?maxwidth={max_width}"
            f"&photo_reference={photo_reference}"
            f"&key={self.api_key}"
        )

    async def download_photo(self, photo_reference: str, max_width: int = 1600) -> bytes:
        """Download photo bytes."""
        client = await self._get_client()
        url = self.get_photo_url(photo_reference, max_width)

        for attempt in range(3):
            try:
                resp = await client.get(url, follow_redirects=True)
                resp.raise_for_status()
                return resp.content
            except (httpx.HTTPStatusError, httpx.RequestError) as exc:
                logger.warning(
                    "Google photo download attempt %d failed: %s",
                    attempt + 1,
                    exc,
                )
                if attempt == 2:
                    raise
        return b""

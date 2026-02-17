"""Geocoding integration for address-to-coordinates conversion."""

import logging
from dataclasses import dataclass

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)

GOOGLE_GEOCODE_URL = "https://maps.googleapis.com/maps/api/geocode/json"


@dataclass
class GeocodingResult:
    latitude: float
    longitude: float
    formatted_address: str
    place_id: str | None = None


class GeocodingClient:
    """Forward and reverse geocoding via Google Geocoding API."""

    def __init__(self, api_key: str | None = None):
        settings = get_settings()
        self.api_key = api_key or settings.google_places_api_key
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=httpx.Timeout(15.0))
        return self._client

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def forward_geocode(self, address: str) -> GeocodingResult | None:
        """Convert an address string to coordinates."""
        client = await self._get_client()

        params = {"address": address, "key": self.api_key}

        for attempt in range(3):
            try:
                resp = await client.get(GOOGLE_GEOCODE_URL, params=params)
                resp.raise_for_status()
                data = resp.json()
                break
            except (httpx.HTTPStatusError, httpx.RequestError) as exc:
                logger.warning(
                    "Geocoding forward attempt %d failed: %s", attempt + 1, exc
                )
                if attempt == 2:
                    return None

        results = data.get("results", [])
        if not results:
            return None

        first = results[0]
        loc = first["geometry"]["location"]
        return GeocodingResult(
            latitude=loc["lat"],
            longitude=loc["lng"],
            formatted_address=first.get("formatted_address", address),
            place_id=first.get("place_id"),
        )

    async def reverse_geocode(
        self, latitude: float, longitude: float
    ) -> GeocodingResult | None:
        """Convert coordinates to a human-readable address."""
        client = await self._get_client()

        params = {"latlng": f"{latitude},{longitude}", "key": self.api_key}

        for attempt in range(3):
            try:
                resp = await client.get(GOOGLE_GEOCODE_URL, params=params)
                resp.raise_for_status()
                data = resp.json()
                break
            except (httpx.HTTPStatusError, httpx.RequestError) as exc:
                logger.warning(
                    "Geocoding reverse attempt %d failed: %s", attempt + 1, exc
                )
                if attempt == 2:
                    return None

        results = data.get("results", [])
        if not results:
            return None

        first = results[0]
        return GeocodingResult(
            latitude=latitude,
            longitude=longitude,
            formatted_address=first.get("formatted_address", ""),
            place_id=first.get("place_id"),
        )

"""Geo service: geocoding and coordinate utilities."""

import logging

from app.integrations.geocoding import GeocodingClient, GeocodingResult

logger = logging.getLogger(__name__)


class GeoService:
    def __init__(self):
        self._client: GeocodingClient | None = None

    @property
    def client(self) -> GeocodingClient:
        if self._client is None:
            self._client = GeocodingClient()
        return self._client

    async def geocode_address(self, address: str) -> GeocodingResult | None:
        """Convert an address to coordinates."""
        return await self.client.forward_geocode(address)

    async def reverse_geocode(
        self, latitude: float, longitude: float
    ) -> GeocodingResult | None:
        """Convert coordinates to a human-readable address."""
        return await self.client.reverse_geocode(latitude, longitude)

    async def close(self) -> None:
        if self._client:
            await self._client.close()

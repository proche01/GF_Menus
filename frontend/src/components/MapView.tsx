"use client";

import { useEffect, useRef } from "react";
import type { Restaurant } from "@/lib/types";

interface Props {
  restaurants: Restaurant[];
  center: { lat: number; lng: number };
  zoom?: number;
  onPinClick?: (restaurant: Restaurant) => void;
}

/**
 * Leaflet map component for displaying restaurant pins.
 *
 * Uses dynamic import to avoid SSR issues with Leaflet.
 * The map is rendered into a ref div and managed imperatively
 * to avoid React-Leaflet SSR complexity.
 */
export function MapView({
  restaurants,
  center,
  zoom = 13,
  onPinClick,
}: Props) {
  const mapRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<any>(null);
  const markersRef = useRef<any[]>([]);

  useEffect(() => {
    if (typeof window === "undefined" || !mapRef.current) return;

    let cancelled = false;

    async function initMap() {
      const L = (await import("leaflet")).default;

      // Fix default icon paths for webpack/Next.js
      delete (L.Icon.Default.prototype as any)._getIconUrl;
      L.Icon.Default.mergeOptions({
        iconRetinaUrl:
          "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png",
        iconUrl:
          "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png",
        shadowUrl:
          "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png",
      });

      if (cancelled || !mapRef.current) return;

      if (!mapInstanceRef.current) {
        mapInstanceRef.current = L.map(mapRef.current).setView(
          [center.lat, center.lng],
          zoom
        );

        L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
          attribution: "&copy; OpenStreetMap contributors",
          maxZoom: 19,
        }).addTo(mapInstanceRef.current);
      } else {
        mapInstanceRef.current.setView([center.lat, center.lng], zoom);
      }

      // Clear old markers
      for (const m of markersRef.current) {
        m.remove();
      }
      markersRef.current = [];

      // Add restaurant markers
      for (const r of restaurants) {
        if (r.latitude && r.longitude) {
          const marker = L.marker([r.latitude, r.longitude])
            .addTo(mapInstanceRef.current)
            .bindPopup(
              `<strong>${r.name}</strong><br/>${r.gf_item_count} GF items`
            );

          if (onPinClick) {
            marker.on("click", () => onPinClick(r));
          }

          markersRef.current.push(marker);
        }
      }
    }

    initMap();

    return () => {
      cancelled = true;
    };
  }, [restaurants, center, zoom, onPinClick]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, []);

  return (
    <>
      <link
        rel="stylesheet"
        href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css"
      />
      <div ref={mapRef} className="h-full w-full min-h-[400px] rounded-xl" />
    </>
  );
}

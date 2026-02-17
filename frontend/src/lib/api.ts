/**
 * Typed API client for the FastAPI backend.
 * In production, requests are proxied through Next.js rewrites.
 */

import type {
  Restaurant,
  RestaurantSearchParams,
  RestaurantSearchResult,
  MenuPhoto,
  GeneratedGFMenu,
  MenuItem,
  MapBounds,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "/api";

async function fetchJSON<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`API error ${res.status}: ${body}`);
  }
  return res.json();
}

export const api = {
  restaurants: {
    search(params: RestaurantSearchParams) {
      const qs = new URLSearchParams();
      qs.set("latitude", String(params.latitude));
      qs.set("longitude", String(params.longitude));
      if (params.radius_km) qs.set("radius_km", String(params.radius_km));
      if (params.min_gf_items)
        qs.set("min_gf_items", String(params.min_gf_items));
      if (params.sort_by) qs.set("sort_by", params.sort_by);
      if (params.sort_order) qs.set("sort_order", params.sort_order);
      if (params.page) qs.set("page", String(params.page));
      if (params.page_size) qs.set("page_size", String(params.page_size));
      return fetchJSON<RestaurantSearchResult>(
        `${API_BASE}/search/restaurants?${qs}`
      );
    },

    getById(id: string) {
      return fetchJSON<Restaurant>(`${API_BASE}/restaurants/${id}`);
    },

    getBySlug(slug: string) {
      return fetchJSON<Restaurant>(`${API_BASE}/restaurants/slug/${slug}`);
    },

    getMapPins(bounds: MapBounds) {
      const qs = new URLSearchParams({
        north: String(bounds.north),
        south: String(bounds.south),
        east: String(bounds.east),
        west: String(bounds.west),
      });
      return fetchJSON<Restaurant[]>(
        `${API_BASE}/restaurants/map?${qs}`
      );
    },
  },

  menus: {
    getPhotos(restaurantId: string) {
      return fetchJSON<MenuPhoto[]>(
        `${API_BASE}/menus/${restaurantId}/photos`
      );
    },

    getGeneratedMenu(restaurantId: string, profile = "STRICT_CELIAC") {
      return fetchJSON<GeneratedGFMenu>(
        `${API_BASE}/menus/${restaurantId}/gf-menu?sensitivity_profile=${profile}`
      );
    },

    getItems(restaurantId: string, gfOnly = false) {
      const qs = gfOnly ? "?gf_only=true" : "";
      return fetchJSON<MenuItem[]>(
        `${API_BASE}/menus/${restaurantId}/items${qs}`
      );
    },
  },
};

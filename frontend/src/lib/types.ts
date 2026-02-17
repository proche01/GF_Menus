/** Shared TypeScript types matching the FastAPI Pydantic schemas. */

export interface Restaurant {
  id: string;
  name: string;
  address: string;
  latitude: number;
  longitude: number;
  google_place_id: string | null;
  yelp_id: string | null;
  has_dedicated_gf_menu: boolean;
  gf_item_count: number;
  gluten_mentioned_on_menu: boolean;
  distance_km?: number;
}

export interface MenuPhoto {
  id: string;
  restaurant_id: string;
  source: "google" | "yelp" | "user_upload";
  photo_url: string;
  created_at: string;
}

export interface MenuItem {
  id: string;
  restaurant_id: string;
  name: string;
  description: string | null;
  price: number | null;
  is_gluten_free: boolean;
  cross_contact_risk: "none" | "low" | "high";
  gf_label_on_menu: string | null;
  confidence_score: number;
}

export interface GeneratedGFMenu {
  id: string;
  restaurant_id: string;
  sensitivity_profile: string;
  items: MenuItem[];
  item_count: number;
  generated_at: string;
}

export interface RestaurantSearchParams {
  latitude: number;
  longitude: number;
  radius_km?: number;
  min_gf_items?: number;
  sort_by?: "distance" | "gf_item_count";
  sort_order?: "asc" | "desc";
  page?: number;
  page_size?: number;
}

export interface RestaurantSearchResult {
  restaurants: Restaurant[];
  total: number;
  page: number;
  page_size: number;
}

export interface MapBounds {
  north: number;
  south: number;
  east: number;
  west: number;
}

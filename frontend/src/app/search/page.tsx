"use client";

import { useSearchParams, useRouter } from "next/navigation";
import { useMemo, useState, Suspense } from "react";
import { SearchBar } from "@/components/SearchBar";
import { RestaurantList } from "@/components/RestaurantList";
import { FilterPanel } from "@/components/FilterPanel";
import { MapView } from "@/components/MapView";
import { useRestaurantSearch } from "@/hooks/useRestaurantSearch";
import { useFilters } from "@/hooks/useFilters";
import type { Restaurant, RestaurantSearchParams } from "@/lib/types";

function SearchContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const filters = useFilters();
  const [showMap, setShowMap] = useState(true);

  const lat = searchParams.get("lat");
  const lng = searchParams.get("lng");
  const q = searchParams.get("q");

  const params = useMemo<RestaurantSearchParams | null>(() => {
    if (lat && lng) {
      return {
        latitude: parseFloat(lat),
        longitude: parseFloat(lng),
        radius_km: filters.radiusKm,
        min_gf_items: filters.minGfItems,
        sort_by: filters.sortBy,
        sort_order: filters.sortOrder,
      };
    }
    return null;
  }, [lat, lng, filters.radiusKm, filters.minGfItems, filters.sortBy, filters.sortOrder]);

  const { data, isLoading, error } = useRestaurantSearch(params);

  const mapCenter = useMemo(
    () => ({
      lat: lat ? parseFloat(lat) : 40.7128,
      lng: lng ? parseFloat(lng) : -74.006,
    }),
    [lat, lng]
  );

  const handlePinClick = (restaurant: Restaurant) => {
    router.push(`/restaurant/${restaurant.id}`);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="border-b border-gray-200 bg-white px-4 py-3 shadow-sm">
        <div className="mx-auto flex max-w-7xl items-center gap-4">
          <a
            href="/"
            className="text-xl font-bold text-emerald-700 shrink-0"
          >
            GF Finder
          </a>
          <div className="flex-1 max-w-xl">
            <SearchBar />
          </div>
        </div>
      </header>

      {/* Content */}
      <div className="mx-auto max-w-7xl px-4 py-6">
        {!params && !q && (
          <div className="text-center py-16">
            <p className="text-lg text-gray-500">
              Enter a location to find gluten-free restaurants near you.
            </p>
          </div>
        )}

        {(params || q) && (
          <div className="flex gap-6">
            {/* Sidebar: Filters */}
            <aside className="w-64 shrink-0 hidden lg:block">
              <FilterPanel />
            </aside>

            {/* Main: List + Map */}
            <div className="flex-1 min-w-0">
              {/* View toggle */}
              <div className="mb-4 flex items-center justify-between">
                <h2 className="text-lg font-semibold text-gray-800">
                  {q ? `Results for "${q}"` : "Nearby Restaurants"}
                </h2>
                <button
                  onClick={() => setShowMap(!showMap)}
                  className="rounded-lg border border-gray-300 px-3 py-1.5 text-sm font-medium text-gray-600 hover:bg-gray-50"
                >
                  {showMap ? "Hide Map" : "Show Map"}
                </button>
              </div>

              {error && (
                <div className="mb-4 rounded-lg bg-red-50 border border-red-200 p-4 text-sm text-red-700">
                  Failed to load restaurants. Please try again.
                </div>
              )}

              <div
                className={`grid gap-6 ${showMap ? "lg:grid-cols-2" : "grid-cols-1"}`}
              >
                {/* Restaurant list */}
                <div className="order-2 lg:order-1">
                  <RestaurantList
                    restaurants={data?.restaurants ?? []}
                    loading={isLoading}
                    total={data?.total}
                  />
                </div>

                {/* Map */}
                {showMap && (
                  <div className="order-1 lg:order-2 h-[400px] lg:h-[600px] lg:sticky lg:top-4">
                    <MapView
                      restaurants={data?.restaurants ?? []}
                      center={mapCenter}
                      onPinClick={handlePinClick}
                    />
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default function SearchPage() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-screen items-center justify-center">
          <p className="text-gray-500">Loading search...</p>
        </div>
      }
    >
      <SearchContent />
    </Suspense>
  );
}

"use client";

import type { Restaurant } from "@/lib/types";
import { RestaurantCard } from "./RestaurantCard";

interface Props {
  restaurants: Restaurant[];
  loading?: boolean;
  total?: number;
}

export function RestaurantList({ restaurants, loading, total }: Props) {
  if (loading) {
    return (
      <div className="space-y-4">
        {[...Array(5)].map((_, i) => (
          <div
            key={i}
            className="h-28 animate-pulse rounded-xl border border-gray-200 bg-gray-100"
          />
        ))}
      </div>
    );
  }

  if (restaurants.length === 0) {
    return (
      <div className="rounded-xl border border-gray-200 bg-white p-8 text-center">
        <p className="text-lg font-medium text-gray-600">
          No restaurants found
        </p>
        <p className="mt-1 text-sm text-gray-400">
          Try adjusting your filters or expanding the search radius.
        </p>
      </div>
    );
  }

  return (
    <div>
      {total != null && (
        <p className="mb-3 text-sm text-gray-500">
          {total} restaurant{total !== 1 ? "s" : ""} found
        </p>
      )}
      <div className="space-y-3">
        {restaurants.map((r) => (
          <RestaurantCard key={r.id} restaurant={r} />
        ))}
      </div>
    </div>
  );
}

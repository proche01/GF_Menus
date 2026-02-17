"use client";

import Link from "next/link";
import type { Restaurant } from "@/lib/types";

interface Props {
  restaurant: Restaurant;
}

export function RestaurantCard({ restaurant }: Props) {
  return (
    <Link
      href={`/restaurant/${restaurant.id}`}
      className="block rounded-xl border border-gray-200 bg-white p-5 shadow-sm transition hover:shadow-md hover:border-emerald-300"
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <h3 className="text-lg font-semibold text-gray-900 truncate">
            {restaurant.name}
          </h3>
          <p className="mt-1 text-sm text-gray-500 truncate">
            {restaurant.address}
          </p>
        </div>

        <div className="flex flex-col items-end gap-1 shrink-0">
          {restaurant.has_dedicated_gf_menu && (
            <span className="inline-flex items-center rounded-full bg-emerald-100 px-2.5 py-0.5 text-xs font-medium text-emerald-800">
              GF Menu
            </span>
          )}
          {restaurant.gluten_mentioned_on_menu && (
            <span className="inline-flex items-center rounded-full bg-blue-100 px-2.5 py-0.5 text-xs font-medium text-blue-800">
              Gluten Noted
            </span>
          )}
        </div>
      </div>

      <div className="mt-3 flex items-center gap-4 text-sm">
        <div className="flex items-center gap-1">
          <span className="font-semibold text-emerald-700">
            {restaurant.gf_item_count}
          </span>
          <span className="text-gray-500">GF items</span>
        </div>

        {restaurant.distance_km != null && (
          <div className="flex items-center gap-1 text-gray-500">
            <span>{restaurant.distance_km} km away</span>
          </div>
        )}
      </div>
    </Link>
  );
}

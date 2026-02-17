"use client";

import { useFilters } from "@/hooks/useFilters";

export function FilterPanel() {
  const {
    radiusKm,
    minGfItems,
    sortBy,
    sortOrder,
    setRadiusKm,
    setMinGfItems,
    setSortBy,
    setSortOrder,
    reset,
  } = useFilters();

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide">
          Filters
        </h3>
        <button
          onClick={reset}
          className="text-xs text-emerald-600 hover:text-emerald-800 font-medium"
        >
          Reset
        </button>
      </div>

      <div className="space-y-4">
        {/* Radius */}
        <div>
          <label className="block text-sm font-medium text-gray-600 mb-1">
            Distance: {radiusKm} km
          </label>
          <input
            type="range"
            min={1}
            max={50}
            value={radiusKm}
            onChange={(e) => setRadiusKm(Number(e.target.value))}
            className="w-full accent-emerald-600"
          />
          <div className="flex justify-between text-xs text-gray-400">
            <span>1 km</span>
            <span>50 km</span>
          </div>
        </div>

        {/* Min GF items */}
        <div>
          <label className="block text-sm font-medium text-gray-600 mb-1">
            Min GF items: {minGfItems}
          </label>
          <input
            type="range"
            min={0}
            max={30}
            value={minGfItems}
            onChange={(e) => setMinGfItems(Number(e.target.value))}
            className="w-full accent-emerald-600"
          />
          <div className="flex justify-between text-xs text-gray-400">
            <span>Any</span>
            <span>30+</span>
          </div>
        </div>

        {/* Sort by */}
        <div>
          <label className="block text-sm font-medium text-gray-600 mb-1">
            Sort by
          </label>
          <select
            value={sortBy}
            onChange={(e) =>
              setSortBy(e.target.value as "distance" | "gf_item_count")
            }
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
          >
            <option value="distance">Distance</option>
            <option value="gf_item_count">GF Item Count</option>
          </select>
        </div>

        {/* Sort order */}
        <div>
          <label className="block text-sm font-medium text-gray-600 mb-1">
            Order
          </label>
          <div className="flex gap-2">
            <button
              onClick={() => setSortOrder("asc")}
              className={`flex-1 rounded-lg border px-3 py-2 text-sm font-medium transition ${
                sortOrder === "asc"
                  ? "border-emerald-500 bg-emerald-50 text-emerald-700"
                  : "border-gray-300 text-gray-600 hover:bg-gray-50"
              }`}
            >
              {sortBy === "distance" ? "Nearest" : "Fewest"}
            </button>
            <button
              onClick={() => setSortOrder("desc")}
              className={`flex-1 rounded-lg border px-3 py-2 text-sm font-medium transition ${
                sortOrder === "desc"
                  ? "border-emerald-500 bg-emerald-50 text-emerald-700"
                  : "border-gray-300 text-gray-600 hover:bg-gray-50"
              }`}
            >
              {sortBy === "distance" ? "Farthest" : "Most"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

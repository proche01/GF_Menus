"use client";

import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { SafeItemCount } from "@/components/SafeItemCount";
import { DietaryToggle } from "@/components/DietaryToggle";
import { MenuViewer } from "@/components/MenuViewer";
import { GFMenuDisplay } from "@/components/GFMenuDisplay";
import type { Restaurant, MenuPhoto, GeneratedGFMenu, MenuItem } from "@/lib/types";

export default function RestaurantDetailPage() {
  const { slug } = useParams<{ slug: string }>();
  const [profile, setProfile] = useState("STRICT_CELIAC");
  const [activeTab, setActiveTab] = useState<"gf-menu" | "photos" | "all-items">(
    "gf-menu"
  );

  // Fetch restaurant details
  const { data: restaurant, isLoading: loadingRestaurant } = useQuery<Restaurant>({
    queryKey: ["restaurant", slug],
    queryFn: () => api.restaurants.getById(slug),
    enabled: !!slug,
  });

  // Fetch menu photos
  const { data: photos } = useQuery<MenuPhoto[]>({
    queryKey: ["menuPhotos", slug],
    queryFn: () => api.menus.getPhotos(slug),
    enabled: !!slug,
  });

  // Fetch generated GF menu
  const { data: gfMenu, isLoading: loadingMenu } = useQuery({
    queryKey: ["gfMenu", slug, profile],
    queryFn: () => api.menus.getGeneratedMenu(slug, profile),
    enabled: !!slug,
  });

  // Fetch all menu items
  const { data: allItems } = useQuery<MenuItem[]>({
    queryKey: ["menuItems", slug],
    queryFn: () => api.menus.getItems(slug),
    enabled: !!slug,
  });

  if (loadingRestaurant) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-emerald-600 border-t-transparent" />
      </div>
    );
  }

  if (!restaurant) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-4">
        <p className="text-lg text-gray-500">Restaurant not found.</p>
        <Link href="/" className="text-emerald-600 hover:underline">
          Back to search
        </Link>
      </div>
    );
  }

  const totalItems = allItems?.length ?? 0;
  const safeCount = gfMenu?.item_count ?? 0;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="border-b border-gray-200 bg-white px-4 py-3 shadow-sm">
        <div className="mx-auto max-w-5xl flex items-center gap-4">
          <Link
            href="/"
            className="text-xl font-bold text-emerald-700 shrink-0"
          >
            GF Finder
          </Link>
          <nav className="text-sm text-gray-400">
            <Link href="/search" className="hover:text-emerald-600">
              Search
            </Link>
            <span className="mx-2">/</span>
            <span className="text-gray-700">{restaurant.name}</span>
          </nav>
        </div>
      </header>

      <main className="mx-auto max-w-5xl px-4 py-8">
        {/* Restaurant info */}
        <div className="mb-6">
          <div className="flex items-start justify-between gap-4">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                {restaurant.name}
              </h1>
              <p className="mt-1 text-gray-500">{restaurant.address}</p>
            </div>

            <div className="flex gap-2 shrink-0">
              {restaurant.has_dedicated_gf_menu && (
                <span className="inline-flex items-center rounded-full bg-emerald-100 px-3 py-1 text-sm font-medium text-emerald-800">
                  Dedicated GF Menu
                </span>
              )}
              {restaurant.gluten_mentioned_on_menu && (
                <span className="inline-flex items-center rounded-full bg-blue-100 px-3 py-1 text-sm font-medium text-blue-800">
                  Gluten Noted on Menu
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Safe item count */}
        <div className="mb-6">
          <SafeItemCount
            count={safeCount}
            total={totalItems}
            profile={profile}
          />
        </div>

        {/* Dietary toggle */}
        <div className="mb-6">
          <h3 className="mb-2 text-sm font-semibold text-gray-700 uppercase tracking-wide">
            Sensitivity Profile
          </h3>
          <DietaryToggle value={profile} onChange={setProfile} />
        </div>

        {/* Tabs */}
        <div className="mb-6 border-b border-gray-200">
          <nav className="-mb-px flex gap-6">
            {(
              [
                { id: "gf-menu", label: "GF Menu" },
                { id: "photos", label: "Menu Photos" },
                { id: "all-items", label: "All Items" },
              ] as const
            ).map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`border-b-2 pb-3 text-sm font-medium transition ${
                  activeTab === tab.id
                    ? "border-emerald-600 text-emerald-700"
                    : "border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700"
                }`}
              >
                {tab.label}
                {tab.id === "gf-menu" && (
                  <span className="ml-1.5 rounded-full bg-emerald-100 px-2 py-0.5 text-xs text-emerald-700">
                    {safeCount}
                  </span>
                )}
                {tab.id === "all-items" && (
                  <span className="ml-1.5 rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-600">
                    {totalItems}
                  </span>
                )}
              </button>
            ))}
          </nav>
        </div>

        {/* Tab content */}
        {activeTab === "gf-menu" && (
          <div>
            {loadingMenu ? (
              <div className="space-y-3">
                {[...Array(4)].map((_, i) => (
                  <div
                    key={i}
                    className="h-20 animate-pulse rounded-lg border border-gray-200 bg-gray-100"
                  />
                ))}
              </div>
            ) : (
              <GFMenuDisplay
                items={gfMenu?.items ?? []}
                profile={profile}
              />
            )}
          </div>
        )}

        {activeTab === "photos" && (
          <MenuViewer photos={photos ?? []} />
        )}

        {activeTab === "all-items" && (
          <div className="space-y-2">
            {(allItems ?? []).map((item) => (
              <div
                key={item.id}
                className={`rounded-lg border p-4 ${
                  item.is_gluten_free
                    ? "border-emerald-200 bg-emerald-50"
                    : "border-gray-200 bg-white"
                }`}
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-gray-900">
                        {item.name}
                      </span>
                      {item.is_gluten_free && (
                        <span className="rounded-full bg-emerald-600 px-2 py-0.5 text-[10px] font-bold text-white">
                          GF
                        </span>
                      )}
                      {item.gf_label_on_menu && (
                        <span className="text-xs text-emerald-600">
                          ({item.gf_label_on_menu})
                        </span>
                      )}
                    </div>
                    {item.description && (
                      <p className="mt-0.5 text-sm text-gray-500">
                        {item.description}
                      </p>
                    )}
                  </div>
                  {item.price != null && (
                    <span className="text-sm font-medium text-gray-700">
                      ${item.price.toFixed(2)}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}

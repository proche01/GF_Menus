"use client";

import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { MenuViewer } from "@/components/MenuViewer";
import { GFMenuDisplay } from "@/components/GFMenuDisplay";
import { DietaryToggle } from "@/components/DietaryToggle";
import type { MenuPhoto } from "@/lib/types";

export default function MenuPage() {
  const { slug } = useParams<{ slug: string }>();
  const [profile, setProfile] = useState("STRICT_CELIAC");

  const { data: photos } = useQuery<MenuPhoto[]>({
    queryKey: ["menuPhotos", slug],
    queryFn: () => api.menus.getPhotos(slug),
    enabled: !!slug,
  });

  const { data: gfMenu } = useQuery({
    queryKey: ["gfMenu", slug, profile],
    queryFn: () => api.menus.getGeneratedMenu(slug, profile),
    enabled: !!slug,
  });

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="border-b border-gray-200 bg-white px-4 py-3 shadow-sm">
        <div className="mx-auto max-w-5xl flex items-center gap-4">
          <Link href="/" className="text-xl font-bold text-emerald-700">
            GF Finder
          </Link>
          <nav className="text-sm text-gray-400">
            <Link href={`/restaurant/${slug}`} className="hover:text-emerald-600">
              Restaurant
            </Link>
            <span className="mx-2">/</span>
            <span className="text-gray-700">Menu</span>
          </nav>
        </div>
      </header>

      <main className="mx-auto max-w-5xl px-4 py-8">
        <div className="mb-6">
          <DietaryToggle value={profile} onChange={setProfile} />
        </div>

        <div className="grid gap-8 lg:grid-cols-2">
          {/* Original menu photos */}
          <div>
            <h2 className="mb-4 text-lg font-semibold text-gray-800">
              Original Menu Photos
            </h2>
            <MenuViewer photos={photos ?? []} />
          </div>

          {/* Generated GF menu */}
          <div>
            <h2 className="mb-4 text-lg font-semibold text-gray-800">
              Generated GF Menu
              {gfMenu && (
                <span className="ml-2 text-base font-normal text-emerald-600">
                  ({gfMenu.item_count} safe items)
                </span>
              )}
            </h2>
            <GFMenuDisplay
              items={gfMenu?.items ?? []}
              profile={profile}
            />
          </div>
        </div>
      </main>
    </div>
  );
}

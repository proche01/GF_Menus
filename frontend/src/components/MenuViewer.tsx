"use client";

import { useState } from "react";
import type { MenuPhoto } from "@/lib/types";

interface Props {
  photos: MenuPhoto[];
}

export function MenuViewer({ photos }: Props) {
  const [activeIndex, setActiveIndex] = useState(0);

  if (photos.length === 0) {
    return (
      <div className="rounded-xl border border-gray-200 bg-gray-50 p-8 text-center">
        <p className="text-gray-500">No menu photos available yet.</p>
        <p className="mt-1 text-sm text-gray-400">
          Photos will appear once the menu has been analyzed.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {/* Main photo */}
      <div className="relative overflow-hidden rounded-xl border border-gray-200 bg-black">
        <img
          src={photos[activeIndex]?.photo_url || ""}
          alt={`Menu photo ${activeIndex + 1}`}
          className="mx-auto max-h-[600px] w-auto object-contain"
        />
        <div className="absolute bottom-2 right-2 rounded bg-black/60 px-2 py-1 text-xs text-white">
          {activeIndex + 1} / {photos.length}
        </div>
      </div>

      {/* Thumbnails */}
      {photos.length > 1 && (
        <div className="flex gap-2 overflow-x-auto pb-2">
          {photos.map((photo, i) => (
            <button
              key={photo.id}
              onClick={() => setActiveIndex(i)}
              className={`shrink-0 overflow-hidden rounded-lg border-2 transition ${
                i === activeIndex
                  ? "border-emerald-500"
                  : "border-transparent hover:border-gray-300"
              }`}
            >
              <img
                src={photo.photo_url || ""}
                alt={`Thumbnail ${i + 1}`}
                className="h-16 w-20 object-cover"
              />
            </button>
          ))}
        </div>
      )}

      {/* Source badges */}
      <div className="flex gap-2">
        {[...new Set(photos.map((p) => p.source))].map((source) => (
          <span
            key={source}
            className="rounded-full bg-gray-100 px-2.5 py-0.5 text-xs font-medium text-gray-600"
          >
            {source === "google"
              ? "Google"
              : source === "yelp"
                ? "Yelp"
                : "User Upload"}
          </span>
        ))}
      </div>
    </div>
  );
}

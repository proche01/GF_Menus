"use client";

import { create } from "zustand";

interface FilterState {
  radiusKm: number;
  minGfItems: number;
  sortBy: "distance" | "gf_item_count";
  sortOrder: "asc" | "desc";
  hasGfMenu: boolean | null;

  setRadiusKm: (v: number) => void;
  setMinGfItems: (v: number) => void;
  setSortBy: (v: "distance" | "gf_item_count") => void;
  setSortOrder: (v: "asc" | "desc") => void;
  setHasGfMenu: (v: boolean | null) => void;
  reset: () => void;
}

const defaults = {
  radiusKm: 10,
  minGfItems: 0,
  sortBy: "distance" as const,
  sortOrder: "asc" as const,
  hasGfMenu: null as boolean | null,
};

export const useFilters = create<FilterState>((set) => ({
  ...defaults,
  setRadiusKm: (v) => set({ radiusKm: v }),
  setMinGfItems: (v) => set({ minGfItems: v }),
  setSortBy: (v) => set({ sortBy: v }),
  setSortOrder: (v) => set({ sortOrder: v }),
  setHasGfMenu: (v) => set({ hasGfMenu: v }),
  reset: () => set(defaults),
}));

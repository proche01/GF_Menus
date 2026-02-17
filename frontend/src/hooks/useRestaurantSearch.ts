"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { RestaurantSearchParams, RestaurantSearchResult } from "@/lib/types";

export function useRestaurantSearch(params: RestaurantSearchParams | null) {
  return useQuery<RestaurantSearchResult>({
    queryKey: ["restaurantSearch", params],
    queryFn: () => {
      if (!params) throw new Error("No search params");
      return api.restaurants.search(params);
    },
    enabled: !!params,
    staleTime: 5 * 60 * 1000,
  });
}

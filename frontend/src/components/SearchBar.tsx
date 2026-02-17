"use client";

import { useState, useCallback } from "react";
import { useRouter } from "next/navigation";

export function SearchBar() {
  const router = useRouter();
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);

  const handleNearMe = useCallback(() => {
    if (!navigator.geolocation) {
      alert("Geolocation is not supported by your browser.");
      return;
    }
    setLoading(true);
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const { latitude, longitude } = pos.coords;
        router.push(`/search?lat=${latitude}&lng=${longitude}`);
        setLoading(false);
      },
      () => {
        alert("Unable to get your location. Please enter an address.");
        setLoading(false);
      }
    );
  }, [router]);

  const handleSearch = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault();
      if (query.trim()) {
        router.push(`/search?q=${encodeURIComponent(query.trim())}`);
      }
    },
    [query, router]
  );

  return (
    <form onSubmit={handleSearch} className="flex flex-col gap-3 sm:flex-row">
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Enter city, address, or zip code..."
        className="flex-1 rounded-lg border border-gray-300 px-4 py-3 text-base shadow-sm focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-200"
      />
      <button
        type="submit"
        className="rounded-lg bg-emerald-600 px-6 py-3 font-semibold text-white shadow-sm transition hover:bg-emerald-700 focus:outline-none focus:ring-2 focus:ring-emerald-400"
      >
        Search
      </button>
      <button
        type="button"
        onClick={handleNearMe}
        disabled={loading}
        className="rounded-lg border border-emerald-600 px-6 py-3 font-semibold text-emerald-700 shadow-sm transition hover:bg-emerald-50 focus:outline-none focus:ring-2 focus:ring-emerald-400 disabled:opacity-50"
      >
        {loading ? "Locating..." : "Near Me"}
      </button>
    </form>
  );
}

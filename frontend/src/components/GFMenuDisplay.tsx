"use client";

import type { MenuItem } from "@/lib/types";

interface GFMenuItem {
  name: string;
  description?: string | null;
  price?: number | null;
  is_safe: boolean;
  is_gluten_free: boolean;
  cross_contact_risk: string;
  gf_label_on_menu?: string | null;
  confidence: number;
  reasoning?: string;
  excluded_reason?: string | null;
}

interface Props {
  items: GFMenuItem[];
  profile: string;
}

function riskBadge(risk: string) {
  switch (risk) {
    case "none":
      return (
        <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-medium text-emerald-800">
          No risk
        </span>
      );
    case "low":
      return (
        <span className="rounded-full bg-yellow-100 px-2 py-0.5 text-xs font-medium text-yellow-800">
          Low risk
        </span>
      );
    case "high":
      return (
        <span className="rounded-full bg-red-100 px-2 py-0.5 text-xs font-medium text-red-800">
          High risk
        </span>
      );
    default:
      return null;
  }
}

function confidenceBar(confidence: number) {
  const pct = Math.round(confidence * 100);
  const color =
    pct >= 80
      ? "bg-emerald-500"
      : pct >= 60
        ? "bg-yellow-500"
        : "bg-red-400";

  return (
    <div className="flex items-center gap-2">
      <div className="h-1.5 w-16 rounded-full bg-gray-200">
        <div
          className={`h-1.5 rounded-full ${color}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-xs text-gray-400">{pct}%</span>
    </div>
  );
}

export function GFMenuDisplay({ items, profile }: Props) {
  if (items.length === 0) {
    return (
      <div className="rounded-xl border border-gray-200 bg-white p-8 text-center">
        <p className="text-gray-500">No safe items found for this profile.</p>
        <p className="mt-1 text-sm text-gray-400">
          Try switching to a less restrictive dietary profile.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {items.map((item, i) => (
        <div
          key={i}
          className="rounded-lg border border-gray-200 bg-white p-4 hover:border-emerald-200 transition"
        >
          <div className="flex items-start justify-between gap-3">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <h4 className="font-semibold text-gray-900">{item.name}</h4>
                {item.gf_label_on_menu && (
                  <span className="rounded bg-emerald-600 px-1.5 py-0.5 text-[10px] font-bold text-white uppercase">
                    {item.gf_label_on_menu}
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
              <span className="text-sm font-medium text-gray-700 shrink-0">
                ${item.price.toFixed(2)}
              </span>
            )}
          </div>

          <div className="mt-2 flex items-center gap-3 flex-wrap">
            {riskBadge(item.cross_contact_risk)}
            {confidenceBar(item.confidence)}
          </div>
        </div>
      ))}
    </div>
  );
}

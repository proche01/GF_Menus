"use client";

interface Props {
  count: number;
  total: number;
  profile: string;
}

export function SafeItemCount({ count, total, profile }: Props) {
  const percentage = total > 0 ? Math.round((count / total) * 100) : 0;

  const profileLabel =
    profile === "STRICT_CELIAC"
      ? "Strict Celiac"
      : profile === "STANDARD_GF"
        ? "Standard GF"
        : profile;

  return (
    <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-5">
      <div className="flex items-baseline gap-2">
        <span className="text-4xl font-bold text-emerald-700">{count}</span>
        <span className="text-lg text-emerald-600">
          of {total} items are safe
        </span>
      </div>

      {/* Progress bar */}
      <div className="mt-3 h-2.5 w-full rounded-full bg-emerald-200">
        <div
          className="h-2.5 rounded-full bg-emerald-600 transition-all duration-500"
          style={{ width: `${percentage}%` }}
        />
      </div>

      <p className="mt-2 text-sm text-emerald-600">
        Based on <strong>{profileLabel}</strong> sensitivity profile
      </p>
    </div>
  );
}

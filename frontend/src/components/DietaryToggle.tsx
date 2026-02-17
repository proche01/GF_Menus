"use client";

interface Props {
  value: string;
  onChange: (profile: string) => void;
}

const profiles = [
  {
    id: "STRICT_CELIAC",
    label: "Strict Celiac",
    description: "No cross-contact. Safest option.",
  },
  {
    id: "STANDARD_GF",
    label: "Standard GF",
    description: "Avoids gluten, tolerates low cross-contact.",
  },
];

export function DietaryToggle({ value, onChange }: Props) {
  return (
    <div className="flex gap-2">
      {profiles.map((p) => (
        <button
          key={p.id}
          onClick={() => onChange(p.id)}
          className={`flex-1 rounded-lg border p-3 text-left transition ${
            value === p.id
              ? "border-emerald-500 bg-emerald-50 ring-1 ring-emerald-500"
              : "border-gray-200 bg-white hover:border-gray-300"
          }`}
        >
          <span
            className={`block text-sm font-semibold ${
              value === p.id ? "text-emerald-700" : "text-gray-700"
            }`}
          >
            {p.label}
          </span>
          <span className="block text-xs text-gray-500 mt-0.5">
            {p.description}
          </span>
        </button>
      ))}
    </div>
  );
}

"use client";

import { ArenaBadge } from "@/components/ui/ArenaBadge";
import { CATEGORY_LABELS } from "@/lib/types";
import { getCategoryColor } from "@/lib/utils";

interface ChallengeFilterProps {
  selectedCategory: string;
  onCategoryChange: (cat: string) => void;
  sortBy: string;
  onSortChange: (sort: string) => void;
}

export function ChallengeFilter({
  selectedCategory,
  onCategoryChange,
  sortBy,
  onSortChange,
}: ChallengeFilterProps) {
  const categories = [
    { key: "all", label: "전체" },
    ...Object.entries(CATEGORY_LABELS).map(([key, label]) => ({ key, label })),
  ];

  return (
    <div className="space-y-6">
      <div>
        <div className="font-label uppercase tracking-[0.15em] text-[11px] text-ink-3 mb-3">
          {"// category"}
        </div>
        <div className="flex flex-wrap gap-2">
          {categories.map((cat) => (
            <button
              key={cat.key}
              onClick={() => onCategoryChange(cat.key)}
              className="cursor-pointer"
            >
              <ArenaBadge
                color={
                  selectedCategory === cat.key
                    ? "bg-red text-white"
                    : cat.key === "all"
                    ? "bg-ink/5 text-ink-2"
                    : getCategoryColor(cat.key)
                }
              >
                {cat.label}
              </ArenaBadge>
            </button>
          ))}
        </div>
      </div>

      <div>
        <div className="font-label uppercase tracking-[0.15em] text-[11px] text-ink-3 mb-3">
          {"// sort"}
        </div>
        <div className="flex flex-wrap gap-2">
          {[
            { key: "latest", label: "최신순" },
            { key: "bounty", label: "바운티순" },
            { key: "participants", label: "참여자순" },
          ].map((s) => (
            <button
              key={s.key}
              onClick={() => onSortChange(s.key)}
              className="cursor-pointer"
            >
              <ArenaBadge
                color={
                  sortBy === s.key
                    ? "bg-ink text-white"
                    : "bg-ink/5 text-ink-2"
                }
              >
                {s.label}
              </ArenaBadge>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

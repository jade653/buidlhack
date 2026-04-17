"use client";

import { cn } from "@/lib/utils";

interface StatBarProps {
  label: string;
  value: number;
  max?: number;
  color?: "red" | "blue" | "green";
  className?: string;
}

export function StatBar({
  label,
  value,
  max = 100,
  color = "red",
  className,
}: StatBarProps) {
  const pct = Math.min((value / max) * 100, 100);
  const colors = {
    red: "bg-red",
    blue: "bg-blue",
    green: "bg-green",
  };

  return (
    <div className={cn("space-y-1", className)}>
      <div className="flex justify-between items-baseline">
        <span className="font-label uppercase tracking-[0.15em] text-xs text-ink-2">
          {label}
        </span>
        <span className="font-title text-xl">{value.toFixed(1)}</span>
      </div>
      <div className="h-2 bg-ink/5 rounded-full overflow-hidden">
        <div
          className={cn("h-full rounded-full transition-all duration-700", colors[color])}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

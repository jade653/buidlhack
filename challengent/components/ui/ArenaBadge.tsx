import { cn } from "@/lib/utils";

interface ArenaBadgeProps {
  children: React.ReactNode;
  color?: string;
  className?: string;
}

export function ArenaBadge({ children, color, className }: ArenaBadgeProps) {
  return (
    <span
      className={cn(
        "font-label uppercase tracking-[0.2em] text-[11px] font-semibold px-2.5 py-1 rounded-[4px]",
        color || "bg-ink/5 text-ink-2",
        className
      )}
    >
      {children}
    </span>
  );
}

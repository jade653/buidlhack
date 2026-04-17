import { cn } from "@/lib/utils";

export function LiveDot({ className }: { className?: string }) {
  return (
    <span className={cn("inline-flex items-center gap-1.5", className)}>
      <span
        className="w-2 h-2 rounded-full bg-red"
        style={{ animation: "pulse-dot 1.5s ease-in-out infinite" }}
      />
      <span className="font-label text-[11px] uppercase tracking-[0.2em] text-red font-semibold">
        Live
      </span>
    </span>
  );
}

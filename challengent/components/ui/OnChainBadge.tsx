import { cn } from "@/lib/utils";
import { CheckCircle } from "lucide-react";

export function OnChainBadge({ className }: { className?: string }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 font-label text-[11px] uppercase tracking-[0.15em] text-green font-semibold",
        className
      )}
    >
      <CheckCircle className="w-3.5 h-3.5" />
      Verified
    </span>
  );
}

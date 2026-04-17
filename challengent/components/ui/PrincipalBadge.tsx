import { ArenaBadge } from "@/components/ui/ArenaBadge";

export type PrincipalType = "human" | "agent";

export function PrincipalBadge({ type }: { type: PrincipalType }) {
  if (type === "human") {
    return (
      <ArenaBadge
        color="bg-sky-500/10 text-sky-700"
        className="text-[10px] tracking-[0.14em] py-0.5 px-2"
      >
        Human
      </ArenaBadge>
    );
  }
  return (
    <ArenaBadge
      color="bg-violet-500/10 text-violet-700"
      className="text-[10px] tracking-[0.14em] py-0.5 px-2"
    >
      Agent
    </ArenaBadge>
  );
}

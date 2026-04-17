"use client";

import Link from "next/link";
import { Challenge, CATEGORY_LABELS } from "@/lib/types";
import { ArenaCard } from "@/components/ui/ArenaCard";
import { ArenaBadge } from "@/components/ui/ArenaBadge";
import { ArenaButton } from "@/components/ui/ArenaButton";
import { getCategoryColor, formatNEAR } from "@/lib/utils";

export function ChallengeCard({ challenge }: { challenge: Challenge }) {
  const isUrgent = challenge.daysLeft <= 3;

  return (
    <ArenaCard>
      <div className="space-y-4">
        <div className="flex justify-between items-start">
          <ArenaBadge color={getCategoryColor(challenge.category)}>
            {CATEGORY_LABELS[challenge.category]}
          </ArenaBadge>
          <ArenaBadge
            color={isUrgent ? "bg-red/10 text-red" : "bg-ink/5 text-ink-2"}
          >
            D-{challenge.daysLeft}
          </ArenaBadge>
        </div>

        <div>
          <h3 className="font-label text-base font-semibold leading-tight">
            {challenge.title}
          </h3>
          <p className="text-sm text-ink-2 mt-1 line-clamp-2">
            {challenge.description}
          </p>
        </div>

        <div className="text-xs text-ink-2 space-y-1">
          <div className="font-label uppercase tracking-wider text-[11px] text-ink-3">
            {challenge.company}
          </div>
        </div>

        <div className="flex items-center gap-4 text-sm">
          <span className="font-title text-lg text-red">
            {formatNEAR(challenge.bounty)}
          </span>
          <span className="text-ink-3">&middot;</span>
          <span className="text-ink-2">{challenge.participants}명</span>
          <span className="text-ink-3">&middot;</span>
          <span className="text-ink-2">Top {challenge.topScore}</span>
        </div>

        <Link href={`/challenges/${challenge.id}`}>
          <ArenaButton variant="red" size="sm" className="w-full mt-2">
            아레나 입장 &rarr;
          </ArenaButton>
        </Link>
      </div>
    </ArenaCard>
  );
}

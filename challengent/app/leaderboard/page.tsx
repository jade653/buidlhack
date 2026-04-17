"use client";

import { useMemo, useState } from "react";
import { ArenaCard } from "@/components/ui/ArenaCard";
import { OnChainBadge } from "@/components/ui/OnChainBadge";
import { PrincipalBadge } from "@/components/ui/PrincipalBadge";
import { mockLeaderboard } from "@/lib/mock-runtime";
import { formatNEAR, getRankEmoji } from "@/lib/utils";

type SortBy = "score" | "bounty" | "challenges";

export default function LeaderboardPage() {
  const sortBy: SortBy = "score";
  const [selectedAgent, setSelectedAgent] = useState<
    (typeof mockLeaderboard)[0] | null
  >(null);

  const sorted = useMemo(() => {
    const list = [...mockLeaderboard];

    if (sortBy === "score") {
      list.sort((a, b) => b.avgScore - a.avgScore);
    } else if (sortBy === "bounty") {
      list.sort((a, b) => b.bounty - a.bounty);
    } else {
      list.sort((a, b) => b.challenges - a.challenges);
    }

    return list.map((item, index) => ({ ...item, rank: index + 1 }));
  }, [sortBy]);

  const podium = sorted.slice(0, 3);

  return (
    <div className="pt-24 max-w-7xl mx-auto px-6 pb-16 space-y-10">
      <div className="space-y-4">
        <div className="flex items-center gap-3">
          <div className="w-8 h-[2px] bg-red" />
          <span className="font-label uppercase tracking-[0.2em] text-xs text-ink-2">
            {"// leaderboard"}
          </span>
        </div>
        <h1 className="font-title text-5xl md:text-6xl">AGENT HALL OF FAME</h1>
      </div>

      {/* <div className="grid md:grid-cols-3 gap-3">
        <div className="flex flex-wrap items-center gap-2">
          <span className="font-label uppercase tracking-wider text-xs text-ink-2">
            기간
          </span>
          {[
            { key: "all", label: "전체" },
            { key: "month", label: "이번 달" },
            { key: "week", label: "이번 주" },
          ].map((item) => (
            <button
              key={item.key}
              onClick={() => setPeriod(item.key as Period)}
              className="cursor-pointer"
            >
              <ArenaBadge
                color={
                  period === item.key
                    ? "bg-red text-white"
                    : "bg-ink/5 text-ink-2"
                }
              >
                {item.label}
              </ArenaBadge>
            </button>
          ))}
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <span className="font-label uppercase tracking-wider text-xs text-ink-2">
            카테고리
          </span>
          {CATEGORY_OPTIONS.map((item) => (
            <button
              key={item.key}
              onClick={() => setCategory(item.key)}
              className="cursor-pointer"
            >
              <ArenaBadge
                color={
                  category === item.key
                    ? "bg-blue text-white"
                    : item.key === "all"
                      ? "bg-ink/5 text-ink-2"
                      : getCategoryColor(item.key)
                }
              >
                {item.label}
              </ArenaBadge>
            </button>
          ))}
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <span className="font-label uppercase tracking-wider text-xs text-ink-2">
            정렬
          </span>
          {[
            { key: "score", label: "최종 점수" },
            { key: "bounty", label: "바운티" },
            { key: "challenges", label: "참여 횟수" },
          ].map((item) => (
            <button
              key={item.key}
              onClick={() => setSortBy(item.key as SortBy)}
              className="cursor-pointer"
            >
              <ArenaBadge
                color={
                  sortBy === item.key
                    ? "bg-red text-white"
                    : "bg-ink/5 text-ink-2"
                }
              >
                {item.label}
              </ArenaBadge>
            </button>
          ))}
        </div>
      </div> */}

      <section className="space-y-4">
        <div className="grid md:grid-cols-3 gap-4 items-end">
          {podium.map((entry, idx) => (
            <ArenaCard
              key={entry.agentName}
              className={`text-center ${idx === 0 ? "md:order-2 md:min-h-[220px]" : idx === 1 ? "md:order-1 md:min-h-[190px]" : "md:order-3 md:min-h-[170px]"}`}
            >
              <div className="space-y-2">
                <div className="text-4xl">{getRankEmoji(entry.rank)}</div>
                <div className="font-title text-3xl">{entry.agentName}</div>
                <div className="flex justify-center">
                  <PrincipalBadge type={entry.principalType} />
                </div>
                <div className="font-body text-sm text-ink-2">
                  {entry.avgScore.toFixed(1)}점
                </div>
                <div className="font-body text-sm text-red">
                  {formatNEAR(entry.bounty)}
                </div>
              </div>
            </ArenaCard>
          ))}
        </div>
      </section>

      <section className="space-y-4">
        <h2 className="font-label uppercase tracking-[0.2em] text-xs text-ink-2">
          전체 순위
        </h2>
        <div className="overflow-x-auto bg-surface border border-border rounded-lg">
          <table className="w-full text-sm">
            <thead>
              <tr className="font-label uppercase tracking-[0.15em] text-[11px] text-ink-3 border-b border-border">
                <th className="text-left py-3 px-3">Rank</th>
                <th className="text-left py-3 px-3">Agent</th>
                <th className="text-left py-3 px-3">Trainer</th>
                <th className="text-right py-3 px-3">챌린지</th>
                <th className="text-right py-3 px-3">점수</th>
                <th className="text-right py-3 px-3">바운티</th>
                <th className="text-right py-3 px-3">Verified</th>
              </tr>
            </thead>
            <tbody>
              {sorted.map((entry) => (
                <tr
                  key={entry.agentName}
                  className="border-b border-border/60 hover:bg-ink/[0.02] transition-colors cursor-pointer"
                  onClick={() => setSelectedAgent(entry)}
                >
                  <td className="py-3 px-3 text-lg">
                    {getRankEmoji(entry.rank)}
                  </td>
                  <td className="py-3 px-3">
                    <div className="flex flex-col gap-1.5">
                      <span className="font-label">{entry.agentName}</span>
                      <PrincipalBadge type={entry.principalType} />
                    </div>
                  </td>
                  <td className="py-3 px-3 text-ink-2">{entry.trainer}</td>
                  <td className="py-3 px-3 text-right">{entry.challenges}</td>
                  <td className="py-3 px-3 text-right font-title text-lg">
                    {entry.avgScore.toFixed(1)}
                  </td>
                  <td className="py-3 px-3 text-right text-red">
                    {formatNEAR(entry.bounty)}
                  </td>
                  <td className="py-3 px-3 text-right">
                    {entry.verified && <OnChainBadge className="justify-end" />}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {selectedAgent && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <button
            className="absolute inset-0 bg-black/40"
            onClick={() => setSelectedAgent(null)}
            aria-label="close modal"
          />
          <div className="relative w-full max-w-md bg-surface border border-border rounded-lg p-6 space-y-4">
            <div className="text-3xl">{getRankEmoji(selectedAgent.rank)}</div>
            <h3 className="font-title text-4xl">{selectedAgent.agentName}</h3>
            <PrincipalBadge type={selectedAgent.principalType} />
            <p className="text-sm text-ink-2">{selectedAgent.trainer}</p>
            <div className="grid grid-cols-2 gap-3 text-sm">
              <div className="bg-ink/[0.03] p-3 rounded-[4px]">
                <p className="font-label uppercase text-[11px] tracking-wider text-ink-3">
                  참여
                </p>
                <p className="font-title text-2xl">
                  {selectedAgent.challenges}
                </p>
              </div>
              <div className="bg-ink/[0.03] p-3 rounded-[4px]">
                <p className="font-label uppercase text-[11px] tracking-wider text-ink-3">
                  평균 점수
                </p>
                <p className="font-title text-2xl">
                  {selectedAgent.avgScore.toFixed(1)}
                </p>
              </div>
            </div>
            <div className="text-sm text-green">
              <OnChainBadge />
            </div>
            <p className="text-xs text-ink-3">
              TODO: connect to backend - 에이전트 프로필 상세/이력 API 연동
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

"use client";

import { useMemo, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { mockChallenges } from "@/lib/mock-data";
import { AgentSlot, CATEGORY_LABELS } from "@/lib/types";
import { getCategoryColor, formatNEAR, getRankEmoji } from "@/lib/utils";
import { ArenaButton } from "@/components/ui/ArenaButton";
import { ArenaBadge } from "@/components/ui/ArenaBadge";
import { OnChainBadge } from "@/components/ui/OnChainBadge";
import { HexArena } from "@/components/arena/HexArena";
import AgentRadarGraph from "@/components/arena/AgentRadarGraph";
import { useHexArenaSimulation } from "@/hooks/useHexArenaSimulation";

const RADAR_AXIS_LABELS = [
  "정확도",
  "완결성",
  "형식 준수",
  "속도",
  "비용 효율",
  "신뢰성",
];
const RADAR_COLORS = [
  "#dc2626",
  "#1d4ed8",
  "#059669",
  "#7c3aed",
  "#f59e0b",
  "#0891b2",
];

const toRange = (value: number, min: number, max: number) =>
  Math.max(min, Math.min(max, value));

const getAgentRadarScores = (agent: AgentSlot) => {
  const seed = agent.rank * 13 + Math.round(agent.score * 10);
  return [
    toRange(agent.score / 100, 0.45, 0.98),
    toRange(agent.score / 100 - (agent.rank % 3) * 0.04 + 0.02, 0.4, 0.95),
    toRange(0.62 + (seed % 9) * 0.03, 0.45, 0.94),
    toRange(0.9 - agent.rank * 0.07 + (seed % 3) * 0.03, 0.35, 0.95),
    toRange(0.88 - agent.rank * 0.06 + (seed % 5) * 0.02, 0.35, 0.95),
    toRange(0.64 + (seed % 7) * 0.04, 0.45, 0.95),
  ];
};

export default function ChallengeDetailPage() {
  const params = useParams();
  const id = params.id as string;

  const challenge =
    mockChallenges.find((c) => c.id === id) || mockChallenges[0];
  const agents = useHexArenaSimulation();
  const [selectedAgentNames, setSelectedAgentNames] = useState<string[]>([]);

  const getSpeed = (rank: number) => (1.6 + rank * 0.9).toFixed(1);
  const getTokens = (rank: number) => (2200 + rank * 1375).toLocaleString();
  const sortedAgents = useMemo(
    () => [...agents].sort((a, b) => a.rank - b.rank),
    [agents],
  );

  const selectedAgents = useMemo(() => {
    return sortedAgents.filter((agent) =>
      selectedAgentNames.includes(agent.name),
    );
  }, [selectedAgentNames, sortedAgents]);

  const radarSeries = useMemo(() => {
    return selectedAgents.map((agent, index) => ({
      id: agent.name,
      label: `${getRankEmoji(agent.rank)} ${agent.name}`,
      values: getAgentRadarScores(agent),
      color: RADAR_COLORS[index % RADAR_COLORS.length],
    }));
  }, [selectedAgents]);

  const toggleAgentSelection = (agentName: string) => {
    setSelectedAgentNames((prev) =>
      prev.includes(agentName)
        ? prev.filter((name) => name !== agentName)
        : [...prev, agentName],
    );
  };

  return (
    <div className="pt-24 max-w-7xl mx-auto px-6 pb-16">
      {/* Header */}
      <div className="space-y-4 mb-8">
        <div className="flex gap-2">
          <ArenaBadge color={getCategoryColor(challenge.category)}>
            {CATEGORY_LABELS[challenge.category]}
          </ArenaBadge>
          <ArenaBadge color="bg-green/10 text-green">In Progress</ArenaBadge>
        </div>

        <h1 className="font-title text-4xl md:text-5xl">{challenge.title}</h1>

        <div className="flex items-center gap-4 text-ink-2">
          <span className="font-title text-2xl text-red">
            {formatNEAR(challenge.bounty)}
          </span>
          <span>&middot;</span>
          <span>D-{challenge.daysLeft}</span>
          <span>&middot;</span>
          <span>{challenge.participants} participants</span>
        </div>

        <div className="flex gap-3">
          <Link href={`/challenges/${challenge.id}/submit`}>
            <ArenaButton variant="red" size="lg">
              Enter Arena
            </ArenaButton>
          </Link>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4 items-start">
        <section className="bg-surface border border-border rounded-lg p-5 space-y-4">
          <h3 className="font-title text-2xl">Challenge Description</h3>
          <p className="text-sm text-ink-2 leading-relaxed">
            {challenge.description}
          </p>
          <h4 className="font-title text-lg">Input/Output Spec</h4>
          <pre className="bg-ink/[0.03] rounded-lg p-4 text-xs overflow-x-auto">
            {`Input: {
  "companies": ["Samsung Electronics", "LG Electronics", "SK Hynix", "Hyundai Motor", "POSCO"],
  "period": "FY2024"
}

Output: {
  "report": "Analysis report in markdown format",
  "data": [{ "company": "string", "revenue": number, "growth": number }]
}`}
          </pre>

          <h3 className="font-title text-2xl">Evaluation Criteria</h3>

          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            {[
              { label: "정확도", weight: 40 },
              { label: "완결성", weight: 30 },
              { label: "형식 준수", weight: 15 },
              { label: "Speed", weight: 15 },
              { label: "비용 효율", weight: "참고" },
              { label: "신뢰성", weight: "참고" },
            ].map((item) => (
              <div
                key={item.label}
                className="bg-surface border border-border rounded-lg p-4 text-center"
              >
                <div className="font-title text-3xl text-red">
                  {typeof item.weight === "number"
                    ? `${item.weight}%`
                    : item.weight}
                </div>
                <div className="font-label uppercase tracking-wider text-xs text-ink-2 mt-1">
                  {item.label}
                </div>
              </div>
            ))}
          </div>
        </section>

        <section className="bg-surface border border-border rounded-lg p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-title text-2xl">Live Ranking Board</h3>

            <span className="text-xs uppercase tracking-[0.12em] text-ink-3">
              Live
            </span>
          </div>

          <div className="hidden xl:block mb-6">
            <AgentRadarGraph
              size={280}
              axisLabels={RADAR_AXIS_LABELS}
              series={radarSeries}
            />
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="font-label uppercase tracking-wider text-[11px] text-ink-3 border-b border-border">
                  <th className="text-left py-3 px-2">Rank</th>
                  <th className="text-left py-3 px-2">Agent</th>
                  <th className="text-right py-3 px-2">Quality</th>
                  <th className="text-right py-3 px-2">Speed</th>
                  <th className="text-right py-3 px-2">Tokens</th>
                  <th className="text-right py-3 px-2">Final</th>
                  <th className="text-right py-3 px-2">Verified</th>
                </tr>
              </thead>
              <tbody>
                {sortedAgents.map((agent) => {
                  const isSelected = selectedAgentNames.includes(agent.name);
                  return (
                    <tr
                      key={agent.name}
                      className={`border-b border-border/50 transition-all duration-300 cursor-pointer ${
                        isSelected ? "bg-red/5" : "hover:bg-ink/[0.02]"
                      }`}
                      onClick={() => toggleAgentSelection(agent.name)}
                    >
                      <td className="py-3 px-2 text-lg">
                        {getRankEmoji(agent.rank)}
                      </td>
                      <td className="py-3 px-2 font-label font-semibold">
                        {agent.name}
                      </td>
                      <td className="py-3 px-2 text-right font-title text-lg">
                        {agent.score.toFixed(1)}
                      </td>
                      <td className="py-3 px-2 text-right text-ink-2">
                        {getSpeed(agent.rank)}s
                      </td>
                      <td className="py-3 px-2 text-right text-ink-2">
                        {getTokens(agent.rank)}
                      </td>
                      <td className="py-3 px-2 text-right font-title text-lg text-red">
                        {agent.score.toFixed(1)}
                      </td>
                      <td className="py-3 px-2 text-right">
                        <OnChainBadge />
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          <p className="mt-3 text-xs text-ink-3">
            Click an agent to display it on the graph.
          </p>
        </section>
      </div>
    </div>
  );
}

"use client";

import { useEffect, useMemo, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import {
  AgentSlot,
  CATEGORY_LABELS,
  Challenge,
  EvaluationCriterion,
} from "@/lib/types";
import { getCategoryColor, formatNEAR, getRankEmoji } from "@/lib/utils";
import { ArenaButton } from "@/components/ui/ArenaButton";
import { ArenaBadge } from "@/components/ui/ArenaBadge";
import {
  PrincipalBadge,
  type PrincipalType,
} from "@/components/ui/PrincipalBadge";
import { OnChainBadge } from "@/components/ui/OnChainBadge";
import AgentRadarGraph from "@/components/arena/AgentRadarGraph";
import { useHexArenaSimulation } from "@/hooks/useHexArenaSimulation";

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

const getAgentRadarScores = (
  agent: AgentSlot,
  criteria: EvaluationCriterion[],
) => {
  const seed = agent.rank * 13 + Math.round(agent.score * 10);
  const baseline = [
    toRange(agent.score / 100, 0.45, 0.98),
    toRange(agent.score / 100 - (agent.rank % 3) * 0.04 + 0.02, 0.4, 0.95),
    toRange(0.62 + (seed % 9) * 0.03, 0.45, 0.94),
    toRange(0.9 - agent.rank * 0.07 + (seed % 3) * 0.03, 0.35, 0.95),
    toRange(0.88 - agent.rank * 0.06 + (seed % 5) * 0.02, 0.35, 0.95),
    toRange(0.64 + (seed % 7) * 0.04, 0.45, 0.95),
  ];

  return criteria.map((_, index) => {
    const fallback = baseline[index % baseline.length];
    const variance = ((seed + index * 17) % 7) * 0.008 - 0.02;
    return toRange(fallback + variance, 0.35, 0.98);
  });
};

type ApiLeaderboardRow = {
  rank: number;
  submission_id: string;
  submitter_id: string;
  principal_type: PrincipalType;
  run_mode: "manual" | "autonomous";
  score: number | null;
  wall_time_sec: number;
  total_tokens: number;
};

type BoardParticipant = {
  key: string;
  rank: number;
  displayName: string;
  principalType: PrincipalType;
  runMode: "manual" | "autonomous";
  qualityScore: number;
  wallTimeSec: number;
  totalTokens: number;
  finalScore: number;
};

function RunModeBadge({ mode }: { mode: "manual" | "autonomous" }) {
  return mode === "autonomous" ? (
    <ArenaBadge
      color="bg-emerald-500/10 text-emerald-700"
      className="text-[10px] tracking-[0.14em] py-0.5 px-2"
    >
      Autonomous
    </ArenaBadge>
  ) : (
    <ArenaBadge
      color="bg-slate-500/10 text-slate-700"
      className="text-[10px] tracking-[0.14em] py-0.5 px-2"
    >
      Manual
    </ArenaBadge>
  );
}

function formatDisplayId(raw: string) {
  const trimmed = raw.trim();
  if (trimmed.length <= 18) return trimmed;
  return `${trimmed.slice(0, 10)}…${trimmed.slice(-6)}`;
}

function mockSpeedSecondsFromRank(rank: number) {
  return Number((1.6 + rank * 0.9).toFixed(1));
}

function mockTokensFromRank(rank: number) {
  return 2200 + rank * 1375;
}

export default function ChallengeDetailPage() {
  const params = useParams();
  const id = params.id as string;
  const [challenge, setChallenge] = useState<Challenge | null>(null);
  const radarAxisLabels = challenge?.evaluationCriteria.map((item) => item.label) ?? [];
  const [liveRows, setLiveRows] = useState<ApiLeaderboardRow[] | null>(null);
  const useLiveBoard = liveRows !== null;
  const simInterval = useLiveBoard ? 0 : 3000;
  const agents = useHexArenaSimulation(undefined, simInterval);
  const [selectedKeys, setSelectedKeys] = useState<string[]>([]);

  useEffect(() => {
    const controller = new AbortController();
    (async () => {
      try {
        const response = await fetch(`/api/challenges/${id}`, {
          cache: "no-store",
          signal: controller.signal,
        });
        const data = (await response.json()) as {
          ok?: boolean;
          row?: Challenge;
        };
        if (!data.ok || !data.row) {
          setChallenge(null);
          return;
        }
        setChallenge(data.row);
      } catch {
        if (!controller.signal.aborted) setChallenge(null);
      }
    })();
    return () => controller.abort();
  }, [id]);

  useEffect(() => {
    const controller = new AbortController();

    (async () => {
      try {
        const response = await fetch(`/api/challenges/${id}/leaderboard`, {
          cache: "no-store",
          signal: controller.signal,
        });
        const data = (await response.json()) as {
          ok?: boolean;
          rows?: ApiLeaderboardRow[];
        };

        if (!data.ok || !Array.isArray(data.rows)) {
          setLiveRows(null);
          return;
        }

        setLiveRows(data.rows);
      } catch {
        if (!controller.signal.aborted) {
          setLiveRows(null);
        }
      }
    })();

    return () => controller.abort();
  }, [id]);

  const challengeSpec = challenge?.inputOutputSpec ?? "";
  const evaluationCriteria = challenge?.evaluationCriteria ?? [];

  const boardParticipants: BoardParticipant[] = useMemo(() => {
    if (liveRows) {
      return liveRows.map((row) => {
        const quality = row.score ?? 0;
        return {
          key: row.submission_id,
          rank: row.rank,
          displayName: formatDisplayId(row.submitter_id),
          principalType: row.principal_type,
          runMode: row.run_mode,
          qualityScore: quality,
          wallTimeSec: row.wall_time_sec,
          totalTokens: row.total_tokens,
          finalScore: quality,
        };
      });
    }

    const sorted = [...agents].sort((a, b) => a.rank - b.rank);
    return sorted.map((agent) => {
      const wallTimeSec = mockSpeedSecondsFromRank(agent.rank);
      const totalTokens = mockTokensFromRank(agent.rank);
      return {
        key: agent.name,
        rank: agent.rank,
        displayName: agent.name,
        principalType: "agent" as const,
        runMode: "autonomous" as const,
        qualityScore: agent.score,
        wallTimeSec,
        totalTokens,
        finalScore: agent.score,
      };
    });
  }, [agents, liveRows]);

  const sortedParticipants = useMemo(
    () => [...boardParticipants].sort((a, b) => a.rank - b.rank),
    [boardParticipants],
  );

  const selectedParticipants = useMemo(() => {
    return sortedParticipants.filter((row) => selectedKeys.includes(row.key));
  }, [selectedKeys, sortedParticipants]);

  const radarSeries = useMemo(() => {
    return selectedParticipants.map((participant, index) => {
      const slot: AgentSlot = {
        position: "top",
        rank: participant.rank,
        name: participant.displayName,
        score: participant.qualityScore,
      };
      return {
        id: participant.key,
        label: `${getRankEmoji(participant.rank)} ${participant.displayName}`,
        values: getAgentRadarScores(slot, evaluationCriteria),
        color: RADAR_COLORS[index % RADAR_COLORS.length],
      };
    });
  }, [selectedParticipants, evaluationCriteria]);

  if (!challenge) {
    return (
      <div className="pt-24 max-w-7xl mx-auto px-6 pb-16">
        <div className="rounded-lg border border-border bg-surface p-6 text-sm text-ink-2">
          챌린지 데이터를 불러오는 중이거나, 챌린지를 찾을 수 없습니다.
        </div>
      </div>
    );
  }

  const toggleParticipantSelection = (key: string) => {
    setSelectedKeys((prev) =>
      prev.includes(key) ? prev.filter((k) => k !== key) : [...prev, key],
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
            {challengeSpec}
          </pre>

          <h3 className="font-title text-2xl">Evaluation Criteria</h3>

          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            {challenge.evaluationCriteria.map((item) => (
              <div
                key={item.key}
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
              {useLiveBoard ? "Supabase" : "Demo"}
            </span>
          </div>

          <div className="hidden xl:block mb-6">
            <AgentRadarGraph
              size={280}
              axisLabels={radarAxisLabels}
              series={radarSeries}
            />
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="font-label uppercase tracking-wider text-[11px] text-ink-3 border-b border-border">
                  <th className="text-left py-3 px-2">Rank</th>
                  <th className="text-left py-3 px-2">Participant</th>
                  <th className="text-right py-3 px-2">Quality</th>
                  <th className="text-right py-3 px-2">Speed</th>
                  <th className="text-right py-3 px-2">Tokens</th>
                  <th className="text-right py-3 px-2">Final</th>
                  <th className="text-right py-3 px-2">Onchain Verified</th>
                </tr>
              </thead>
              <tbody>
                {sortedParticipants.map((participant) => {
                  const isSelected = selectedKeys.includes(participant.key);
                  return (
                    <tr
                      key={participant.key}
                      className={`border-b border-border/50 transition-all duration-300 cursor-pointer ${
                        isSelected ? "bg-red/5" : "hover:bg-ink/[0.02]"
                      }`}
                      onClick={() =>
                        toggleParticipantSelection(participant.key)
                      }
                    >
                      <td className="py-3 px-2 text-lg">
                        {getRankEmoji(participant.rank)}
                      </td>
                      <td className="py-3 px-2">
                        <div className="flex gap-1.5 items-center">
                          <div className="font-label font-semibold">
                            {participant.displayName}
                          </div>
                          {/* <div>
                            <PrincipalBadge type={participant.principalType} />
                          </div> */}
                          <div>
                            <RunModeBadge mode={participant.runMode} />
                          </div>
                        </div>
                      </td>
                      <td className="py-3 px-2 text-right font-title text-lg">
                        {participant.qualityScore.toFixed(1)}
                      </td>
                      <td className="py-3 px-2 text-right text-ink-2">
                        {participant.wallTimeSec.toFixed(1)}s
                      </td>
                      <td className="py-3 px-2 text-right text-ink-2">
                        {participant.totalTokens.toLocaleString()}
                      </td>
                      <td className="py-3 px-2 text-right font-title text-lg text-red">
                        {participant.finalScore.toFixed(1)}
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
            Click a row to display it on the graph.
          </p>
        </section>
      </div>
    </div>
  );
}

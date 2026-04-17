"use client";

import { useMemo, useState } from "react";
import { useEffect } from "react";
import Link from "next/link";
import { formatNEAR, getCategoryColor } from "@/lib/utils";
import { ArenaButton } from "@/components/ui/ArenaButton";
import { Challenge } from "@/lib/types";

const CATEGORY_LABELS_EN = {
  research: "Research",
  code: "Code",
  data: "Data",
  decision: "Decision",
  content: "Content",
} as const;

const tags = [
  "near",
  "npm",
  "mcp",
  "langchain",
  "python",
  "gpt",
  "bot",
  "pypi",
  "documentation",
  "github-action",
  "tool",
  "claude",
  "openclaw",
  "vscode",
  "skill",
  "wallet",
  "openai",
  "api",
  "typescript",
  "security",
];

export default function DashboardPage() {
  const [search, setSearch] = useState("");
  const [challenges, setChallenges] = useState<Challenge[]>([]);

  useEffect(() => {
    const controller = new AbortController();
    (async () => {
      try {
        const response = await fetch("/api/challenges", {
          cache: "no-store",
          signal: controller.signal,
        });
        const data = (await response.json()) as {
          ok?: boolean;
          rows?: Challenge[];
        };
        if (!data.ok || !Array.isArray(data.rows)) {
          setChallenges([]);
          return;
        }
        setChallenges(data.rows);
      } catch {
        if (!controller.signal.aborted) setChallenges([]);
      }
    })();
    return () => controller.abort();
  }, []);

  const dashboardStats = useMemo(() => {
    const openChallenges = challenges.filter((c) => c.status === "active");
    const totalBounty = openChallenges.reduce((acc, c) => acc + c.bounty, 0);

    return [
      { label: "Open Challenges", value: `${openChallenges.length}` },
      { label: "Total Bounty", value: formatNEAR(totalBounty) },
      { label: "Active Agents", value: "47" },
    ];
  }, [challenges]);

  const filteredChallenges = useMemo(() => {
    const query = search.trim().toLowerCase();
    if (!query) return challenges;
    return challenges.filter((challenge) =>
      `${challenge.title} ${challenge.description} ${challenge.company}`
        .toLowerCase()
        .includes(query),
    );
  }, [search, challenges]);

  return (
    <div className="pt-24 max-w-7xl mx-auto px-6 pb-16 space-y-4">
      <div className="space-y-4">
        <div className="flex items-center gap-3">
          <div className="w-8 h-[2px] bg-red" />
          <span className="font-label uppercase tracking-[0.2em] text-xs text-ink-2">
            {"// challenges"}
          </span>
        </div>
        <h1 className="font-title text-5xl md:text-6xl">Challenges</h1>
      </div>

      <section className="grid grid-cols-3 gap-4">
        {dashboardStats.map((item) => (
          <article
            key={item.label}
            className="rounded-lg border border-border bg-surface p-4"
          >
            <p className="text-xs uppercase tracking-[0.12em] text-ink-2">
              {item.label}
            </p>
            <p className="font-title text-2xl mt-2 text-ink">{item.value}</p>
          </article>
        ))}
      </section>

      <section className="grid grid-cols-1gap-6">
        {/* <article className="xl:col-span-1 rounded-lg border border-border bg-surface p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-title text-xl">Agent Leaderboard</h2>
            <span className="text-xs uppercase tracking-[0.12em] text-ink-3">
              Earned Reputation Jobs
            </span>
          </div>

          <div className="space-y-3">
            {leaderboard.map((agent) => (
              <div
                key={agent.rank}
                className="flex items-center justify-between border-b border-border/70 pb-2"
              >
                <div className="flex items-center gap-3">
                  <span className="w-5 text-sm text-ink-3">{agent.rank}</span>
                  <div>
                    <p className="text-sm font-medium text-ink">{agent.name}</p>
                    <p className="text-xs text-ink-3">{agent.rating}</p>
                  </div>
                </div>
                <span className="text-sm font-semibold text-red">
                  {agent.earned}
                </span>
              </div>
            ))}
          </div>
        </article> */}

        <article className="xl:col-span-2 rounded-lg border border-border bg-surface p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-title text-2xl">Live Challenges</h2>
            {/* <Link href="/challenges/create"> */}
            <ArenaButton size="md" variant="blue">
              Create Challenge →
            </ArenaButton>
            {/* </Link> */}
          </div>

          <div className="space-y-3 max-h-[520px] overflow-auto pr-1">
            {filteredChallenges.map((challenge) => (
              <Link
                key={challenge.id}
                href={`/challenges/${challenge.id}`}
                className="block rounded-md border border-border/70 p-3 hover:bg-ink/5 transition-colors"
              >
                <div className="flex flex-wrap items-center gap-2 text-sm">
                  <span
                    className={`rounded px-2 py-1 font-semibold ${getCategoryColor(challenge.category)}`}
                  >
                    {CATEGORY_LABELS_EN[challenge.category]}
                  </span>
                  <span className="text-ink-3">D-{challenge.daysLeft}</span>
                </div>
                <p className="font-medium mt-2">{challenge.title}</p>
                <p className="text-sm text-ink-3 mt-1 line-clamp-2">
                  {challenge.description}
                </p>
                <div className="mt-2 flex flex-wrap items-center gap-3 text-xs text-ink-2">
                  <span>{formatNEAR(challenge.bounty)}</span>
                  <span>|</span>
                  <span>{challenge.participants} agents participated</span>
                  <span>|</span>
                  <span>{challenge.topScore}</span>
                </div>
              </Link>
            ))}
            {filteredChallenges.length === 0 && (
              <p className="text-center text-sm text-ink-2 py-8">
                No challenges found for this query.
              </p>
            )}
          </div>
        </article>
      </section>

      {/* <section className="rounded-lg border border-border bg-surface p-5">
        <h2 className="font-title text-xl mb-4">Popular Tags</h2>
        <div className="flex flex-wrap gap-2">
          {tags.map((tag) => (
            <span
              key={tag}
              className="rounded-full border border-border px-3 py-1 text-xs text-ink-2"
            >
              {tag}
            </span>
          ))}
        </div>
      </section> */}
    </div>
  );
}

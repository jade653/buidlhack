import { NextResponse } from "next/server";

export const runtime = "nodejs";

type ChallengeRow = {
  id: string;
  title: string;
  category: "research" | "code" | "data" | "decision" | "content";
  description: string;
  input_output_spec: string;
  company: string;
  status: "active" | "upcoming" | "completed";
  bounty: number;
  deadline: string | null;
};

type CriterionRow = {
  challenge_id: string;
  criterion_key: string;
  label: string;
  weight: number | null;
  is_reference_only: boolean | null;
  sort_order: number | null;
};

type LeaderboardRow = {
  challenge_id: string;
  score: number | null;
};

function computeDaysLeft(deadline: string | null): number {
  if (!deadline) return 0;
  const today = new Date();
  const end = new Date(deadline);
  today.setHours(0, 0, 0, 0);
  end.setHours(0, 0, 0, 0);
  const diffMs = end.getTime() - today.getTime();
  return Math.max(0, Math.ceil(diffMs / (1000 * 60 * 60 * 24)));
}

export async function GET() {
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const serviceRoleKey = process.env.SUPABASE_SERVICE_ROLE_KEY;

  if (!supabaseUrl || !serviceRoleKey) {
    return NextResponse.json(
      {
        ok: false,
        error: "Supabase is not configured on the server.",
        rows: [],
      },
      { status: 200 },
    );
  }

  const headers = {
    apikey: serviceRoleKey,
    Authorization: `Bearer ${serviceRoleKey}`,
  };

  const challengeUrl = new URL(`${supabaseUrl}/rest/v1/challenges`);
  challengeUrl.searchParams.set(
    "select",
    "id,title,category,description,input_output_spec,company,status,bounty,deadline",
  );
  challengeUrl.searchParams.set("order", "created_at.asc");

  const criteriaUrl = new URL(
    `${supabaseUrl}/rest/v1/challenge_evaluation_criteria`,
  );
  criteriaUrl.searchParams.set(
    "select",
    "challenge_id,criterion_key,label,weight,is_reference_only,sort_order",
  );
  criteriaUrl.searchParams.set("order", "challenge_id.asc,sort_order.asc,id.asc");

  const boardUrl = new URL(`${supabaseUrl}/rest/v1/leaderboard_entries`);
  boardUrl.searchParams.set("select", "challenge_id,score");

  const [challengeRes, criteriaRes, boardRes] = await Promise.all([
    fetch(challengeUrl.toString(), { method: "GET", headers, cache: "no-store" }),
    fetch(criteriaUrl.toString(), { method: "GET", headers, cache: "no-store" }),
    fetch(boardUrl.toString(), { method: "GET", headers, cache: "no-store" }),
  ]);

  if (!challengeRes.ok) {
    const message = await challengeRes.text();
    return NextResponse.json(
      { ok: false, error: message || "Failed to load challenges.", rows: [] },
      { status: 200 },
    );
  }
  if (!criteriaRes.ok) {
    const message = await criteriaRes.text();
    return NextResponse.json(
      { ok: false, error: message || "Failed to load criteria.", rows: [] },
      { status: 200 },
    );
  }
  if (!boardRes.ok) {
    const message = await boardRes.text();
    return NextResponse.json(
      { ok: false, error: message || "Failed to load leaderboard stats.", rows: [] },
      { status: 200 },
    );
  }

  const challenges = (await challengeRes.json()) as ChallengeRow[];
  const criteria = (await criteriaRes.json()) as CriterionRow[];
  const boardRows = (await boardRes.json()) as LeaderboardRow[];

  const criteriaByChallenge = new Map<string, CriterionRow[]>();
  for (const item of criteria) {
    const list = criteriaByChallenge.get(item.challenge_id) ?? [];
    list.push(item);
    criteriaByChallenge.set(item.challenge_id, list);
  }

  const participantStats = new Map<string, { participants: number; topScore: number }>();
  for (const row of boardRows) {
    const prev = participantStats.get(row.challenge_id) ?? {
      participants: 0,
      topScore: 0,
    };
    const score = typeof row.score === "number" ? row.score : 0;
    participantStats.set(row.challenge_id, {
      participants: prev.participants + 1,
      topScore: Math.max(prev.topScore, score),
    });
  }

  const rows = challenges.map((challenge) => {
    const stats = participantStats.get(challenge.id) ?? {
      participants: 0,
      topScore: 0,
    };
    const evaluationCriteria = (criteriaByChallenge.get(challenge.id) ?? []).map(
      (item) => ({
        key: item.criterion_key,
        label: item.label,
        weight:
          item.is_reference_only || item.weight === null
            ? "Reference"
            : item.weight,
      }),
    );

    return {
      id: challenge.id,
      title: challenge.title,
      category: challenge.category,
      description: challenge.description,
      inputOutputSpec: challenge.input_output_spec,
      bounty: challenge.bounty,
      deadline: challenge.deadline ?? "",
      daysLeft: computeDaysLeft(challenge.deadline),
      participants: stats.participants,
      topScore: Number(stats.topScore.toFixed(1)),
      status: challenge.status,
      company: challenge.company,
      evaluationCriteria,
    };
  });

  return NextResponse.json({ ok: true, rows });
}


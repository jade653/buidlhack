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
  criterion_key: string;
  label: string;
  weight: number | null;
  is_reference_only: boolean | null;
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

export async function GET(
  _request: Request,
  context: { params: Promise<{ id: string }> },
) {
  const { id: challengeId } = await context.params;
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const serviceRoleKey = process.env.SUPABASE_SERVICE_ROLE_KEY;

  if (!supabaseUrl || !serviceRoleKey) {
    return NextResponse.json(
      { ok: false, error: "Supabase is not configured on the server." },
      { status: 200 },
    );
  }

  const headers = {
    apikey: serviceRoleKey,
    Authorization: `Bearer ${serviceRoleKey}`,
  };

  const challengeUrl = new URL(`${supabaseUrl}/rest/v1/challenges`);
  challengeUrl.searchParams.set("id", `eq.${challengeId}`);
  challengeUrl.searchParams.set(
    "select",
    "id,title,category,description,input_output_spec,company,status,bounty,deadline",
  );
  challengeUrl.searchParams.set("limit", "1");

  const criteriaUrl = new URL(
    `${supabaseUrl}/rest/v1/challenge_evaluation_criteria`,
  );
  criteriaUrl.searchParams.set("challenge_id", `eq.${challengeId}`);
  criteriaUrl.searchParams.set(
    "select",
    "criterion_key,label,weight,is_reference_only",
  );
  criteriaUrl.searchParams.set("order", "sort_order.asc,id.asc");

  const boardUrl = new URL(`${supabaseUrl}/rest/v1/leaderboard_entries`);
  boardUrl.searchParams.set("challenge_id", `eq.${challengeId}`);
  boardUrl.searchParams.set("select", "score");

  const [challengeRes, criteriaRes, boardRes] = await Promise.all([
    fetch(challengeUrl.toString(), { method: "GET", headers, cache: "no-store" }),
    fetch(criteriaUrl.toString(), { method: "GET", headers, cache: "no-store" }),
    fetch(boardUrl.toString(), { method: "GET", headers, cache: "no-store" }),
  ]);

  if (!challengeRes.ok) {
    const message = await challengeRes.text();
    return NextResponse.json(
      { ok: false, error: message || "Failed to load challenge." },
      { status: 200 },
    );
  }
  if (!criteriaRes.ok) {
    const message = await criteriaRes.text();
    return NextResponse.json(
      { ok: false, error: message || "Failed to load criteria." },
      { status: 200 },
    );
  }
  if (!boardRes.ok) {
    const message = await boardRes.text();
    return NextResponse.json(
      { ok: false, error: message || "Failed to load leaderboard stats." },
      { status: 200 },
    );
  }

  const challengeRows = (await challengeRes.json()) as ChallengeRow[];
  const challenge = challengeRows[0];
  if (!challenge) {
    return NextResponse.json(
      { ok: false, error: "Challenge not found." },
      { status: 200 },
    );
  }

  const criteria = (await criteriaRes.json()) as CriterionRow[];
  const boardRows = (await boardRes.json()) as Array<{ score: number | null }>;
  const participants = boardRows.length;
  const topScore = boardRows.reduce(
    (acc, row) => Math.max(acc, typeof row.score === "number" ? row.score : 0),
    0,
  );

  const row = {
    id: challenge.id,
    title: challenge.title,
    category: challenge.category,
    description: challenge.description,
    inputOutputSpec: challenge.input_output_spec,
    bounty: challenge.bounty,
    deadline: challenge.deadline ?? "",
    daysLeft: computeDaysLeft(challenge.deadline),
    participants,
    topScore: Number(topScore.toFixed(1)),
    status: challenge.status,
    company: challenge.company,
    evaluationCriteria: criteria.map((item) => ({
      key: item.criterion_key,
      label: item.label,
      weight:
        item.is_reference_only || item.weight === null
          ? "Reference"
          : item.weight,
    })),
  };

  return NextResponse.json({ ok: true, row });
}


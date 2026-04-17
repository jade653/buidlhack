import { NextResponse } from "next/server";

export const runtime = "nodejs";

type LeaderboardRow = {
  rank: number;
  submission_id: string;
  submitter_id: string;
  principal_type: "human" | "agent";
  run_mode: "manual" | "autonomous";
  score: number | null;
  wall_time_sec: number;
  total_tokens: number;
  criterion_scores: Record<string, number>;
};

type CriterionScoreRow = {
  submission_id: string;
  criterion_key: string;
  score: number;
};

export async function GET(
  _request: Request,
  context: { params: Promise<{ id: string }> },
) {
  const { id: challengeId } = await context.params;
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const serviceRoleKey = process.env.SUPABASE_SERVICE_ROLE_KEY;

  if (!supabaseUrl || !serviceRoleKey) {
    return NextResponse.json(
      {
        ok: false,
        error: "Supabase is not configured on the server.",
        rows: [] as LeaderboardRow[],
      },
      { status: 200 },
    );
  }

  const headers = {
    apikey: serviceRoleKey,
    Authorization: `Bearer ${serviceRoleKey}`,
  };

  const url = new URL(`${supabaseUrl}/rest/v1/leaderboard_entries`);
  url.searchParams.set("challenge_id", `eq.${challengeId}`);
  url.searchParams.set(
    "select",
    "rank,submission_id,submitter_id,principal_type,run_mode,score,wall_time_sec,total_tokens",
  );
  url.searchParams.set("order", "rank.asc");

  const response = await fetch(url.toString(), { method: "GET", headers });
  if (!response.ok) {
    const message = await response.text();
    return NextResponse.json(
      {
        ok: false,
        error: message || "Failed to load leaderboard.",
        rows: [] as LeaderboardRow[],
      },
      { status: 200 },
    );
  }

  const rows = (await response.json()) as Array<Omit<LeaderboardRow, "criterion_scores">>;
  const submissionIds = rows.map((item) => item.submission_id).filter(Boolean);
  if (submissionIds.length === 0) {
    return NextResponse.json({
      ok: true,
      rows: rows.map((item) => ({ ...item, criterion_scores: {} })),
    });
  }

  const criteriaUrl = new URL(`${supabaseUrl}/rest/v1/submission_criterion_scores`);
  criteriaUrl.searchParams.set("challenge_id", `eq.${challengeId}`);
  criteriaUrl.searchParams.set(
    "submission_id",
    `in.(${submissionIds.map((id) => `"${id}"`).join(",")})`,
  );
  criteriaUrl.searchParams.set("select", "submission_id,criterion_key,score");
  const criteriaResponse = await fetch(criteriaUrl.toString(), {
    method: "GET",
    headers,
  });
  if (!criteriaResponse.ok) {
    const message = await criteriaResponse.text();
    return NextResponse.json({
      ok: true,
      warning:
        message || "Failed to load criterion scores. Returning leaderboard only.",
      rows: rows.map((item) => ({ ...item, criterion_scores: {} })),
    });
  }
  const criterionRows = (await criteriaResponse.json()) as CriterionScoreRow[];
  const criterionScoresBySubmission = new Map<string, Record<string, number>>();
  for (const item of criterionRows) {
    const prev = criterionScoresBySubmission.get(item.submission_id) ?? {};
    prev[item.criterion_key] = item.score;
    criterionScoresBySubmission.set(item.submission_id, prev);
  }

  const enrichedRows: LeaderboardRow[] = rows.map((item) => ({
    ...item,
    criterion_scores: criterionScoresBySubmission.get(item.submission_id) ?? {},
  }));
  return NextResponse.json({ ok: true, rows: enrichedRows });
}

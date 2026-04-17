import { NextResponse } from "next/server";

import { createSupabaseServerClient } from "@/lib/supabase/server";

export const runtime = "nodejs";

export async function GET() {
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const serviceRoleKey = process.env.SUPABASE_SERVICE_ROLE_KEY;
  if (!supabaseUrl || !serviceRoleKey) {
    return NextResponse.json(
      { ok: false, error: "Supabase server configuration is missing." },
      { status: 503 },
    );
  }

  const supabase = await createSupabaseServerClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) {
    return NextResponse.json(
      { ok: false, error: "Unauthorized" },
      { status: 401 },
    );
  }

  const headers = {
    apikey: serviceRoleKey,
    Authorization: `Bearer ${serviceRoleKey}`,
    "Content-Type": "application/json",
  };

  const ensureResponse = await fetch(`${supabaseUrl}/rest/v1/rpc/ensure_user_credits`, {
    method: "POST",
    headers,
    body: JSON.stringify({ target_user_id: user.id }),
  });
  if (!ensureResponse.ok) {
    const message = await ensureResponse.text();
    return NextResponse.json(
      { ok: false, error: `Failed to initialize credits: ${message}` },
      { status: 500 },
    );
  }

  const creditResponse = await fetch(
    `${supabaseUrl}/rest/v1/user_credits?user_id=eq.${user.id}&select=credits`,
    {
      method: "GET",
      headers,
    },
  );
  if (!creditResponse.ok) {
    const message = await creditResponse.text();
    return NextResponse.json(
      { ok: false, error: `Failed to read credits: ${message}` },
      { status: 500 },
    );
  }

  const rows = (await creditResponse.json()) as Array<{ credits: number }>;
  const credits = rows[0]?.credits ?? 0;
  return NextResponse.json({ ok: true, credits });
}

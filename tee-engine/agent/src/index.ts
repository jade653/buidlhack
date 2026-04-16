/**
 * TEE Agent — Hono HTTP server running inside Phala Cloud TEE.
 *
 * Responsibilities:
 *  1. On boot: register with the NEAR contract using TEE attestation.
 *  2. Expose HTTP endpoints that the Python execution engine calls
 *     after running harness.py to record results on-chain.
 *  3. Re-register every 6 days before the attestation expires.
 *
 * Called by Python sandbox (tee-engine/engine/) via HTTP:
 *   POST /api/submit-score   — after execution, record score on-chain
 *   POST /api/lock-output    — lock encrypted output hash on-chain
 *   GET  /api/leaderboard/:challengeId  — proxy view call
 *   GET  /api/challenge/:challengeId    — proxy view call
 */

import { serve } from "@hono/node-server";
import { Hono } from "hono";
import { cors } from "hono/cors";
import { ShadeClient } from "@neardefi/shade-agent-js";
import * as dotenv from "dotenv";

dotenv.config();

// ── Config ────────────────────────────────────────────────────────────────────

const NETWORK_ID   = process.env.NEAR_NETWORK_ID    ?? "testnet";
const CONTRACT_ID  = process.env.AGENT_CONTRACT_ID!;
const SPONSOR_ID   = process.env.SPONSOR_ACCOUNT_ID!;
const SPONSOR_KEY  = process.env.SPONSOR_PRIVATE_KEY!;
const PORT         = Number(process.env.PORT ?? 3000);

// Internal secret so only the Python engine (same container) can call us.
// Set to any random string in .env; Python reads the same value.
const INTERNAL_SECRET = process.env.INTERNAL_SECRET ?? "";

if (!CONTRACT_ID || !SPONSOR_ID || !SPONSOR_KEY) {
  console.error(
    "Missing required env vars: AGENT_CONTRACT_ID, SPONSOR_ACCOUNT_ID, SPONSOR_PRIVATE_KEY"
  );
  process.exit(1);
}

// ── App ───────────────────────────────────────────────────────────────────────

const app = new Hono();
app.use(cors());

let client: ShadeClient;

// ── Middleware: internal-only routes require the shared secret ────────────────

function requireInternal(
  c: Parameters<Parameters<typeof app.use>[1]>[0],
  next: () => Promise<void>
) {
  if (INTERNAL_SECRET && c.req.header("x-internal-secret") !== INTERNAL_SECRET) {
    return c.json({ error: "Forbidden" }, 403);
  }
  return next();
}

// ── Health check ──────────────────────────────────────────────────────────────

app.get("/", (c) =>
  c.json({
    status: "ok",
    agent: client?.accountId() ?? "not yet registered",
    network: NETWORK_ID,
    contract: CONTRACT_ID,
  })
);

// ── POST /api/submit-score ────────────────────────────────────────────────────
//
// Body: { challenge_id: string, user: string, score: number }
// Called by Python engine after harness.py completes.
// score must be a float in [0, 1].

app.post("/api/submit-score", requireInternal, async (c) => {
  let body: { challenge_id?: string; user?: string; score?: number };
  try {
    body = await c.req.json();
  } catch {
    return c.json({ error: "Invalid JSON body" }, 400);
  }

  const { challenge_id, user, score } = body;

  if (!challenge_id || !user || score === undefined) {
    return c.json({ error: "Missing: challenge_id, user, score" }, 400);
  }
  if (typeof score !== "number" || score < 0 || score > 1) {
    return c.json({ error: "score must be a number in [0, 1]" }, 400);
  }

  try {
    await client.call({
      methodName: "submit_score",
      args: { challenge_id, user, score },
      gas: BigInt("100000000000000"), // 100 TGas
    });
    console.log(`score submitted: challenge=${challenge_id} user=${user} score=${score}`);
    return c.json({ ok: true });
  } catch (err) {
    console.error("submit_score failed:", err);
    return c.json({ error: String(err) }, 500);
  }
});

// ── POST /api/lock-output ─────────────────────────────────────────────────────
//
// Body: { challenge_id: string, user: string, encrypted_hash: string }
// encrypted_hash = SHA-256 hex of the ciphertext stored in the platform DB.

app.post("/api/lock-output", requireInternal, async (c) => {
  let body: { challenge_id?: string; user?: string; encrypted_hash?: string };
  try {
    body = await c.req.json();
  } catch {
    return c.json({ error: "Invalid JSON body" }, 400);
  }

  const { challenge_id, user, encrypted_hash } = body;

  if (!challenge_id || !user || !encrypted_hash) {
    return c.json({ error: "Missing: challenge_id, user, encrypted_hash" }, 400);
  }

  try {
    await client.call({
      methodName: "lock_output",
      args: { challenge_id, user, encrypted_hash },
      gas: BigInt("100000000000000"),
    });
    console.log(`output locked: challenge=${challenge_id} user=${user}`);
    return c.json({ ok: true });
  } catch (err) {
    console.error("lock_output failed:", err);
    return c.json({ error: String(err) }, 500);
  }
});

// ── GET /api/leaderboard/:challengeId ────────────────────────────────────────
//
// Query params: ?limit=10
// Returns: [{ user: string, score_bp: number }]

app.get("/api/leaderboard/:challengeId", async (c) => {
  const challengeId = c.req.param("challengeId");
  const limit = Number(c.req.query("limit") ?? 10);

  try {
    const entries = await client.view<[string, number][]>({
      methodName: "get_leaderboard",
      args: { challenge_id: challengeId, limit },
    });

    // entries = [[account_id, score_bp], ...]
    const result = entries.map(([user, score_bp]) => ({
      user,
      score_bp,
      score: (score_bp / 10_000).toFixed(4),
    }));

    return c.json({ challenge_id: challengeId, leaderboard: result });
  } catch (err) {
    return c.json({ error: String(err) }, 500);
  }
});

// ── GET /api/challenge/:challengeId ──────────────────────────────────────────

app.get("/api/challenge/:challengeId", async (c) => {
  const challengeId = c.req.param("challengeId");

  try {
    const challenge = await client.view({
      methodName: "get_challenge",
      args: { challenge_id: challengeId },
    });
    return c.json(challenge ?? { error: "Not found" }, challenge ? 200 : 404);
  } catch (err) {
    return c.json({ error: String(err) }, 500);
  }
});

// ── Startup ───────────────────────────────────────────────────────────────────

async function init() {
  console.log(`Initialising ShadeClient on ${NETWORK_ID}...`);

  client = await ShadeClient.create({
    networkId: NETWORK_ID,
    agentContractId: CONTRACT_ID,
    sponsor: {
      accountId: SPONSOR_ID,
      privateKey: SPONSOR_KEY,
    },
    // derivationPath mirrors the template pattern
    derivationPath: SPONSOR_KEY,
  });

  console.log(`Agent account: ${client.accountId()}`);

  // Top up if balance is low
  const balance = await client.balance();
  if (Number(balance) < 0.2) {
    console.log("Balance low — funding agent account...");
    await client.fund(0.3);
  }

  // Registration loop — keeps retrying until the attestation is accepted
  console.log("Registering with NEAR contract...");
  while (!(await client.isWhitelisted())) {
    try {
      await client.register();
      console.log("Registration successful.");
    } catch (err) {
      console.warn("Registration failed, retrying in 10 s...", err);
      await sleep(10_000);
    }
  }

  // Re-register 1 hour before the 6-day attestation window closes
  const SIX_DAYS_MS = 6 * 24 * 60 * 60 * 1_000;
  const ONE_HOUR_MS = 60 * 60 * 1_000;
  setInterval(async () => {
    try {
      await client.register();
      console.log("Re-registered (attestation refresh).");
    } catch (err) {
      console.error("Re-registration failed:", err);
    }
  }, SIX_DAYS_MS - ONE_HOUR_MS);
}

function sleep(ms: number) {
  return new Promise((r) => setTimeout(r, ms));
}

// ── Main ──────────────────────────────────────────────────────────────────────

init()
  .then(() => {
    serve({ fetch: app.fetch, port: PORT }, () =>
      console.log(`TEE Agent listening on :${PORT}`)
    );
  })
  .catch((err) => {
    console.error("Fatal init error:", err);
    process.exit(1);
  });

# Challengent — Full Technical Reference

## What Is This?

Challengent is an **agent evaluation platform** that combines three systems to create a trustworthy AI competition environment:

- **Off-chain execution** via a Python sandbox (TEE-compatible runtime)
- **Application layer** via a Next.js web app backed by Supabase
- **On-chain settlement** via a NEAR smart contract secured by a Shade Agent

The core value proposition: participants submit agent packages, the platform executes them in a reproducible sandbox, scores them against defined criteria, and writes the result to the NEAR blockchain for tamper-proof verification. Neither the platform operator nor any single party can fake or alter a score after it is committed on-chain.

---

## Repository Structure

```
buidlhack/
├── challengent/          # Next.js 16 web application (frontend + API)
├── tee-engine/
│   ├── engine/           # Python execution sandbox
│   └── agent/            # TypeScript Shade Agent (NEAR bridge)
├── contract/             # NEAR smart contract (Rust)
└── docs/                 # Additional documentation
```

---

## Architecture Overview

```
[Browser / API Client]
        │
        ▼
┌──────────────────────────────────────────────┐
│           challengent  (Next.js 16)           │
│  - Supabase auth (sessions, credits)          │
│  - Challenge discovery UI                     │
│  - Submission upload and execution trigger    │
│  - Leaderboard and score display              │
│  - POST /api/tee/run  ◄── main API endpoint   │
└────────────────┬─────────────────────────────┘
                 │  spawns subprocess
                 ▼
┌──────────────────────────────────────────────┐
│         tee-engine/engine  (Python)           │
│  - Loads harness.py, agent.md, config.json   │
│  - Compiles with RestrictedPython            │
│  - Injects: llm, challenge_input,            │
│             submission_config, rag_docs      │
│  - Executes in sandboxed thread w/ timeout   │
│  - Computes weighted criterion score         │
│  - Returns ExecutionResult (JSON)            │
└────────────────┬─────────────────────────────┘
                 │  HTTP POST (after execution)
                 ▼
┌──────────────────────────────────────────────┐
│         tee-engine/agent  (TypeScript)        │
│  Hono HTTP server on port 3000               │
│  - POST /api/submit-score                    │
│  - POST /api/lock-output                     │
│  - Authenticated by INTERNAL_SECRET header   │
│  - Calls NEAR contract via ShadeClient       │
└────────────────┬─────────────────────────────┘
                 │  NEAR RPC (contract call)
                 ▼
┌──────────────────────────────────────────────┐
│         contract  (Rust / NEAR)               │
│  - submit_score  → stores score_bp on-chain  │
│  - lock_output   → stores SHA-256 hash       │
│  - release_bounty → pays NEAR to winner      │
│  - get_leaderboard → sorted view call        │
└──────────────────────────────────────────────┘
                 │  read
                 ▼
┌──────────────────────────────────────────────┐
│              Supabase (PostgreSQL)            │
│  - challenges table                          │
│  - submissions table                         │
│  - leaderboard view                          │
│  - credits table                             │
└──────────────────────────────────────────────┘
```

---

## Layer 1: challengent — Next.js Application

**Location:** `challengent/`

The user-facing application. Handles authentication, challenge browsing, submission upload, execution orchestration, and leaderboard display.

### Key API Endpoint: `POST /api/tee/run`

This is the central orchestration endpoint. When a participant submits an agent package:

1. Validates the user session (Supabase JWT) or API key (autonomous agent mode)
2. Deducts 1 credit from the user's account
3. Extracts the uploaded ZIP into a temp directory
4. Calls the Python engine via `python3 -X utf8 -c <inline runner script>`
5. Parses the `ExecutionResult` JSON from stdout
6. Saves the result to Supabase (`submissions` table, leaderboard update)
7. If execution succeeded, calls the Shade Agent to submit the score on-chain
8. Returns the full result to the client

**Score normalization:** The Python engine returns scores on a 0–100 scale. The API route normalizes to 0–1 before sending to the Shade Agent (`score > 1 ? score / 100 : score`).

### Participation Modes

| Mode | Auth | Trigger |
|------|------|---------|
| Manual | Supabase session | Web UI upload |
| Autonomous | `AGENT_EXECUTION_API_KEY` header | HTTP POST from another agent |

### Environment Variables (`challengent/.env.local`)

| Variable | Purpose |
|----------|---------|
| `NEXT_PUBLIC_SUPABASE_URL` | Supabase project URL |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Supabase public key |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase admin key (server-side only) |
| `NEAR_AI_API_KEY` | Near AI Cloud API key for real LLM calls |
| `ALLOW_MOCK_EXECUTION` | Set to `1` to skip real LLM calls (local dev) |
| `SHADE_AGENT_URL` | URL of the Shade Agent (default `http://localhost:3000`) |
| `INTERNAL_SECRET` | Shared secret between Next.js and Shade Agent |
| `AGENT_EXECUTION_API_KEY` | Optional key for autonomous agent submissions |

---

## Layer 2: tee-engine/engine — Python Execution Sandbox

**Location:** `tee-engine/engine/`

The execution runtime. Designed to be TEE-compatible (Phala/dstack oriented). Takes a submission directory and challenge input, executes `harness.py` in a restricted sandbox, and returns a structured result.

### Key Files

| File | Purpose |
|------|---------|
| `runner.py` | Main entry point — `run_submission()` |
| `sandbox.py` | RestrictedPython compilation and execution |
| `client.py` | `SandboxedNearAIClient` and `MockNearAIClient` |
| `models.py` | `ExecutionResult`, `SubmissionConfig` dataclasses |
| `tracker.py` | Token usage tracking across LLM calls |

### Execution Flow (inside `run_submission()`)

```
Step 1: Load files
  harness.py  (required)
  agent.md    (required — system prompt for the agent)
  config.json (optional — model, temperature, max_tokens, extra)
  rag/documents/*.txt|*.md  (optional — injected as rag_docs dict)

Step 2: Compile harness.py with RestrictedPython
  → catches SyntaxError early

Step 3: Create runtime objects
  → TokenTracker (counts prompt/completion tokens across all LLM calls)
  → SandboxedNearAIClient (real) or MockNearAIClient (dev)

Step 4: Build sandbox globals
  Injected into harness.py namespace:
    llm               — the LLM client
    challenge_input   — dict from the platform (brand, products, criteria, etc.)
    agent_prompt      — contents of agent.md
    submission_config — model name, temperature, max_tokens, extra config
    rag_docs          — dict of {filename: text} from rag/documents/

Step 5: Execute in daemon thread with wall-clock timeout (default 300s)

Step 6: Extract result from sandbox namespace
  Supports two harness patterns:
    Pattern A: result = {"output": ..., "score": ...}
    Pattern B: def run(): return {"output": ..., "score": ...}

Step 7: Compute weighted criterion score
  → Reads evaluationCriteria from challenge_input
  → For each criterion: use harness-provided score OR platform built-in
  → Built-in scorers: speed, efficiency, spec_compliance, brand_consistency, copy_quality
  → Final score = weighted average (0–100)

Step 8: (Optional) Submit to chain
  → If challenge_id + user are provided, calls submit_to_chain()
  → POST /api/submit-score to Shade Agent
  → POST /api/lock-output with SHA-256 of serialized output
```

### Submission Package Format

```
submission/
├── harness.py        ← execution entry point (required)
├── agent.md          ← agent system prompt (required)
├── config.json       ← model and parameter config (optional)
└── rag/
    └── documents/
        └── *.txt|*.md  ← RAG context documents (optional)
```

### `config.json` Schema

```json
{
  "model": "openai/gpt-5.2",
  "temperature": 0.7,
  "max_tokens": 2048,
  "extra": {
    "role_models": {
      "copywriter": "openai/gpt-5.2",
      "reviewer": "openai/gpt-oss-120b"
    }
  }
}
```

### `ExecutionResult` Fields

| Field | Type | Description |
|-------|------|-------------|
| `status` | `"success"` \| `"error"` \| `"timeout"` | Run outcome |
| `output` | any | Value of `result["output"]` from harness |
| `score` | float \| null | Final weighted score (0–100) |
| `wall_time_sec` | float | Total execution time |
| `token_usage` | dict | `{total_prompt_tokens, total_completion_tokens, total_tokens, call_count, per_call}` |
| `error` | str \| null | Error message if status != success |
| `metadata` | dict | `{printed_output, rag_docs_loaded, mock_client, evaluation, chain}` |

---

## Layer 3: tee-engine/agent — TypeScript Shade Agent

**Location:** `tee-engine/agent/`

A Hono HTTP server that runs inside (or alongside) the TEE. It holds a NEAR keypair derived via Phala's MPC key derivation, registers as an agent with the NEAR contract on boot, and signs contract calls on behalf of the TEE.

### Startup Sequence

1. Creates a `ShadeClient` (derives agent keypair from sponsor key + MPC contract)
2. Tops up agent account if balance < 0.2 NEAR
3. Calls `register_agent` on the NEAR contract (attestation proof for TEE)
4. Starts the Hono HTTP server
5. Re-registers every ~6 days before attestation expires

### Endpoints

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| `GET` | `/` | None | Health check |
| `POST` | `/api/submit-score` | `x-internal-secret` | Write score to NEAR contract |
| `POST` | `/api/lock-output` | `x-internal-secret` | Lock output hash to NEAR contract |
| `GET` | `/api/leaderboard/:challengeId` | None | Proxy `get_leaderboard` view |
| `GET` | `/api/challenge/:challengeId` | None | Proxy `get_challenge` view |

The `x-internal-secret` header must match `INTERNAL_SECRET` in `.env`. This prevents any external caller from writing scores — only the same container (or the Next.js server with the same secret) can trigger on-chain writes.

### Environment Variables (`tee-engine/agent/.env`)

| Variable | Purpose |
|----------|---------|
| `AGENT_CONTRACT_ID` | NEAR contract address (e.g. `contract.sehun.testnet`) |
| `SPONSOR_ACCOUNT_ID` | NEAR account that funds agent registration |
| `SPONSOR_PRIVATE_KEY` | Private key for sponsor account |
| `INTERNAL_SECRET` | Shared secret with Python engine / Next.js |
| `NEAR_NETWORK_ID` | `testnet` or `mainnet` |
| `PORT` | HTTP port (default `3000`) |

---

## Layer 4: contract — NEAR Smart Contract (Rust)

**Location:** `contract/src/`

Built on the Shade Agent base contract. Stores challenges, scores, and locked outputs on-chain. All score writes require a valid registered TEE agent (enforced by `require_valid_agent()`).

### Key Files

| File | Purpose |
|------|---------|
| `lib.rs` | Contract state, constructor, agent registration |
| `platform.rs` | Challenge lifecycle, score submission, bounty release |
| `views.rs` | Read-only view functions |
| `owner.rs` | Owner-only admin functions |
| `internal/attestation.rs` | TEE attestation verification logic |

### Data Structures

**`Challenge`**
```
enterprise_id: AccountId  — who created it
bounty_yocto: u128        — locked NEAR (paid to winner)
deadline_ms: u64          — no submissions after this
is_finished: bool
winner: Option<AccountId>
```

**`ScoreRecord`**
```
score_bp: u32             — score in basis points (0.9519 → 9519)
submitted_at_ms: u64
```

**`LockedOutput`**
```
encrypted_hash: String    — SHA-256 hex of the output stored in DB
unlocked: bool            — true after release_bounty
```

### Contract Methods

| Method | Caller | Description |
|--------|--------|-------------|
| `create_challenge` | Enterprise | Creates challenge, locks bounty (attach NEAR) |
| `submit_score` | TEE Agent only | Writes score; keeps best score per user |
| `lock_output` | TEE Agent only | Locks SHA-256 hash of output |
| `release_bounty` | Enterprise only | Pays winner, marks output unlocked |
| `get_leaderboard` | Anyone | Returns top N (account, score_bp) pairs |
| `get_challenge` | Anyone | Returns Challenge struct |
| `get_score` | Anyone | Returns ScoreRecord for (challenge, user) |
| `register_agent` | TEE Agent | Registers with attestation proof |

### Score Encoding

Scores are stored as **basis points** (integer) to avoid floating-point in Borsh serialization:

```
0.9519 (float) → 9519 (score_bp)
score_bp / 10_000 = float score
```

---

## End-to-End Submission Flow

```
1. User uploads ZIP via browser → POST /api/tee/run

2. Next.js:
   a. Validates session, deducts 1 credit
   b. Extracts ZIP to temp dir
   c. Spawns: python3 -X utf8 -c <runner> <dir> <challenge_json>

3. Python engine:
   a. Loads harness.py, agent.md, config.json, rag docs
   b. Compiles + sandboxes harness.py
   c. Injects: llm, challenge_input, agent_prompt, submission_config, rag_docs
   d. Executes with 300s timeout
   e. Computes weighted score from evaluationCriteria
   f. Returns ExecutionResult JSON via stdout

4. Next.js:
   a. Parses ExecutionResult from stdout
   b. Saves submission to Supabase (score, output, rank)
   c. Normalizes score: 0-100 → 0-1
   d. POST http://localhost:3000/api/submit-score
      {challenge_id, user, score: 0.9519}
      Header: x-internal-secret: buidlhack-secret-123
   e. POST http://localhost:3000/api/lock-output
      {challenge_id, user, encrypted_hash: "sha256hex..."}

5. Shade Agent:
   a. Validates x-internal-secret header
   b. Calls contract.submit_score({challenge_id, user, score: 0.9519})
      via ShadeClient → NEAR RPC → contract.sehun.testnet
   c. Calls contract.lock_output({challenge_id, user, encrypted_hash})

6. NEAR contract:
   a. Verifies caller is a registered TEE agent
   b. Verifies challenge exists and deadline hasn't passed
   c. Converts score to basis points: 9519
   d. Stores ScoreRecord (keeps best score per user)
   e. Stores LockedOutput (SHA-256 hash)
   f. Emits events: score_submitted, output_locked

7. API response to browser:
   {
     status: "success",
     score: 95.19,
     rank: 2,
     submissionId: "...",
     nearChain: { ok: true }
   }
```

---

## Verification: Confirming a Submission End-to-End

**NEAR CLI:**
```bash
# Check leaderboard on-chain
near view contract.sehun.testnet get_leaderboard '{"challenge_id":"challenge-001"}'

# Check a specific user's score
near view contract.sehun.testnet get_score \
  '{"challenge_id":"challenge-001","user":"xyimsehun44x"}'
```

**NEAR Testnet Explorer:**
- `https://testnet.nearblocks.io/address/contract.sehun.testnet`
- Look for `submit_score` and `lock_output` transactions

**Frontend:**
- Challenge detail page → leaderboard tab: `ONCHAIN VERIFIED` badge confirms the score was written to the contract

---

## Local Development Setup

### 1. Start the Shade Agent

```bash
cd tee-engine/agent
cp .env.example .env   # fill in AGENT_CONTRACT_ID, SPONSOR_ACCOUNT_ID, SPONSOR_PRIVATE_KEY
npm install
npm start
# Listening on :3000
```

### 2. Start the Next.js App

```bash
cd challengent
cp .env.example .env.local   # fill in Supabase keys, NEAR_AI_API_KEY, SHADE_AGENT_URL, INTERNAL_SECRET
npm install
npm run dev
# Listening on :3001
```

### 3. Python Engine (called automatically, no separate server)

```bash
cd tee-engine
python3 -m venv .venv
source .venv/bin/activate      # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
```

The Python engine is invoked as a subprocess by Next.js — it does not run as a persistent server.

### 4. Mock Mode

Set `ALLOW_MOCK_EXECUTION=1` in `.env.local` to bypass real Near AI Cloud API calls. The mock client returns fixed strings, which is useful for testing the full pipeline without spending API credits.

---

## Security Design

| Concern | Mechanism |
|---------|-----------|
| Fake scores | `submit_score` requires a registered TEE agent — only the Shade Agent running in the attested TEE can call it |
| Score tampering | Best-score-only policy; once committed, scores cannot be lowered |
| Output integrity | SHA-256 of serialized output is locked on-chain at submission time |
| Internal secret | `x-internal-secret` header prevents external callers from hitting the Shade Agent directly |
| Sandbox isolation | RestrictedPython blocks file I/O, os module, subprocess, and other dangerous builtins |
| Credential separation | `SUPABASE_SERVICE_ROLE_KEY` and `INTERNAL_SECRET` are server-side only, never exposed to the browser |

---

## Deployed Contract

- **Network:** NEAR Testnet
- **Contract ID:** `contract.sehun.testnet`
- **Deployer:** `sehun.testnet`

To create a new challenge on testnet:

```bash
near call contract.sehun.testnet create_challenge \
  '{"challenge_id":"your-challenge-id","deadline_ms":9999999999000}' \
  --accountId sehun.testnet --deposit 0.1
```

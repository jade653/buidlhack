import { NextResponse } from "next/server";
import {
  mkdtemp,
  cp,
  readFile,
  rm,
  writeFile,
  mkdir,
  readdir,
} from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { spawn } from "node:child_process";

export const runtime = "nodejs";

type TeeRunRequest = {
  baseGuide?: string;
  challengeId?: string;
  submitterId?: string;
  principalType?: "human" | "agent";
  source?: "inline" | "github";
  github?: {
    repo?: string;
    ref?: string;
    packagePath?: string;
  };
};

type TeeRunResponse = {
  status: "success" | "error" | "timeout";
  output: unknown;
  score: number | null;
  wall_time_sec: number;
  token_usage: Record<string, unknown>;
  error: string | null;
  metadata: Record<string, unknown>;
};

type PersistedSubmissionInfo = {
  submissionId: string;
  rank: number | null;
};

const ALLOWED_EXTENSIONS = new Set([".py", ".md", ".json", ".txt"]);

function normalizeRepo(input: string): string {
  const trimmed = input.trim().replace(/^https?:\/\/github\.com\//, "");
  return trimmed.replace(/\/+$/, "");
}

function normalizePackagePath(input: string): string {
  return input
    .trim()
    .replace(/^\/+/, "")
    .replace(/\/+$/, "");
}

function assertSafePath(targetPath: string): void {
  const normalized = path.posix.normalize(targetPath);
  if (normalized.startsWith("../") || normalized === "..") {
    throw new Error(`Unsafe package path: ${targetPath}`);
  }
}

async function fetchGitHubContents(
  repo: string,
  ref: string,
  packagePath: string,
  outDir: string,
  rootPackagePath: string = packagePath,
): Promise<void> {
  const apiUrl = `https://api.github.com/repos/${repo}/contents/${packagePath}?ref=${encodeURIComponent(ref)}`;
  const response = await fetch(apiUrl, {
    headers: {
      "User-Agent": "challengent-tee-runner",
      Accept: "application/vnd.github+json",
    },
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(
      `Failed to read GitHub path (${response.status}): ${repo}/${packagePath}@${ref}`,
    );
  }

  const entries = (await response.json()) as Array<{
    type: "file" | "dir";
    name: string;
    path: string;
    download_url: string | null;
  }>;

  if (!Array.isArray(entries)) {
    throw new Error("GitHub package path must be a directory.");
  }

  for (const entry of entries) {
    assertSafePath(entry.path);
    const relative = entry.path
      .slice(rootPackagePath.length)
      .replace(/^\/+/, "");
    const localPath = path.join(outDir, relative);

    if (entry.type === "dir") {
      await mkdir(localPath, { recursive: true });
      await fetchGitHubContents(repo, ref, entry.path, outDir, rootPackagePath);
      continue;
    }

    const ext = path.extname(entry.name).toLowerCase();
    if (!ALLOWED_EXTENSIONS.has(ext)) {
      continue;
    }
    if (!entry.download_url) continue;

    const fileResponse = await fetch(entry.download_url, {
      headers: { "User-Agent": "challengent-tee-runner" },
      cache: "no-store",
    });
    if (!fileResponse.ok) {
      throw new Error(`Failed to download file: ${entry.path}`);
    }
    const content = await fileResponse.text();
    await mkdir(path.dirname(localPath), { recursive: true });
    await writeFile(localPath, content, "utf-8");
  }
}

async function validateSubmissionDir(submissionDir: string): Promise<void> {
  const requiredFiles = ["harness.py", "agent.md", "config.json"];
  const existing = new Set(await readdir(submissionDir));
  for (const file of requiredFiles) {
    if (!existing.has(file)) {
      throw new Error(
        `Missing required file "${file}" in submission package root.`,
      );
    }
  }
}

function runPythonSubmission(args: {
  teeEngineDir: string;
  submissionDir: string;
  challengePath: string;
  useMockClient: boolean;
}): Promise<TeeRunResponse> {
  const script = `
import json
import sys
from pathlib import Path

tee_engine_dir = Path(sys.argv[1])
submission_dir = Path(sys.argv[2])
challenge_path = Path(sys.argv[3])
use_mock = sys.argv[4] == "1"

sys.path.insert(0, str(tee_engine_dir))

from engine import run_submission

challenge_input = json.loads(challenge_path.read_text(encoding="utf-8"))

mock_answers = [
    "badge: Soft ritual edit\\ntitle: Clinical glow, softened into a beautiful daily ritual.\\nbody: Three tactile essentials for cleansing, brightening, and sealing in comfort with a polished shelf presence.\\ncta: Shop Luma Dew\\nbenefit_title: Built for skin that wants radiance without overload.\\nbenefit_body: A concise lineup of cruelty-free formulas designed to feel elegant from sink to vanity.",
    "badge: Soft ritual edit\\ntitle: Clinical glow, softened into a beautiful daily ritual.\\nbody: Three tactile essentials for cleansing, brightening, and sealing in comfort with a polished shelf presence.\\ncta: Shop Luma Dew\\nbenefit_title: Built for skin that wants radiance without overload.\\nbenefit_body: A concise lineup of cruelty-free formulas designed to feel elegant from sink to vanity.",
]

result = run_submission(
    submission_dir=submission_dir,
    challenge_input=challenge_input,
    use_mock_client=use_mock,
    mock_responses=mock_answers if use_mock else None,
)

print(json.dumps({
    "status": result.status,
    "output": result.output,
    "score": result.score,
    "wall_time_sec": result.wall_time_sec,
    "token_usage": result.token_usage,
    "error": result.error,
    "metadata": result.metadata,
}, ensure_ascii=False))
`;

  return new Promise((resolve, reject) => {
    const python = spawn(
      "python3",
      [
        "-c",
        script,
        args.teeEngineDir,
        args.submissionDir,
        args.challengePath,
        args.useMockClient ? "1" : "0",
      ],
      {
        stdio: ["ignore", "pipe", "pipe"],
      },
    );

    let stdout = "";
    let stderr = "";

    python.stdout.on("data", (chunk) => {
      stdout += chunk.toString();
    });
    python.stderr.on("data", (chunk) => {
      stderr += chunk.toString();
    });

    python.on("error", (err) => {
      reject(err);
    });

    python.on("close", (code) => {
      if (code !== 0) {
        reject(
          new Error(
            `Python process failed with code ${code}. ${stderr || stdout}`,
          ),
        );
        return;
      }

      const trimmed = stdout.trim();
      if (!trimmed) {
        reject(new Error("Empty response from Python runner."));
        return;
      }

      try {
        resolve(JSON.parse(trimmed) as TeeRunResponse);
      } catch {
        reject(new Error(`Invalid JSON from Python runner: ${trimmed}`));
      }
    });
  });
}

async function persistToSupabase(args: {
  challengeId: string;
  submitterId: string;
  principalType: "human" | "agent";
  source: "inline" | "github";
  executionMode: "near-ai-cloud" | "mock";
  result: TeeRunResponse;
}): Promise<PersistedSubmissionInfo | null> {
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const serviceRoleKey = process.env.SUPABASE_SERVICE_ROLE_KEY;
  if (!supabaseUrl || !serviceRoleKey) return null;

  const headers = {
    apikey: serviceRoleKey,
    Authorization: `Bearer ${serviceRoleKey}`,
    "Content-Type": "application/json",
  };

  const totalTokens = Number(args.result.token_usage?.total_tokens ?? 0);
  const outputText =
    typeof args.result.output === "string" ? args.result.output : null;

  const insertResponse = await fetch(`${supabaseUrl}/rest/v1/submissions`, {
    method: "POST",
    headers: {
      ...headers,
      Prefer: "return=representation",
    },
    body: JSON.stringify({
      challenge_id: args.challengeId,
      submitter_id: args.submitterId,
      principal_type: args.principalType,
      source: args.source,
      execution_mode: args.executionMode,
      status: args.result.status,
      score: args.result.score,
      wall_time_sec: args.result.wall_time_sec,
      total_tokens: totalTokens,
      token_usage: args.result.token_usage,
      output_text: outputText,
      output_json: args.result.output,
    }),
  });
  if (!insertResponse.ok) {
    const message = await insertResponse.text();
    throw new Error(`Supabase insert failed: ${message}`);
  }

  const inserted = (await insertResponse.json()) as Array<{ id: string }>;
  const submissionId = inserted[0]?.id;
  if (!submissionId) {
    throw new Error("Supabase insert succeeded but submission id missing.");
  }

  const rpcResponse = await fetch(
    `${supabaseUrl}/rest/v1/rpc/recompute_leaderboard`,
    {
      method: "POST",
      headers,
      body: JSON.stringify({ target_challenge_id: args.challengeId }),
    },
  );
  if (!rpcResponse.ok) {
    const message = await rpcResponse.text();
    throw new Error(`Supabase leaderboard recompute failed: ${message}`);
  }

  const rankResponse = await fetch(
    `${supabaseUrl}/rest/v1/leaderboard_entries?submission_id=eq.${submissionId}&select=rank`,
    {
      method: "GET",
      headers,
    },
  );
  if (!rankResponse.ok) {
    const message = await rankResponse.text();
    throw new Error(`Supabase rank query failed: ${message}`);
  }
  const rankRows = (await rankResponse.json()) as Array<{ rank: number | null }>;
  const rank = rankRows[0]?.rank ?? null;

  return { submissionId, rank };
}

export async function POST(request: Request) {
  const body = (await request.json()) as TeeRunRequest;
  const baseGuide = body.baseGuide?.trim();
  const source = body.source ?? "inline";
  const challengeId = body.challengeId?.trim() || "unknown-challenge";
  const submitterId = body.submitterId?.trim() || "anonymous";
  const requestedPrincipal = body.principalType;
  const principalType: "human" | "agent" =
    requestedPrincipal === "human" || requestedPrincipal === "agent"
      ? requestedPrincipal
      : source === "github"
        ? "agent"
        : "human";

  if (!baseGuide) {
    return NextResponse.json(
      { ok: false, error: "baseGuide is required." },
      { status: 400 },
    );
  }

  const appRoot = process.cwd();
  const teeEngineDir = path.resolve(appRoot, "../tee-engine");
  const sampleDir = path.join(teeEngineDir, "samples", "cosmetic1");
  const challengePath = path.join(
    teeEngineDir,
    "samples",
    "cosmetics_challenge_input.json",
  );
  const hasNearApiKey = Boolean(process.env.NEAR_AI_API_KEY);
  const allowMockExecution = process.env.ALLOW_MOCK_EXECUTION === "1";
  const useMockClient = !hasNearApiKey && allowMockExecution;
  const executionMode = useMockClient ? "mock" : "near-ai-cloud";

  let tempRoot = "";

  try {
    if (!hasNearApiKey && !allowMockExecution) {
      return NextResponse.json(
        {
          ok: false,
          error:
            "NEAR_AI_API_KEY is not configured. Set it to run with real Near AI Cloud. (Use ALLOW_MOCK_EXECUTION=1 only for local mock testing.)",
        },
        { status: 503 },
      );
    }

    tempRoot = await mkdtemp(path.join(tmpdir(), "challengent-submission-"));
    const submissionDir = path.join(tempRoot, "submission");

    if (source === "github") {
      const repoRaw = body.github?.repo?.trim();
      const ref = body.github?.ref?.trim() || "main";
      const packagePathRaw = body.github?.packagePath?.trim() || "";

      if (!repoRaw || !packagePathRaw) {
        return NextResponse.json(
          { ok: false, error: "github.repo and github.packagePath are required." },
          { status: 400 },
        );
      }

      const repo = normalizeRepo(repoRaw);
      const packagePath = normalizePackagePath(packagePathRaw);
      assertSafePath(packagePath);
      await mkdir(submissionDir, { recursive: true });
      await fetchGitHubContents(repo, ref, packagePath, submissionDir);
      await validateSubmissionDir(submissionDir);
    } else {
      await cp(sampleDir, submissionDir, { recursive: true });
    }

    const harnessSource = await readFile(
      path.join(submissionDir, "harness.py"),
      "utf-8",
    );
    await writeFile(path.join(submissionDir, "agent.md"), `${baseGuide}\n`, "utf-8");

    const result = await runPythonSubmission({
      teeEngineDir,
      submissionDir,
      challengePath,
      useMockClient,
    });
    const persisted = await persistToSupabase({
      challengeId,
      submitterId,
      principalType,
      source,
      executionMode,
      result,
    });

    return NextResponse.json({
      ok: true,
      challengeId,
      harnessSource,
      result,
      mockMode: useMockClient,
      executionMode,
      source,
      submissionId: persisted?.submissionId ?? null,
      rank: persisted?.rank ?? null,
    });
  } catch (error) {
    const message =
      error instanceof Error ? error.message : "Unknown submission error";
    return NextResponse.json(
      { ok: false, error: message },
      { status: 500 },
    );
  } finally {
    if (tempRoot) {
      await rm(tempRoot, { recursive: true, force: true });
    }
  }
}

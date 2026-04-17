"use client";

import { useState, useEffect, useRef } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { mockChallenges } from "@/lib/mock-data";
import { ArenaButton } from "@/components/ui/ArenaButton";
import { ArenaBadge } from "@/components/ui/ArenaBadge";
import { StatBar } from "@/components/ui/StatBar";
import { OnChainBadge } from "@/components/ui/OnChainBadge";
import { Challenge } from "@/lib/types";

type Phase = "submit" | "running" | "result";

type ControlSignal = "stop" | "summarize" | "resume";

type TeeRunResult = {
  status: "success" | "error" | "timeout";
  output: unknown;
  score: number | null;
  wall_time_sec: number;
  token_usage: {
    total_prompt_tokens?: number;
    total_completion_tokens?: number;
    total_tokens?: number;
    per_model?: Record<string, unknown>;
    call_count?: number;
  };
  error: string | null;
  metadata: Record<string, unknown>;
};

type SubmissionSource = "inline" | "github";
type OutputViewMode = "text" | "rendered";

const estimateTokensFromText = (text: string): number =>
  Math.max(1, Math.ceil(text.length / 4));

const buildDefaultBaseGuide = (challenge: Challenge) => `## Challenge Goal
- ${challenge.description}

## Context
- Challenge: ${challenge.title}
- Host: ${challenge.company}

## Constraints (TEE / RBAC)
- The trainer can define intent only through this Base Guide in markdown.
- Generated code is monitored in read-only mode within TEE.
- Free-form vibe coding is disabled; only control signals are allowed.

## Evaluation Criteria
${challenge.evaluationCriteria
  .map(
    (item) =>
      `- ${item.label}: ${typeof item.weight === "number" ? `${item.weight}%` : item.weight}`,
  )
  .join("\n")}

## Input / Output Spec
\`\`\`
${challenge.inputOutputSpec}
\`\`\`

## Hard Constraints
- Max execution time: 120 seconds
- Token budget target: <= 12,000 total tokens
- Prefer deterministic and schema-compliant output
- Do not include unsupported claims or fabricated facts

## Starter Strategy (Runnable Baseline)
- Parse the input payload first and validate required fields.
- Produce output that strictly follows the declared output schema.
- Keep the response concise, structured, and production-safe.
- If any field is missing or ambiguous, degrade gracefully instead of failing hard.

## Completion Conditions
- The result must comply with the platform output spec.
- The final score must be returned in the range 0.0 to 1.0.
`;

export default function SubmitPage() {
  const params = useParams();
  const id = params.id as string;
  const challenge =
    mockChallenges.find((c) => c.id === id) || mockChallenges[0];
  const challengeGuide = buildDefaultBaseGuide(challenge);

  const [phase, setPhase] = useState<Phase>("submit");
  const [baseGuide, setBaseGuide] = useState(challengeGuide);
  const [submissionSource, setSubmissionSource] =
    useState<SubmissionSource>("inline");
  const [githubRepo, setGithubRepo] = useState("9oodam/agent-set-1");
  const [githubRef, setGithubRef] = useState("main");
  const [githubPackagePath, setGithubPackagePath] = useState(".");
  const [monitorSummary, setMonitorSummary] = useState<string | null>(null);
  const [lastControlSignal, setLastControlSignal] =
    useState<ControlSignal | null>(null);
  const [runtimeEvents, setRuntimeEvents] = useState<string[]>([]);
  const [runResult, setRunResult] = useState<TeeRunResult | null>(null);
  const [executionMode, setExecutionMode] = useState<
    "near-ai-cloud" | "mock" | null
  >(null);
  const [outputViewMode, setOutputViewMode] = useState<OutputViewMode>("text");
  const [runError, setRunError] = useState<string | null>(null);
  const [startedAt, setStartedAt] = useState<number | null>(null);
  const [elapsedSec, setElapsedSec] = useState(0);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    setBaseGuide(challengeGuide);
    setRunError(null);
  }, [challengeGuide]);

  useEffect(() => {
    if (phase !== "running" || startedAt === null) return;
    const timer = setInterval(() => {
      setElapsedSec(Math.floor((Date.now() - startedAt) / 1400));
    }, 1000);
    return () => clearInterval(timer);
  }, [phase, startedAt]);

  const addRuntimeEvent = (message: string) => {
    setRuntimeEvents((prev) => [
      ...prev,
      `${new Date().toLocaleTimeString()}  ${message}`,
    ]);
  };

  const handleStart = async () => {
    const controller = new AbortController();
    abortRef.current = controller;
    setMonitorSummary(null);
    setRunError(null);
    setRunResult(null);
    setExecutionMode(null);
    setOutputViewMode("text");
    setRuntimeEvents([]);
    setLastControlSignal(null);
    setStartedAt(Date.now());
    setElapsedSec(0);
    setPhase("running");
    addRuntimeEvent("Building submission package (applying base-guide.md)");
    addRuntimeEvent("Sending execution request to backend / TEE");

    try {
      const response = await fetch("/api/tee/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          challengeId: id,
          baseGuide,
          source: submissionSource,
          github:
            submissionSource === "github"
              ? {
                  repo: githubRepo,
                  ref: githubRef,
                  packagePath: githubPackagePath,
                }
              : undefined,
        }),
        signal: controller.signal,
      });

      const data = await response.json();
      if (!response.ok || !data.ok) {
        throw new Error(data.error || "Failed to execute request in TEE.");
      }

      const result = data.result as TeeRunResult;
      setRunResult(result);
      setExecutionMode(
        (data.executionMode as "near-ai-cloud" | "mock" | undefined) ?? null,
      );
      setOutputViewMode("text");
      addRuntimeEvent(
        `Execution finished · status=${result.status} · wall=${result.wall_time_sec.toFixed(2)}s`,
      );
      if (data.executionMode) {
        addRuntimeEvent(`Execution mode: ${data.executionMode}`);
      }
      if (result.error) {
        addRuntimeEvent(`Error: ${result.error}`);
      }
      setPhase("result");
    } catch (error) {
      if (controller.signal.aborted) {
        addRuntimeEvent("Execution stopped by user control signal.");
        setRunError("Execution has been stopped.");
      } else {
        const message =
          error instanceof Error ? error.message : "An unknown error occurred.";
        setRunError(message);
        addRuntimeEvent(`Failed: ${message}`);
      }
      setPhase("submit");
    } finally {
      abortRef.current = null;
    }
  };

  const sendControlSignal = (signal: ControlSignal) => {
    setLastControlSignal(signal);
    if (signal === "stop") {
      abortRef.current?.abort();
      setPhase("submit");
      return;
    }
    if (signal === "summarize") {
      setMonitorSummary(
        `[Summary] elapsed ${elapsedSec}s · events ${runtimeEvents.length}. The agent runs from a Base Guide package, and control signals are only used for monitoring/interruption.`,
      );
      return;
    }
    addRuntimeEvent(
      "Resume signal received (current version runs as a single request, so this is informational).",
    );
  };

  const totalTokens = runResult?.token_usage?.total_tokens ?? 0;
  const finalScore = runResult?.score
    ? Math.round(runResult.score * 1000) / 10
    : 0;
  const criterionScores = challenge.evaluationCriteria.map((item, index) => {
    const base = finalScore;
    const weightBoost = typeof item.weight === "number" ? item.weight / 15 : 3;
    const variance = ((index % 4) - 1.5) * 2.2;
    const value = Math.max(
      35,
      Math.min(99, base * 0.8 + weightBoost + variance),
    );
    return { ...item, value };
  });
  const outputPreview =
    typeof runResult?.output === "string"
      ? runResult.output.slice(0, 800)
      : JSON.stringify(runResult?.output ?? {}, null, 2);
  const htmlOutput =
    typeof runResult?.output === "string" ? runResult.output : null;
  const isHtmlOutput = Boolean(
    htmlOutput &&
    /<html[\s>]|<!doctype html|<body[\s>]/i.test(htmlOutput.slice(0, 500)),
  );
  const basePromptTokens = estimateTokensFromText(
    `${baseGuide}\n${challenge.inputOutputSpec}`,
  );
  const estimatedCallCount = submissionSource === "github" ? 3 : 2;
  const estimatedTotalTokens = Math.round(
    basePromptTokens * estimatedCallCount + 900,
  );
  const estimatedCredits = Math.max(1, Math.round(estimatedTotalTokens / 1000));

  return (
    <div className="pt-24 max-w-7xl mx-auto px-6 pb-16">
      <div className="mb-8 rounded-lg border border-border bg-surface/80 p-4 text-sm text-ink-2 space-y-2">
        <div className="font-label uppercase tracking-wider text-xs text-ink-3">
          RBAC / TEE
        </div>
        <p>
          Trainers cannot write code directly inside TEE. System intent is
          authored only through{" "}
          <strong className="text-ink">Base Guide (MD)</strong>, and
          AI-generated code is monitored in{" "}
          <strong className="text-ink">read-only</strong> mode.
        </p>
        <p>
          Vibe coding chat is restricted to{" "}
          <strong className="text-ink">control signals</strong> (stop,
          summarize, resume) to avoid single-session bottlenecks and maximize
          autonomous execution.
        </p>
      </div>

      {/* Step 1: Submit */}
      {phase === "submit" && (
        <div className="space-y-8">
          <div className="flex items-center gap-3">
            <div className="w-8 h-[2px] bg-red" />
            <span className="font-label uppercase tracking-[0.2em] text-xs text-ink-2">
              {"// submit agent"} — {challenge.title}
            </span>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Write: Base Guide only */}
            <div className="space-y-2 min-h-0">
              <div className="flex flex-wrap items-center gap-2">
                <ArenaBadge color="bg-red/10 text-red">Write</ArenaBadge>
                <ArenaBadge color="bg-ink/5 text-ink-2">
                  base-guide.md
                </ArenaBadge>
              </div>
              <p className="text-sm text-ink-3">
                Write your objectives, constraints, and agent instructions in
                Markdown.
              </p>
              <textarea
                value={baseGuide}
                onChange={(e) => setBaseGuide(e.target.value)}
                className="w-full min-h-[20rem] bg-surface text-ink font-mono text-sm p-4 rounded-lg border border-border focus:outline-none focus:border-red resize-y"
                spellCheck={false}
                aria-label="Base Guide markdown"
              />

              <div className="rounded-lg border border-border bg-surface p-3 space-y-3">
                <div className="font-label uppercase tracking-wider text-xs text-ink-2">
                  Submission Source
                </div>
                <div className="flex gap-2 flex-wrap">
                  <ArenaButton
                    variant={submissionSource === "inline" ? "red" : "ghost"}
                    size="sm"
                    onClick={() => setSubmissionSource("inline")}
                  >
                    Platform Template
                  </ArenaButton>
                  <ArenaButton
                    variant={submissionSource === "github" ? "red" : "ghost"}
                    size="sm"
                    onClick={() => setSubmissionSource("github")}
                  >
                    GitHub Agent Set
                  </ArenaButton>
                </div>
                {submissionSource === "github" && (
                  <div className="space-y-2">
                    <input
                      value={githubRepo}
                      onChange={(e) => setGithubRepo(e.target.value)}
                      placeholder="owner/repo (public)"
                      className="w-full border border-border rounded-[4px] px-3 py-2 text-sm bg-surface focus:outline-none focus:border-red"
                    />
                    <div className="grid grid-cols-2 gap-2">
                      <input
                        value={githubRef}
                        onChange={(e) => setGithubRef(e.target.value)}
                        placeholder="branch/tag/sha"
                        className="w-full border border-border rounded-[4px] px-3 py-2 text-sm bg-surface focus:outline-none focus:border-red"
                      />
                      <input
                        value={githubPackagePath}
                        onChange={(e) => setGithubPackagePath(e.target.value)}
                        placeholder="path/to/package/root"
                        className="w-full border border-border rounded-[4px] px-3 py-2 text-sm bg-surface focus:outline-none focus:border-red"
                      />
                    </div>
                    <p className="text-sm text-red">
                      * Required at package root: harness.py, agent.md,
                      config.json
                    </p>
                  </div>
                )}
              </div>
            </div>

            {/* Confidential metadata */}
            <div className="space-y-2 min-h-0 flex flex-col">
              <div className="flex flex-wrap items-center gap-2">
                <ArenaBadge color="bg-blue/10 text-blue">
                  Confidential
                </ArenaBadge>
                <ArenaBadge color="bg-ink/5 text-ink-2">
                  source hidden
                </ArenaBadge>
              </div>
              <p className="text-sm text-ink-3">
                Your source code is encrypted end-to-end and executed only
                within a trusted runtime boundary.
              </p>
              <div className="flex-1 min-h-[20rem] w-full overflow-auto bg-[#1e1e1e] text-gray-300 font-mono text-sm p-4 rounded-lg border border-border space-y-2">
                <div className="text-green-400">confidentiality_policy</div>
                <div>- only runtime metrics and final output are exposed</div>
                <div>- attestation metadata is shown after execution</div>
                <div className="text-green-400 pt-2">
                  submission_fingerprint
                </div>
                <div>{`${challenge.id}-${submissionSource}-${baseGuide.length}`}</div>
              </div>
            </div>
          </div>

          {/* <div className="rounded-lg border border-border bg-surface p-4 space-y-3">
            <div className="font-label uppercase tracking-wider text-xs text-ink-2">
              Input / Output Spec
            </div>
            <pre className="bg-ink/[0.03] rounded-lg p-4 text-xs overflow-x-auto whitespace-pre-wrap">
              {challenge.inputOutputSpec}
            </pre>
          </div>

          <div className="rounded-lg border border-border bg-surface p-4 space-y-3">
            <div className="font-label uppercase tracking-wider text-xs text-ink-2">
              Challenge Evaluation Criteria
            </div>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
              {challenge.evaluationCriteria.map((item) => (
                <div
                  key={item.key}
                  className="rounded-lg border border-border p-3 text-center"
                >
                  <div className="font-title text-2xl text-red">
                    {typeof item.weight === "number"
                      ? `${item.weight}%`
                      : item.weight}
                  </div>
                  <div className="text-xs text-ink-2 mt-1">{item.label}</div>
                </div>
              ))}
            </div>
          </div> */}

          <div className="bg-surface border border-border rounded-lg p-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
            <div className="text-sm text-ink-2">
              Estimated tokens: ~{estimatedTotalTokens.toLocaleString()} ·
              Estimated cost: {estimatedCredits} credits · Guide{" "}
              {baseGuide.trim().length > 0 ? "ready" : "empty"}
            </div>
            <ArenaBadge color="bg-green/10 text-green">
              Balance: 150 credits ✓
            </ArenaBadge>
          </div>

          <ArenaButton
            variant="red"
            size="lg"
            className="w-full"
            onClick={handleStart}
            disabled={
              !baseGuide.trim() ||
              (submissionSource === "github" &&
                (!githubRepo.trim() || !githubPackagePath.trim()))
            }
          >
            Enter Arena 🥊
          </ArenaButton>
          {runError && (
            <div className="rounded-lg border border-red/30 bg-red/5 p-4 text-sm text-red">
              {runError}
            </div>
          )}
        </div>
      )}

      {/* Step 2: Running */}
      {phase === "running" && (
        <div className="space-y-6">
          <div className="bg-surface border border-border rounded-lg p-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex flex-wrap items-center gap-4">
              <span className="text-lg">🥊</span>
              <span className="font-label uppercase tracking-wider text-sm font-semibold">
                Running (TEE connected)
              </span>
              <span className="font-mono text-sm text-ink-2">
                Elapsed: {elapsedSec}s
              </span>
            </div>
          </div>

          <div className="flex flex-col gap-6">
            <div className="flex flex-col lg:flex-row gap-6">
              <div className="flex-1 bg-[#1e1e1e] rounded-lg p-4 h-72 lg:h-96 overflow-y-auto font-mono text-sm">
                {runtimeEvents.map((event, i) => (
                  <div key={`${event}-${i}`} className="mb-2 text-gray-300">
                    {event}
                  </div>
                ))}
                {runtimeEvents.length === 0 && (
                  <div className="text-gray-500">Waiting to start...</div>
                )}
              </div>

              <div className="lg:w-64 space-y-4 shrink-0">
                <div className="bg-surface border border-border rounded-lg p-4 space-y-4">
                  <div className="font-label uppercase tracking-wider text-xs text-ink-2">
                    Runtime Status
                  </div>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span>backend</span>
                      <span>✅ request sent</span>
                    </div>
                    <div className="flex justify-between">
                      <span>tee-engine</span>
                      <span>🔄 running</span>
                    </div>
                    <div className="flex justify-between">
                      <span>result</span>
                      <span>⏳ pending</span>
                    </div>
                  </div>
                  <div className="border-t border-border pt-3 space-y-1 text-xs text-ink-2">
                    <div>Events: {runtimeEvents.length}</div>
                    <div>Elapsed: {elapsedSec}s</div>
                    <div>Mode: API integration</div>
                  </div>
                </div>
              </div>
            </div>

            {/* Confidential execution metadata */}
            <div className="space-y-2">
              <div className="flex flex-wrap items-center gap-2">
                <ArenaBadge color="bg-blue/10 text-blue">
                  Confidential
                </ArenaBadge>
                <ArenaBadge color="bg-ink/5 text-ink-2">
                  source hidden
                </ArenaBadge>
              </div>
              <div className="w-full max-h-64 overflow-auto bg-[#1e1e1e] text-green-400 font-mono text-sm p-4 rounded-lg border border-border space-y-2">
                <div>source_visibility: hidden</div>
                <div>
                  execution_mode: {executionMode ? executionMode : "pending"}
                </div>
                <div>runtime_boundary: tee-only</div>
              </div>
              <p className="text-xs text-ink-3">
                Code plaintext is not exposed. Evaluate runs via attestation,
                runtime metrics, and output quality.
              </p>
            </div>

            {/* Control signals only — no free-form chat */}
            <div className="rounded-lg border border-border bg-surface p-4 space-y-3">
              <div className="font-label uppercase tracking-wider text-ink-2">
                Control Signals (Monitoring / Interrupt)
              </div>
              <p className="text-sm text-ink-3">
                Free-form vibe coding input is disabled. Only the buttons below
                are allowed.
              </p>
              <div className="flex flex-wrap gap-2">
                <ArenaButton
                  variant="ghost"
                  size="sm"
                  onClick={() => sendControlSignal("stop")}
                >
                  Stop
                </ArenaButton>
                <ArenaButton
                  variant="ghost"
                  size="sm"
                  onClick={() => sendControlSignal("summarize")}
                >
                  Summarize
                </ArenaButton>
                <ArenaButton
                  variant="red"
                  size="sm"
                  onClick={() => sendControlSignal("resume")}
                >
                  Resume
                </ArenaButton>
              </div>
              {lastControlSignal && (
                <p className="text-xs text-ink-3 font-mono">
                  Last signal: {lastControlSignal}
                </p>
              )}
            </div>

            {monitorSummary && (
              <div className="rounded-lg border border-blue/20 bg-blue/5 p-4 text-sm text-ink-2 whitespace-pre-wrap">
                {monitorSummary}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Step 3: Result */}
      {phase === "result" && (
        <div className="max-w-7xl mx-auto space-y-8">
          <div className="text-center space-y-2">
            <span className="text-4xl">🥊</span>
            <h2 className="font-title text-4xl">Execution Complete</h2>
          </div>

          <div className="grid grid-cols-2 gap-16">
            <div className="space-y-8">
              <div className="space-y-4">
                {criterionScores.map((criterion, index) => (
                  <StatBar
                    key={criterion.key}
                    label={criterion.label}
                    value={criterion.value}
                    color={index % 2 === 0 ? "red" : "blue"}
                  />
                ))}
                <div className="border-t border-border pt-4">
                  <StatBar label="Final" value={finalScore} color="red" />
                </div>
              </div>
              <div className="bg-surface border border-border rounded-lg p-4 text-center space-y-4">
                <div className="font-label uppercase tracking-wider text-ink-2">
                  Run Metrics
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="flex items-center gap-2 justify-center text-ink-2 p-4 border border-ink3 rounded-lg">
                    Tokens{" "}
                    <span className="text-red font-bold text-lg">
                      {totalTokens.toLocaleString()}
                    </span>
                  </div>
                  <div className="flex items-center gap-2 justify-center text-ink-2 p-4 border border-ink3 rounded-lg">
                    Wall
                    <span className="text-blue font-bold text-lg">
                      {(runResult?.wall_time_sec ?? 0).toFixed(2)}s
                    </span>
                  </div>
                </div>
              </div>
              <div className="bg-surface border border-border rounded-lg p-5 space-y-3 text-center">
                <div className="font-label uppercase tracking-wider text-ink-2">
                  Current Rank
                </div>
                <div className="font-title text-5xl text-red">🥈 #2</div>
                <div className="text-sm text-ink-2">
                  / {challenge.participants}
                </div>
                <OnChainBadge className="justify-center" />
              </div>
            </div>

            <div className="space-y-4 h-full flex flex-col">
              <div className="flex items-center justify-between shrink-0">
                <div className="font-title text-xl text-ink-2">
                  Result Preview
                </div>
                <div className="flex gap-2">
                  <ArenaButton
                    variant={outputViewMode === "text" ? "red" : "ghost"}
                    size="sm"
                    onClick={() => setOutputViewMode("text")}
                  >
                    Text / JSON
                  </ArenaButton>
                  <ArenaButton
                    variant={outputViewMode === "rendered" ? "red" : "ghost"}
                    size="sm"
                    onClick={() => setOutputViewMode("rendered")}
                    disabled={!isHtmlOutput}
                  >
                    Rendered
                  </ArenaButton>
                </div>
              </div>
              {/* {executionMode && (
                <div className="text-xs text-ink-3 text-center">
                  Runtime backend:{" "}
                  <span className="font-mono">
                    {executionMode === "near-ai-cloud"
                      ? "Near AI Cloud"
                      : "Mock"}
                  </span>
                </div>
              )} */}
              {outputViewMode === "rendered" && isHtmlOutput && htmlOutput ? (
                <iframe
                  title="Rendered HTML output"
                  srcDoc={htmlOutput}
                  sandbox=""
                  className="flex-1 min-h-80 rounded-lg border border-border bg-white"
                />
              ) : (
                <div className="flex-1 min-h-80 bg-[#1e1e1e] text-gray-300 rounded-lg border border-border p-4 font-mono text-xs whitespace-pre-wrap overflow-auto">
                  {outputPreview}
                </div>
              )}
              {!isHtmlOutput && (
                <p className="text-xs text-ink-3">
                  Rendered HTML view is available only when output contains an
                  HTML document.
                </p>
              )}
            </div>
          </div>

          <div className="space-y-4">
            <div className="flex gap-4 justify-center">
              <ArenaButton
                variant="red"
                onClick={() => {
                  setPhase("submit");
                  setRunResult(null);
                }}
              >
                Retry
              </ArenaButton>
              <Link href={`/challenges/${id}`}>
                <ArenaButton variant="ghost">View Ranking</ArenaButton>
              </Link>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { mockChallenges } from "@/lib/mock-data";
import { ArenaButton } from "@/components/ui/ArenaButton";
import { ArenaBadge } from "@/components/ui/ArenaBadge";
import { StatBar } from "@/components/ui/StatBar";
import { OnChainBadge } from "@/components/ui/OnChainBadge";
import { useExecutionStream } from "@/hooks/useExecutionStream";
import { getAgentColor, cn } from "@/lib/utils";

type Phase = "submit" | "running" | "result";

type ControlSignal = "stop" | "summarize" | "resume";

const DEFAULT_BASE_GUIDE = `## 목표
- 삼성전자 실적과 공급망 리스크를 요약한다.

## 제약 (TEE / RBAC)
- 트레이너는 이 Base Guide **마크다운으로만** 시스템 의도를 기술한다.
- 생성 코드는 TEE에서 **읽기 전용**으로만 모니터링한다.

## 에이전트 지시
- orchestrator → worker 분배 → reviewer 순으로 자율 실행.
- 인간 개입은 **컨트롤 신호**(중단·요약·재개)로만 허용한다.

## 완료 조건
- 최종 보고서 dict를 반환한다.
`;

/** 데모용: 실행 시작 후 읽기 전용으로 보여 줄 에이전트 생성 harness */
const MOCK_GENERATED_HARNESS = `import asyncio
from agents import orchestrator, worker_a, worker_b, reviewer

async def run(input_data: dict) -> dict:
    plan = await orchestrator.analyze(input_data)
    results = await asyncio.gather(
        worker_a.execute(plan["task_a"]),
        worker_b.execute(plan["task_b"]),
    )
    feedback = interrupt("confirm", "하이닉스도 분석 범위에 포함할까요?")
    if feedback:
        extra = await worker_a.execute({"target": "SK하이닉스"})
        results.append(extra)
    style = interrupt("text_input", "보고서 스타일을 선택해주세요")
    return await reviewer.compile(results, style=style)
`;

const READONLY_PLACEHOLDER = `# harness.py
# 에이전트가 생성한 코드는 실행 단계에서만 스트리밍되어 표시됩니다.
# (트레이너 직접 편집 불가 — Read-only)
`;

export default function SubmitPage() {
  const params = useParams();
  const id = params.id as string;
  const challenge =
    mockChallenges.find((c) => c.id === id) || mockChallenges[0];

  const [phase, setPhase] = useState<Phase>("submit");
  const [baseGuide, setBaseGuide] = useState(DEFAULT_BASE_GUIDE);
  const [monitorSummary, setMonitorSummary] = useState<string | null>(null);
  const [lastControlSignal, setLastControlSignal] =
    useState<ControlSignal | null>(null);

  const stream = useExecutionStream();

  useEffect(() => {
    if (stream.status === "completed" && phase === "running") {
      const t = setTimeout(() => setPhase("result"), 500);
      return () => clearTimeout(t);
    }
  }, [stream.status, phase]);

  const handleStart = () => {
    setMonitorSummary(null);
    setLastControlSignal(null);
    setPhase("running");
    stream.start();
  };

  const sendControlSignal = (signal: ControlSignal) => {
    setLastControlSignal(signal);
    if (signal === "stop") {
      stream.stop();
      setPhase("submit");
      return;
    }
    if (signal === "summarize") {
      setMonitorSummary(
        `[요약] 경과 ${stream.elapsed} · 토큰 ${stream.tokenCount.toLocaleString()} · 로그 ${stream.logs.length}건. 에이전트는 Base Guide에 따라 자율 실행 중이며, 자연어 코딩/세션 점유 없이 컨트롤 신호로만 관측됩니다.`,
      );
      return;
    }
    if (signal === "resume") {
      stream.continueExecution();
    }
  };

  return (
    <div className="pt-24 max-w-5xl mx-auto px-6 pb-16">
      <div className="mb-8 rounded-lg border border-border bg-surface/80 p-4 text-sm text-ink-2 space-y-2">
        <div className="font-label uppercase tracking-wider text-xs text-ink-3">
          RBAC / TEE
        </div>
        <p>
          트레이너는 TEE에서 코드를 직접 작성할 수 없습니다. 시스템 설계는{" "}
          <strong className="text-ink">Base Guide (MD)</strong>로만 입력할 수
          있으며, AI가 생성한 코드는{" "}
          <strong className="text-ink">읽기 전용</strong>으로만 모니터링됩니다.
        </p>
        <p>
          바이브 코딩(채팅)은{" "}
          <strong className="text-ink">컨트롤 신호</strong>
          (작업 멈춤·상황 요약·재개)로만 제한되어, 싱글 세션 점유 병목 없이 자동화
          결과를 우선합니다.
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
                <ArenaBadge color="bg-ink/5 text-ink-2">base-guide.md</ArenaBadge>
              </div>
              <p className="text-xs text-ink-3">
                유일한 입력 채널입니다. 마크다운으로 목표·제약·에이전트 지시를
                적습니다.
              </p>
              <textarea
                value={baseGuide}
                onChange={(e) => setBaseGuide(e.target.value)}
                className="w-full min-h-[20rem] bg-surface text-ink font-mono text-sm p-4 rounded-lg border border-border focus:outline-none focus:border-red resize-y"
                spellCheck={false}
                aria-label="Base Guide 마크다운"
              />
            </div>

            {/* Read-only: code preview slot */}
            <div className="space-y-2 min-h-0 flex flex-col">
              <div className="flex flex-wrap items-center gap-2">
                <ArenaBadge color="bg-blue/10 text-blue">Read-only</ArenaBadge>
                <ArenaBadge color="bg-ink/5 text-ink-2">harness.py</ArenaBadge>
              </div>
              <p className="text-xs text-ink-3">
                제출 전에는 플레이스홀더만 표시됩니다. 실행 후 에이전트 산출물이
                여기에 나타납니다.
              </p>
              <pre
                className="flex-1 min-h-[20rem] w-full overflow-auto bg-[#1e1e1e] text-gray-300 font-mono text-sm p-4 rounded-lg border border-border whitespace-pre-wrap"
                aria-readonly="true"
              >
                {READONLY_PLACEHOLDER}
              </pre>
            </div>
          </div>

          <div className="bg-surface border border-border rounded-lg p-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
            <div className="text-sm text-ink-2">
              예상 토큰: ~8,000 · 예상 비용: 8 크레딧 · 가이드{" "}
              {baseGuide.trim().length > 0 ? "작성됨" : "비어 있음"}
            </div>
            <ArenaBadge color="bg-green/10 text-green">
              잔액: 150 크레딧 ✓
            </ArenaBadge>
          </div>

          <ArenaButton
            variant="red"
            size="lg"
            className="w-full"
            onClick={handleStart}
            disabled={!baseGuide.trim()}
          >
            아레나 입장 ⚔️
          </ArenaButton>
        </div>
      )}

      {/* Step 2: Running */}
      {phase === "running" && (
        <div className="space-y-6">
          <div className="bg-surface border border-border rounded-lg p-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex flex-wrap items-center gap-4">
              <span className="text-lg">⚔️</span>
              <span className="font-label uppercase tracking-wider text-xs font-semibold">
                {stream.status === "interrupted"
                  ? "인터럽트 — 컨트롤 신호만 가능"
                  : "실행 중 (모니터링)"}
              </span>
              <span className="font-mono text-sm text-ink-2">
                경과: {stream.elapsed}
              </span>
              <span className="font-mono text-sm text-ink-2">
                토큰: {stream.tokenCount.toLocaleString()}
              </span>
            </div>
          </div>

          <div className="flex flex-col gap-6">
            <div className="flex flex-col lg:flex-row gap-6">
              <div className="flex-1 bg-[#1e1e1e] rounded-lg p-4 h-72 lg:h-96 overflow-y-auto font-mono text-sm">
                {stream.logs.map((log, i) => (
                  <div key={i} className="flex gap-2 mb-2">
                    <span className={cn("shrink-0", getAgentColor(log.agent))}>
                      [{log.agent}]
                    </span>
                    <span>
                      {log.type === "success" && "✅ "}
                      {log.type === "running" && "🔄 "}
                      {log.type === "interrupt" && "⚠️ "}
                      {log.type === "error" && "❌ "}
                    </span>
                    <span className="text-gray-300">{log.message}</span>
                  </div>
                ))}
                {stream.logs.length === 0 && (
                  <div className="text-gray-500">실행 대기 중...</div>
                )}
              </div>

              <div className="lg:w-64 space-y-4 shrink-0">
                <div className="bg-surface border border-border rounded-lg p-4 space-y-4">
                  <div className="font-label uppercase tracking-wider text-xs text-ink-2">
                    실행 현황
                  </div>
                  <div className="space-y-2 text-sm">
                    {["orchestrator", "worker_a", "worker_b", "reviewer"].map(
                      (agent) => {
                        const agentLogs = stream.logs.filter(
                          (l) => l.agent === agent,
                        );
                        const lastLog = agentLogs[agentLogs.length - 1];
                        const status = !lastLog
                          ? "⏳"
                          : lastLog.type === "success"
                            ? "✅"
                            : "🔄";
                        return (
                          <div key={agent} className="flex justify-between">
                            <span className={getAgentColor(agent)}>{agent}</span>
                            <span>{status}</span>
                          </div>
                        );
                      },
                    )}
                  </div>
                  <div className="border-t border-border pt-3 space-y-1 text-xs text-ink-2">
                    <div>
                      LLM 호출:{" "}
                      {stream.logs.filter((l) => l.type === "success").length}회
                    </div>
                    <div>토큰: {stream.tokenCount.toLocaleString()}</div>
                    <div>경과: {stream.elapsed}</div>
                  </div>
                </div>
              </div>
            </div>

            {/* Read-only generated code */}
            <div className="space-y-2">
              <div className="flex flex-wrap items-center gap-2">
                <ArenaBadge color="bg-blue/10 text-blue">Read-only</ArenaBadge>
                <ArenaBadge color="bg-ink/5 text-ink-2">
                  agent-generated harness.py
                </ArenaBadge>
              </div>
              <pre
                className="w-full max-h-64 overflow-auto bg-[#1e1e1e] text-green-400 font-mono text-sm p-4 rounded-lg border border-border whitespace-pre-wrap select-text"
                aria-readonly="true"
              >
                {MOCK_GENERATED_HARNESS}
              </pre>
              <p className="text-xs text-ink-3">
                편집 불가. 복사는 정책에 따라 제한할 수 있습니다(현재 데모는
                선택 가능).
              </p>
            </div>

            {/* Control signals only — no free-form chat */}
            <div className="rounded-lg border border-border bg-surface p-4 space-y-3">
              <div className="font-label uppercase tracking-wider text-xs text-ink-2">
                컨트롤 신호 (모니터링 / 인터럽트)
              </div>
              <p className="text-xs text-ink-3">
                자연어 바이브 코딩 입력은 제공하지 않습니다. 아래 버튼만
                허용됩니다.
              </p>
              <div className="flex flex-wrap gap-2">
                <ArenaButton
                  variant="ghost"
                  size="sm"
                  onClick={() => sendControlSignal("stop")}
                >
                  작업 멈춰
                </ArenaButton>
                <ArenaButton
                  variant="ghost"
                  size="sm"
                  onClick={() => sendControlSignal("summarize")}
                >
                  상황 요약해
                </ArenaButton>
                {stream.status === "interrupted" && (
                  <ArenaButton
                    variant="red"
                    size="sm"
                    onClick={() => sendControlSignal("resume")}
                  >
                    계속 진행
                  </ArenaButton>
                )}
              </div>
              {lastControlSignal && (
                <p className="text-xs text-ink-3 font-mono">
                  마지막 신호: {lastControlSignal}
                </p>
              )}
            </div>

            {monitorSummary && (
              <div className="rounded-lg border border-blue/20 bg-blue/5 p-4 text-sm text-ink-2 whitespace-pre-wrap">
                {monitorSummary}
              </div>
            )}

            {stream.status === "interrupted" && (
              <div className="bg-surface border-2 border-red/30 rounded-lg p-5 space-y-3">
                <div className="flex items-center gap-2">
                  <span className="text-lg">⚠️</span>
                  <span className="font-label uppercase tracking-wider text-xs font-semibold">
                    에이전트 인터럽트
                  </span>
                </div>
                <div className="text-sm text-ink-2">
                  [orchestrator]: 하이닉스도 분석 범위에 포함할까요?
                </div>
                <p className="text-xs text-ink-3">
                  응답은 자유 텍스트가 아니라 위 패널의{" "}
                  <strong className="text-ink">계속 진행</strong> 등 컨트롤
                  신호로만 처리됩니다.
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Step 3: Result */}
      {phase === "result" && (
        <div className="max-w-lg mx-auto space-y-8">
          <div className="text-center space-y-2">
            <span className="text-4xl">⚔️</span>
            <h2 className="font-title text-4xl">전투 완료</h2>
          </div>

          <div className="space-y-4">
            <StatBar label="Quality" value={84.2} color="red" />
            <StatBar label="Speed" value={96.1} color="blue" />
            <div className="border-t border-border pt-4">
              <StatBar label="Final" value={88.1} color="red" />
            </div>
          </div>

          <div className="bg-surface border border-border rounded-lg p-5 space-y-3 text-center">
            <div className="font-label uppercase tracking-wider text-xs text-ink-2">
              현재 순위
            </div>
            <div className="font-title text-5xl text-red">🥈 2위</div>
            <div className="text-sm text-ink-2">/ 23명</div>
            <OnChainBadge className="justify-center" />
          </div>

          <div className="text-sm text-ink-2 text-center">
            토큰 사용: 6,700 (-67 크레딧)
          </div>

          <div className="flex gap-4 justify-center">
            <ArenaButton
              variant="red"
              onClick={() => {
                setPhase("submit");
                stream.stop();
              }}
            >
              재도전
            </ArenaButton>
            <Link href={`/challenges/${id}`}>
              <ArenaButton variant="ghost">랭킹 보기</ArenaButton>
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}

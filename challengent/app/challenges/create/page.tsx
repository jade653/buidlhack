"use client";

import { useState } from "react";
import { ArenaButton } from "@/components/ui/ArenaButton";
import { ArenaBadge } from "@/components/ui/ArenaBadge";
import { ArenaCard } from "@/components/ui/ArenaCard";
import { CATEGORY_LABELS } from "@/lib/types";
import { getCategoryColor } from "@/lib/utils";

type Step = 1 | 2 | 3 | 4;

export default function ChallengeCreatePage() {
  const [step, setStep] = useState<Step>(1);
  const [form, setForm] = useState({
    title: "",
    category: "research" as keyof typeof CATEGORY_LABELS,
    description: "",
    bounty: 100,
    deadline: "",
    maxRuns: 5,
    inputSchema: '{\n  "companies": ["string"],\n  "period": "string"\n}',
    outputSchema: '{\n  "report": "string",\n  "data": [{}]\n}',
    evalLevel: 1 as 1 | 2 | 3,
    weights: { accuracy: 40, completeness: 30, format: 15, speed: 15 },
  });

  const steps = [
    { num: 1, label: "기본 정보" },
    { num: 2, label: "입출력" },
    { num: 3, label: "평가 방식" },
    { num: 4, label: "확인 & 등록" },
  ];

  const totalWeight = Object.values(form.weights).reduce((a, b) => a + b, 0);

  return (
    <div className="pt-24 max-w-7xl mx-auto px-6 pb-16">
      {/* Step indicator */}
      <div className="flex items-center justify-center gap-2 mb-12">
        {steps.map((s, i) => (
          <div key={s.num} className="flex items-center gap-2">
            <button
              onClick={() => setStep(s.num as Step)}
              className={`cursor-pointer w-8 h-8 rounded-full flex items-center justify-center font-title text-sm ${
                step === s.num
                  ? "bg-red text-white"
                  : step > s.num
                    ? "bg-green text-white"
                    : "bg-ink/10 text-ink-2"
              }`}
            >
              {s.num}
            </button>
            <span
              className={`font-label uppercase tracking-wider text-xs hidden sm:inline ${
                step === s.num ? "text-ink" : "text-ink-3"
              }`}
            >
              {s.label}
            </span>
            {i < steps.length - 1 && (
              <div className="w-8 h-[1px] bg-ink/10 mx-1" />
            )}
          </div>
        ))}
      </div>

      {/* Step 1: Basic Info */}
      {step === 1 && (
        <div className="space-y-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-8 h-[2px] bg-red" />
            <span className="font-label uppercase tracking-[0.2em] text-xs text-ink-2">
              {"// basic info"}
            </span>
          </div>

          <div>
            <label className="font-label uppercase tracking-wider text-xs text-ink-2 block mb-2">
              제목
            </label>
            <input
              type="text"
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
              className="w-full border border-border rounded-[4px] px-4 py-3 font-body bg-surface focus:outline-none focus:border-red"
              placeholder="챌린지 제목을 입력하세요"
            />
          </div>

          <div>
            <label className="font-label uppercase tracking-wider text-xs text-ink-2 block mb-2">
              카테고리
            </label>
            <div className="flex flex-wrap gap-2">
              {Object.entries(CATEGORY_LABELS).map(([key, label]) => (
                <button
                  key={key}
                  onClick={() =>
                    setForm({
                      ...form,
                      category: key as keyof typeof CATEGORY_LABELS,
                    })
                  }
                  className="cursor-pointer"
                >
                  <ArenaBadge
                    color={
                      form.category === key
                        ? "bg-red text-white"
                        : getCategoryColor(key)
                    }
                  >
                    {label}
                  </ArenaBadge>
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="font-label uppercase tracking-wider text-xs text-ink-2 block mb-2">
              상세 설명
            </label>
            <textarea
              value={form.description}
              onChange={(e) =>
                setForm({ ...form, description: e.target.value })
              }
              className="w-full border border-border rounded-[4px] px-4 py-3 font-body bg-surface focus:outline-none focus:border-red h-32 resize-none"
              placeholder="마크다운으로 작성하세요"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="font-label uppercase tracking-wider text-xs text-ink-2 block mb-2">
                바운티 (NEAR)
              </label>
              <input
                type="number"
                value={form.bounty}
                onChange={(e) =>
                  setForm({ ...form, bounty: parseInt(e.target.value) || 0 })
                }
                className="w-full border border-border rounded-[4px] px-4 py-3 font-body bg-surface focus:outline-none focus:border-red"
              />
            </div>
            <div>
              <label className="font-label uppercase tracking-wider text-xs text-ink-2 block mb-2">
                마감일
              </label>
              <input
                type="date"
                value={form.deadline}
                onChange={(e) => setForm({ ...form, deadline: e.target.value })}
                className="w-full border border-border rounded-[4px] px-4 py-3 font-body bg-surface focus:outline-none focus:border-red"
              />
            </div>
          </div>

          <div>
            <label className="font-label uppercase tracking-wider text-xs text-ink-2 block mb-2">
              참여당 최대 실행 횟수
            </label>
            <input
              type="number"
              value={form.maxRuns}
              onChange={(e) =>
                setForm({ ...form, maxRuns: parseInt(e.target.value) || 1 })
              }
              className="w-full max-w-[200px] border border-border rounded-[4px] px-4 py-3 font-body bg-surface focus:outline-none focus:border-red"
            />
          </div>

          <div className="flex justify-end">
            <ArenaButton variant="red" onClick={() => setStep(2)}>
              다음 &rarr;
            </ArenaButton>
          </div>
        </div>
      )}

      {/* Step 2: Schema */}
      {step === 2 && (
        <div className="space-y-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-8 h-[2px] bg-blue" />
            <span className="font-label uppercase tracking-[0.2em] text-xs text-ink-2">
              {"// input & output"}
            </span>
          </div>

          <div>
            <label className="font-label uppercase tracking-wider text-xs text-ink-2 block mb-2">
              Input Schema (JSON)
            </label>
            <textarea
              value={form.inputSchema}
              onChange={(e) =>
                setForm({ ...form, inputSchema: e.target.value })
              }
              className="w-full border border-border rounded-[4px] px-4 py-3 font-mono text-sm bg-ink/[0.03] focus:outline-none focus:border-blue h-40 resize-none"
            />
          </div>

          <div>
            <label className="font-label uppercase tracking-wider text-xs text-ink-2 block mb-2">
              Output Schema (JSON)
            </label>
            <textarea
              value={form.outputSchema}
              onChange={(e) =>
                setForm({ ...form, outputSchema: e.target.value })
              }
              className="w-full border border-border rounded-[4px] px-4 py-3 font-mono text-sm bg-ink/[0.03] focus:outline-none focus:border-blue h-40 resize-none"
            />
          </div>

          <div className="flex justify-between">
            <ArenaButton variant="ghost" onClick={() => setStep(1)}>
              &larr; 이전
            </ArenaButton>
            <ArenaButton variant="blue" onClick={() => setStep(3)}>
              다음 &rarr;
            </ArenaButton>
          </div>
        </div>
      )}

      {/* Step 3: Evaluation */}
      {step === 3 && (
        <div className="space-y-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-8 h-[2px] bg-red" />
            <span className="font-label uppercase tracking-[0.2em] text-xs text-ink-2">
              {"// evaluation"}
            </span>
          </div>

          <div className="flex gap-2 mb-6">
            {[
              { level: 1, label: "노코드" },
              { level: 2, label: "함수 업로드" },
              { level: 3, label: "완전 커스텀" },
            ].map((l) => (
              <button
                key={l.level}
                onClick={() =>
                  setForm({ ...form, evalLevel: l.level as 1 | 2 | 3 })
                }
                className="cursor-pointer"
              >
                <ArenaBadge
                  color={
                    form.evalLevel === l.level
                      ? "bg-red text-white"
                      : "bg-ink/5 text-ink-2"
                  }
                >
                  Level {l.level} — {l.label}
                </ArenaBadge>
              </button>
            ))}
          </div>

          {form.evalLevel === 1 && (
            <div className="space-y-4">
              {Object.entries(form.weights).map(([key, value]) => (
                <div key={key}>
                  <div className="flex justify-between items-center mb-1">
                    <span className="font-label uppercase tracking-wider text-xs text-ink-2">
                      {key === "accuracy"
                        ? "정확도"
                        : key === "completeness"
                          ? "완결성"
                          : key === "format"
                            ? "형식 준수"
                            : "Speed"}
                    </span>
                    <span className="font-title text-lg">{value}%</span>
                  </div>
                  <input
                    type="range"
                    min={0}
                    max={100}
                    value={value}
                    onChange={(e) =>
                      setForm({
                        ...form,
                        weights: {
                          ...form.weights,
                          [key]: parseInt(e.target.value),
                        },
                      })
                    }
                    className="w-full accent-red"
                  />
                </div>
              ))}
              <div
                className={`font-label text-xs uppercase tracking-wider ${
                  totalWeight === 100 ? "text-green" : "text-red"
                }`}
              >
                합계: {totalWeight}% {totalWeight === 100 ? "✓" : "(100% 필요)"}
              </div>
            </div>
          )}

          {form.evalLevel === 2 && (
            <div className="space-y-4">
              <pre className="bg-ink/[0.03] border border-border rounded-lg p-4 text-sm font-mono overflow-x-auto">
                {`# 인터페이스 (고정)
def evaluate(
    output: dict,
    ground_truth: dict,
    metadata: dict   # wall_time, token_usage
) -> dict:
    return {
        "total_score": float,   # 0.0 ~ 100.0
        "breakdown": dict,      # 항목별 점수
        "feedback": str         # 유저에게 표시
    }`}
              </pre>
              <p className="text-sm text-ink-2">
                위 인터페이스를 구현한 Python 파일을 업로드하세요.
              </p>
              <ArenaButton variant="ghost" size="sm">
                파일 업로드
              </ArenaButton>
            </div>
          )}

          {form.evalLevel === 3 && (
            <div className="space-y-4">
              <ArenaCard>
                <div className="space-y-3">
                  <p className="text-sm text-ink-2">
                    ground_truth.json과 eval_script.py를 업로드하세요.
                  </p>
                  <div className="flex gap-3">
                    <ArenaButton variant="ghost" size="sm">
                      ground_truth.json 업로드
                    </ArenaButton>
                    <ArenaButton variant="ghost" size="sm">
                      eval_script.py 업로드
                    </ArenaButton>
                  </div>
                  <p className="text-xs text-green font-label uppercase tracking-wider">
                    암호화 저장됩니다
                  </p>
                </div>
              </ArenaCard>
            </div>
          )}

          <div className="flex justify-between pt-4">
            <ArenaButton variant="ghost" onClick={() => setStep(2)}>
              &larr; 이전
            </ArenaButton>
            <ArenaButton variant="red" onClick={() => setStep(4)}>
              다음 &rarr;
            </ArenaButton>
          </div>
        </div>
      )}

      {/* Step 4: Confirm */}
      {step === 4 && (
        <div className="space-y-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-8 h-[2px] bg-green" />
            <span className="font-label uppercase tracking-[0.2em] text-xs text-ink-2">
              {"// confirm & register"}
            </span>
          </div>

          <ArenaCard>
            <div className="space-y-4">
              <div className="flex justify-between items-start">
                <ArenaBadge color={getCategoryColor(form.category)}>
                  {CATEGORY_LABELS[form.category]}
                </ArenaBadge>
                <ArenaBadge color="bg-ink/5 text-ink-2">미리보기</ArenaBadge>
              </div>
              <h3 className="font-label text-lg font-semibold">
                {form.title || "챌린지 제목"}
              </h3>
              <p className="text-sm text-ink-2">
                {form.description || "설명이 여기에 표시됩니다."}
              </p>
              <div className="font-title text-2xl text-red">
                {form.bounty} NEAR
              </div>
              <div className="text-xs text-ink-3">
                마감: {form.deadline || "미설정"} · 최대 실행: {form.maxRuns}회
              </div>
            </div>
          </ArenaCard>

          <div className="flex justify-between pt-4">
            <ArenaButton variant="ghost" onClick={() => setStep(3)}>
              &larr; 이전
            </ArenaButton>
            <ArenaButton
              variant="red"
              size="lg"
              onClick={() => {
                // TODO: connect to backend — submit challenge & deposit bounty via NEAR Wallet
                alert("챌린지가 등록되었습니다! (목 모드)");
              }}
            >
              챌린지 등록하기
            </ArenaButton>
          </div>
        </div>
      )}
    </div>
  );
}

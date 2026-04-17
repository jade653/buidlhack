import ReactMarkdown from "react-markdown";
import { SKILL_MD } from "@/lib/skill-md";

export default function SkillPage() {
  return (
    <div className="pt-24 max-w-7xl mx-auto px-6 pb-16">
      <div className="space-y-4 mb-8">
        <div className="flex items-center gap-3">
          <div className="w-8 h-[2px] bg-blue" />
          <span className="font-label uppercase tracking-[0.2em] text-xs text-ink-2">
            {"// docs for autonomous agents"}
          </span>
        </div>
        <h1 className="font-title text-5xl md:text-6xl text-ink">SKILL.MD</h1>
        <p className="font-body text-ink-2">
          This is the API guide for agents.
        </p>
      </div>

      <article className="bg-surface border border-border rounded-lg p-6 md:p-8">
        <div className="prose prose-sm max-w-none prose-headings:font-title prose-code:bg-ink/5 prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded prose-pre:bg-ink/5 prose-pre:rounded-lg">
          <ReactMarkdown>{SKILL_MD}</ReactMarkdown>
        </div>
      </article>

      <p className="mt-6 text-xs text-ink-3">
        TODO: connect to backend - API key 발급/호출 테스트 콘솔 연동
      </p>
    </div>
  );
}

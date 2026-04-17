export function MyAgentStats() {
  return (
    <div className="bg-surface border border-border rounded-lg p-5 flex flex-wrap gap-8">
      {[
        { label: "총 참여", value: "17" },
        { label: "바운티", value: "1,200 NEAR" },
        { label: "평균 점수", value: "94.2" },
        { label: "랭킹", value: "\u{1F947} 3위" },
      ].map((stat) => (
        <div key={stat.label}>
          <div className="font-title text-2xl text-ink">{stat.value}</div>
          <div className="font-label uppercase tracking-[0.15em] text-[11px] text-ink-3">
            {stat.label}
          </div>
        </div>
      ))}
    </div>
  );
}

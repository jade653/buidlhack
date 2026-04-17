export function cn(...classes: (string | undefined | null | false)[]) {
  return classes.filter(Boolean).join(" ");
}

export function getRankEmoji(rank: number): string {
  switch (rank) {
    case 1:
      return "\u{1F947}";
    case 2:
      return "\u{1F948}";
    case 3:
      return "\u{1F949}";
    default:
      return `${rank}`;
  }
}

export function formatNEAR(amount: number): string {
  return "$" + amount.toLocaleString();
}

export function getCategoryColor(category: string): string {
  switch (category) {
    case "research":
      return "bg-blue/10 text-blue";
    case "code":
      return "bg-red/10 text-red";
    case "data":
      return "bg-green/10 text-green";
    case "decision":
      return "bg-amber-100 text-amber-700";
    case "content":
      return "bg-purple-100 text-purple-700";
    default:
      return "bg-ink-3/20 text-ink-2";
  }
}

export function getAgentColor(agent: string): string {
  switch (agent) {
    case "orchestrator":
      return "text-red";
    case "worker_a":
      return "text-blue";
    case "worker_b":
      return "text-green";
    case "reviewer":
      return "text-amber-600";
    default:
      return "text-ink";
  }
}

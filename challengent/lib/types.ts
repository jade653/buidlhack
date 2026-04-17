export interface Challenge {
  id: string;
  title: string;
  category: "research" | "code" | "data" | "decision" | "content";
  description: string;
  bounty: number;
  deadline: string;
  daysLeft: number;
  participants: number;
  topScore: number;
  status: "active" | "upcoming" | "completed";
  company: string;
}

export interface LeaderboardEntry {
  rank: number;
  agentName: string;
  trainer: string;
  challenges: number;
  avgScore: number;
  bounty: number;
  verified: boolean;
}

export type AgentPosition = "top" | "tr" | "br" | "bottom" | "bl" | "tl";

export interface AgentSlot {
  position: AgentPosition;
  rank: number;
  name: string;
  score: number;
}

export interface ExecutionLog {
  delay: number;
  agent: "orchestrator" | "worker_a" | "worker_b" | "reviewer";
  type: "success" | "running" | "interrupt" | "error";
  message: string;
}

export interface ChallengeInfo {
  title: string;
  bounty: number;
  isLive: boolean;
}

export type CategoryLabel = {
  [key in Challenge["category"]]: string;
};

export const CATEGORY_LABELS: CategoryLabel = {
  research: "리서치",
  code: "코드",
  data: "데이터",
  decision: "의사결정",
  content: "콘텐츠",
};

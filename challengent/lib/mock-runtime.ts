import { AgentSlot, ExecutionLog, LeaderboardEntry } from "./types";

export const mockLeaderboard: LeaderboardEntry[] = [
  {
    rank: 1,
    agentName: "AlphaAgent-v3",
    principalType: "agent",
    trainer: "@trainer_kim",
    challenges: 17,
    avgScore: 94.2,
    bounty: 1200,
    verified: true,
  },
  {
    rank: 2,
    agentName: "ResearchBot",
    principalType: "agent",
    trainer: "@agent_lee",
    challenges: 12,
    avgScore: 91.8,
    bounty: 480,
    verified: true,
  },
  {
    rank: 3,
    agentName: "CrewMaster",
    principalType: "human",
    trainer: "@dev_park",
    challenges: 8,
    avgScore: 89.5,
    bounty: 200,
    verified: true,
  },
  {
    rank: 4,
    agentName: "SwiftAgent",
    principalType: "agent",
    trainer: "@fast_choi",
    challenges: 21,
    avgScore: 87.1,
    bounty: 150,
    verified: true,
  },
  {
    rank: 5,
    agentName: "NexusAI",
    principalType: "agent",
    trainer: "@nexus_yoon",
    challenges: 9,
    avgScore: 85.3,
    bounty: 120,
    verified: true,
  },
  {
    rank: 6,
    agentName: "DataHunter",
    principalType: "human",
    trainer: "@data_jung",
    challenges: 14,
    avgScore: 83.9,
    bounty: 95,
    verified: true,
  },
  {
    rank: 7,
    agentName: "CodeNinja",
    principalType: "agent",
    trainer: "@ninja_han",
    challenges: 6,
    avgScore: 82.4,
    bounty: 80,
    verified: true,
  },
  {
    rank: 8,
    agentName: "LogicFlow",
    principalType: "human",
    trainer: "@logic_oh",
    challenges: 11,
    avgScore: 80.1,
    bounty: 60,
    verified: true,
  },
];

export const mockHexAgents: AgentSlot[] = [
  { position: "top", rank: 1, name: "AlphaAgent-v3", score: 97.3 },
  { position: "tr", rank: 2, name: "ResearchBot", score: 94.1 },
  { position: "br", rank: 3, name: "CrewMaster", score: 91.8 },
  { position: "bottom", rank: 4, name: "SwiftAgent", score: 88.5 },
  { position: "bl", rank: 5, name: "NexusAI", score: 85.2 },
  { position: "tl", rank: 6, name: "DataHunter", score: 82.7 },
];

export const mockExecutionStream: ExecutionLog[] = [
  {
    delay: 800,
    agent: "orchestrator",
    type: "success",
    message: "Task analysis complete -> dispatched to worker_a and worker_b",
  },
  {
    delay: 1500,
    agent: "worker_a",
    type: "running",
    message: "Collecting Samsung Electronics data...",
  },
  {
    delay: 2000,
    agent: "worker_b",
    type: "running",
    message: "Collecting LG Electronics data...",
  },
  {
    delay: 3500,
    agent: "worker_a",
    type: "success",
    message:
      "Completed (1,240 tokens) - Samsung Electronics FY2024 revenue reached 300T KRW...",
  },
  {
    delay: 4200,
    agent: "worker_b",
    type: "success",
    message:
      "Completed (980 tokens) - LG Electronics operating profit reached 3.5T KRW...",
  },
  {
    delay: 5000,
    agent: "orchestrator",
    type: "interrupt",
    message: "Should we include SK Hynix in the analysis scope as well?",
  },
  {
    delay: 7000,
    agent: "worker_a",
    type: "running",
    message: "Collecting SK Hynix data...",
  },
  {
    delay: 9000,
    agent: "worker_a",
    type: "success",
    message:
      "Completed (1,100 tokens) - SK Hynix HBM revenue shows sharp growth...",
  },
  {
    delay: 10000,
    agent: "reviewer",
    type: "running",
    message: "Validating final report...",
  },
  {
    delay: 12000,
    agent: "reviewer",
    type: "success",
    message: "Validation complete - final score: 94.2",
  },
];


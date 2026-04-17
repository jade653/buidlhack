import { Challenge, LeaderboardEntry, AgentSlot, ExecutionLog } from "./types";

export const mockChallenges: Challenge[] = [
  {
    id: "challenge-001",
    title: "Editorial Cosmetics Landing Page Generation",
    category: "content",
    description:
      "Generate a single-file premium cosmetics storefront from the provided brand brief and product metadata.",
    inputOutputSpec: `Input: {
  "brand": "Luma Dew",
  "tagline": "Clinical glow, everyday ritual.",
  "audience": "Style-conscious customers in their 20s and 30s who want clean skincare with a premium feel.",
  "theme": "Soft editorial beauty brand with warm neutrals and elegant product storytelling.",
  "products": [
    { "name": "Petal Clean Gel Cleanser", "description": "...", "price": "$24" },
    { "name": "Glass Drop Niacinamide Serum", "description": "...", "price": "$38" },
    { "name": "Velvet Barrier Cream", "description": "...", "price": "$42" }
  ],
  "features": [
    "Cruelty-free formulas",
    "Dermatologist tested",
    "Sensitive-skin friendly",
    "Free shipping over $60"
  ]
}

Output: {
  "output": "Single-file HTML storefront string",
  "score": 0.0 ~ 1.0
}`,
    bounty: 350,
    deadline: "2025-12-25",
    daysLeft: 2,
    participants: 6,
    topScore: 96.4,
    status: "active",
    company: "Luma Dew",
    evaluationCriteria: [
      { key: "brand_consistency", label: "Brand Consistency", weight: 35 },
      { key: "copy_quality", label: "Copy Quality", weight: 25 },
      { key: "spec_compliance", label: "Spec Compliance", weight: 20 },
      { key: "speed", label: "Speed", weight: 10 },
      { key: "efficiency", label: "Efficiency", weight: 10 },
    ],
  },
  {
    id: "challenge-002",
    title: "Automated Competitor Market Analysis Report",
    category: "research",
    description:
      "Analyze five companies with multi-agent workflows and generate a structured report.",
    inputOutputSpec: `Input: {
  "companies": ["Samsung Electronics", "LG Electronics", "SK Hynix", "Hyundai Motor", "POSCO"],
  "period": "FY2024"
}

Output: {
  "report": "Analysis report in markdown format",
  "data": [{ "company": "string", "revenue": number, "growth": number }]
}`,
    bounty: 500,
    deadline: "2025-12-31",
    daysLeft: 7,
    participants: 23,
    topScore: 97.3,
    status: "active",
    company: "Samsung SDS",
    evaluationCriteria: [
      { key: "accuracy", label: "Accuracy", weight: 40 },
      { key: "completeness", label: "Completeness", weight: 30 },
      { key: "format", label: "Format Compliance", weight: 15 },
      { key: "speed", label: "Speed", weight: 15 },
      { key: "efficiency", label: "Efficiency", weight: "Reference" },
      { key: "reliability", label: "Reliability", weight: "Reference" },
    ],
  },

  {
    id: "challenge-003",
    title: "Unstructured Data Cleaning and Classification",
    category: "data",
    description:
      "Clean 1,000 rows of noisy CSV data and classify each row into the correct category.",
    inputOutputSpec: `Input: {
  "rows": [{ "raw": "string" }],
  "label_set": ["category_a", "category_b", "category_c"]
}

Output: {
  "cleaned_rows": [{ "text": "string", "label": "string" }],
  "score": 0.0 ~ 1.0
}`,
    bounty: 200,
    deadline: "2025-12-20",
    daysLeft: 14,
    participants: 15,
    topScore: 89.2,
    status: "active",
    company: "Naver",
    evaluationCriteria: [
      { key: "accuracy", label: "Accuracy", weight: 40 },
      { key: "completeness", label: "Completeness", weight: 30 },
      { key: "format", label: "Format Compliance", weight: 15 },
      { key: "speed", label: "Speed", weight: 15 },
      { key: "efficiency", label: "Efficiency", weight: "Reference" },
      { key: "reliability", label: "Reliability", weight: "Reference" },
    ],
  },
  {
    id: "challenge-004",
    title: "Automated Customer Churn Prediction Model",
    category: "decision",
    description:
      "Build a model that analyzes customer data and predicts churn probability.",
    inputOutputSpec: `Input: {
  "customers": [{ "features": { "...": "..." } }]
}

Output: {
  "predictions": [{ "customer_id": "string", "churn_probability": number }],
  "score": 0.0 ~ 1.0
}`,
    bounty: 400,
    deadline: "2025-12-28",
    daysLeft: 5,
    participants: 31,
    topScore: 92.1,
    status: "active",
    company: "SK Telecom",
    evaluationCriteria: [
      { key: "accuracy", label: "Accuracy", weight: 40 },
      { key: "completeness", label: "Completeness", weight: 30 },
      { key: "format", label: "Format Compliance", weight: 15 },
      { key: "speed", label: "Speed", weight: 15 },
      { key: "efficiency", label: "Efficiency", weight: "Reference" },
      { key: "reliability", label: "Reliability", weight: "Reference" },
    ],
  },
  {
    id: "challenge-005",
    title: "Automated Marketing Copy Generation",
    category: "content",
    description:
      "Automatically generate social media copy that follows the brand guidelines.",
    inputOutputSpec: `Input: {
  "brand_guide": "string",
  "campaign_goal": "string",
  "channels": ["instagram", "x", "blog"]
}

Output: {
  "copies": [{ "channel": "string", "text": "string" }],
  "score": 0.0 ~ 1.0
}`,
    bounty: 150,
    deadline: "2025-12-22",
    daysLeft: 10,
    participants: 18,
    topScore: 88.7,
    status: "active",
    company: "LG CNS",
    evaluationCriteria: [
      { key: "accuracy", label: "Accuracy", weight: 40 },
      { key: "completeness", label: "Completeness", weight: 30 },
      { key: "format", label: "Format Compliance", weight: 15 },
      { key: "speed", label: "Speed", weight: 15 },
      { key: "efficiency", label: "Efficiency", weight: "Reference" },
      { key: "reliability", label: "Reliability", weight: "Reference" },
    ],
  },
  {
    id: "challenge-006",
    title: "Automated Code Review Agent",
    category: "code",
    description:
      "Analyze pull request code and generate structured, actionable feedback.",
    inputOutputSpec: `Input: {
  "diff": "unified diff text",
  "repository_context": "optional context",
  "rules": ["security", "performance", "maintainability"]
}

Output: {
  "findings": [{ "severity": "high|medium|low", "comment": "string" }],
  "score": 0.0 ~ 1.0
}`,
    bounty: 350,
    deadline: "2026-01-15",
    daysLeft: 21,
    participants: 8,
    topScore: 0,
    status: "upcoming",
    company: "Toss",
    evaluationCriteria: [
      { key: "accuracy", label: "Accuracy", weight: 40 },
      { key: "completeness", label: "Completeness", weight: 30 },
      { key: "format", label: "Format Compliance", weight: 15 },
      { key: "speed", label: "Speed", weight: 15 },
      { key: "efficiency", label: "Efficiency", weight: "Reference" },
      { key: "reliability", label: "Reliability", weight: "Reference" },
    ],
  },
];

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

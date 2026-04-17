"use client";

import { useState, useEffect, useCallback } from "react";
import { AgentSlot } from "@/lib/types";
import { mockHexAgents } from "@/lib/mock-data";

const POSITIONS: AgentSlot["position"][] = [
  "top",
  "tr",
  "br",
  "bottom",
  "bl",
  "tl",
];

export function useHexArenaSimulation(
  initialAgents?: AgentSlot[],
  interval = 3000
) {
  const [agents, setAgents] = useState<AgentSlot[]>(
    initialAgents || mockHexAgents
  );

  const shuffle = useCallback(() => {
    setAgents((prev) => {
      const next = prev.map((a) => ({
        ...a,
        score: Math.max(
          60,
          Math.min(100, a.score + (Math.random() - 0.5) * 4)
        ),
      }));
      next.sort((a, b) => b.score - a.score);
      return next.map((a, i) => ({
        ...a,
        rank: i + 1,
        position: POSITIONS[i],
      }));
    });
  }, []);

  useEffect(() => {
    const id = setInterval(shuffle, interval);
    return () => clearInterval(id);
  }, [shuffle, interval]);

  return agents;
}

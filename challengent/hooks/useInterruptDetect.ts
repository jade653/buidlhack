"use client";

import { useMemo } from "react";

interface InterruptInfo {
  line: number;
  type: string;
}

export function useInterruptDetect(code: string) {
  const interrupts = useMemo(() => {
    const results: InterruptInfo[] = [];
    const lines = code.split("\n");
    lines.forEach((line, i) => {
      const match = line.match(/interrupt\s*\(\s*["']?(\w+)["']?/);
      if (match) {
        results.push({ line: i + 1, type: match[1] || "unknown" });
      }
    });
    return results;
  }, [code]);

  return {
    hasInterrupts: interrupts.length > 0,
    interrupts,
    count: interrupts.length,
  };
}

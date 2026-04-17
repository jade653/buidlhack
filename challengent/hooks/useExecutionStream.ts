"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { ExecutionLog } from "@/lib/types";
import { mockExecutionStream } from "@/lib/mock-data";

type StreamStatus = "idle" | "running" | "interrupted" | "completed";

export function useExecutionStream() {
  const [logs, setLogs] = useState<ExecutionLog[]>([]);
  const [status, setStatus] = useState<StreamStatus>("idle");
  const [elapsedMs, setElapsedMs] = useState(0);
  const [tokenCount, setTokenCount] = useState(0);
  const timersRef = useRef<ReturnType<typeof setTimeout>[]>([]);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const start = useCallback(() => {
    setLogs([]);
    setStatus("running");
    setElapsedMs(0);
    setTokenCount(0);

    intervalRef.current = setInterval(() => {
      setElapsedMs((prev) => prev + 1000);
    }, 1000);

    mockExecutionStream.forEach((log) => {
      const timer = setTimeout(() => {
        setLogs((prev) => [...prev, log]);
        if (log.type === "success") {
          const match = log.message.match(/([\d,]+)\s*tokens/);
          if (match) {
            setTokenCount((prev) => prev + parseInt(match[1].replace(",", ""), 10));
          }
        }
        if (log.type === "interrupt") {
          setStatus("interrupted");
        }
      }, log.delay);
      timersRef.current.push(timer);
    });

    const endTimer = setTimeout(() => {
      setStatus("completed");
      if (intervalRef.current) clearInterval(intervalRef.current);
    }, 13000);
    timersRef.current.push(endTimer);
  }, []);

  const stop = useCallback(() => {
    timersRef.current.forEach(clearTimeout);
    timersRef.current = [];
    if (intervalRef.current) clearInterval(intervalRef.current);
    setStatus("idle");
  }, []);

  const continueExecution = useCallback(() => {
    setStatus("running");
  }, []);

  useEffect(() => {
    return () => {
      timersRef.current.forEach(clearTimeout);
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, []);

  const formatTime = (ms: number) => {
    const s = Math.floor(ms / 1000);
    const m = Math.floor(s / 60);
    const sec = s % 60;
    return `${String(m).padStart(2, "0")}:${String(sec).padStart(2, "0")}`;
  };

  return {
    logs,
    status,
    elapsedMs,
    elapsed: formatTime(elapsedMs),
    tokenCount,
    start,
    stop,
    continueExecution,
  };
}

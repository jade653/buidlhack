"""
Token usage and execution timing tracker.

TokenTracker is passed into SandboxedNearAIClient. Each LLM call records
its token counts. The runner reads the final totals for ExecutionResult.

Usage:
    tracker = TokenTracker()
    tracker.start()
    # ... run code with client that holds a reference to tracker ...
    elapsed = tracker.elapsed()
    usage = tracker.to_dict()
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class _CallRecord:
    """One LLM API call's token counts."""
    model: str
    prompt_tokens: int
    completion_tokens: int


class TokenTracker:
    """
    Accumulates token usage across all LLM calls in one execution run.

    The tracker is shared between the runner and the client:
      - runner calls tracker.start() before handing execution to the sandbox
      - client calls tracker.record_call() after each API response
      - runner calls tracker.elapsed() and tracker.to_dict() when done
    """

    def __init__(self) -> None:
        self._records: List[_CallRecord] = []
        self._start_time: float = 0.0

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Mark the start of the timed execution window."""
        self._start_time = time.monotonic()

    def elapsed(self) -> float:
        """
        Wall-clock seconds since start() was called.
        Returns 0.0 if start() was never called.
        """
        if self._start_time == 0.0:
            return 0.0
        return time.monotonic() - self._start_time

    # ------------------------------------------------------------------
    # Recording
    # ------------------------------------------------------------------

    def record_call(
        self,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
    ) -> None:
        """Called by SandboxedNearAIClient after each successful API call."""
        self._records.append(
            _CallRecord(
                model=model,
                prompt_tokens=max(0, prompt_tokens),
                completion_tokens=max(0, completion_tokens),
            )
        )

    # ------------------------------------------------------------------
    # Aggregates
    # ------------------------------------------------------------------

    @property
    def call_count(self) -> int:
        return len(self._records)

    @property
    def total_prompt_tokens(self) -> int:
        return sum(r.prompt_tokens for r in self._records)

    @property
    def total_completion_tokens(self) -> int:
        return sum(r.completion_tokens for r in self._records)

    @property
    def total_tokens(self) -> int:
        return self.total_prompt_tokens + self.total_completion_tokens

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """
        Return a plain dict suitable for JSON serialisation and
        inclusion in ExecutionResult.token_usage.
        """
        return {
            "total_prompt_tokens": self.total_prompt_tokens,
            "total_completion_tokens": self.total_completion_tokens,
            "total_tokens": self.total_tokens,
            "call_count": self.call_count,
            "per_call": [
                {
                    "model": r.model,
                    "prompt_tokens": r.prompt_tokens,
                    "completion_tokens": r.completion_tokens,
                }
                for r in self._records
            ],
        }

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"TokenTracker(calls={self.call_count}, "
            f"total_tokens={self.total_tokens}, "
            f"elapsed={self.elapsed():.2f}s)"
        )

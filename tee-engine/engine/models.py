"""
Data models shared across the TEE engine.

Using stdlib dataclasses — no external dependencies needed here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Literal, Optional


@dataclass
class SubmissionConfig:
    """
    Configuration parsed from the user's optional config.json.

    If config.json is absent, SubmissionConfig.default() is used.

    Fields:
        model:       Near AI Cloud model identifier.
        temperature: Sampling temperature for LLM calls.
        max_tokens:  Maximum tokens per LLM completion.
        extra:       Any other keys from config.json, passed through as-is.
    """

    model: str = "near:deepseek-r1"
    temperature: float = 0.7
    max_tokens: int = 2000
    extra: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SubmissionConfig":
        known_keys = {"model", "temperature", "max_tokens"}
        return cls(
            model=str(data.get("model", "near:deepseek-r1")),
            temperature=float(data.get("temperature", 0.7)),
            max_tokens=int(data.get("max_tokens", 2000)),
            extra={k: v for k, v in data.items() if k not in known_keys},
        )

    @classmethod
    def default(cls) -> "SubmissionConfig":
        return cls()


@dataclass
class ExecutionResult:
    """
    Structured result returned by runner.run_submission().

    Fields:
        status:        "success" | "error" | "timeout"
        output:        The value of result["output"] from harness.py
        wall_time_sec: Total wall-clock seconds from exec start to finish
        token_usage:   Token usage dict from TokenTracker.to_dict()
        error:         Human-readable error string (None on success)
        metadata:      Extra info: captured print output, warnings, etc.
    """

    status: Literal["success", "error", "timeout"]
    output: Any = None
    wall_time_sec: float = 0.0
    token_usage: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_success(self) -> bool:
        return self.status == "success"

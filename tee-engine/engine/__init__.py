"""
tee-engine/engine — Python runtime for the Agent Challenge TEE.

Public API
----------
run_submission(submission_dir, challenge_input, **kwargs) -> ExecutionResult
    Execute a user submission against a challenge and return structured results.

ExecutionResult
    Dataclass holding status, output, score, wall_time_sec, token_usage,
    error, and metadata.

SubmissionConfig
    Dataclass parsed from the user's config.json (or defaults).

SandboxedNearAIClient
    OpenAI-compatible LLM client injected into user code as `llm`.

MockNearAIClient
    Drop-in replacement for local testing without a real API key.

TokenTracker
    Accumulates token counts and wall-clock time across LLM calls.

Quick start
-----------
    from engine import run_submission

    result = run_submission(
        submission_dir="samples/cosmetic1",
        challenge_input={"brand": "Luma Dew", "products": []},
    )
    print(result.status, result.score, result.output)
"""

from .client import MockNearAIClient, SandboxedNearAIClient
from .models import ExecutionResult, SubmissionConfig
from .runner import run_submission
from .tracker import TokenTracker

__all__ = [
    "run_submission",
    "ExecutionResult",
    "SubmissionConfig",
    "SandboxedNearAIClient",
    "MockNearAIClient",
    "TokenTracker",
]

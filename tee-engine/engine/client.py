"""
OpenAI-compatible client wrapper for Near AI Cloud.

The platform injects an instance of SandboxedNearAIClient into user code
as the `llm` global. The API key is never exposed to user code — it lives
only inside this module and the TEE environment.

Near AI Cloud base URL: https://cloud-api.near.ai/v1
API key env var:        NEAR_AI_API_KEY

Usage in harness.py:
    # Simple one-shot completion
    answer = llm.complete("What is 2+2?")

    # Full chat with message history
    response = llm.chat([
        {"role": "system", "content": agent_prompt},
        {"role": "user",   "content": "Summarise: " + challenge_input["text"]},
    ])
    text = response["content"]

    # Override model or params for one call
    response = llm.chat(messages, model="near:qwen3", temperature=0.2)
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import certifi
import httpx
from openai import OpenAI

from .tracker import TokenTracker

# ------------------------------------------------------------------
# Defaults — can be overridden at construction time
# ------------------------------------------------------------------

DEFAULT_BASE_URL = "https://cloud-api.near.ai/v1"
DEFAULT_MODEL = "near:deepseek-r1"
DEFAULT_TEMPERATURE = 0.7
DEFAULT_MAX_TOKENS = 2000


class SandboxedNearAIClient:
    """
    Thin wrapper around the OpenAI SDK pointed at Near AI Cloud.

    Key responsibilities:
      1. Hide the API key from user code.
      2. Record token usage for every call via TokenTracker.
      3. Provide a clean, simple interface (chat / complete).

    The model and generation params are taken from SubmissionConfig
    by default but can be overridden per call.

    TODO (production):
      - Add retry logic with exponential backoff.
      - Add per-call timeout.
      - Consider streaming for long completions (not needed for MVP).
      - Rate-limit to prevent credit overuse before execution limit kicks in.
    """

    def __init__(
        self,
        tracker: TokenTracker,
        model: str = DEFAULT_MODEL,
        base_url: str = DEFAULT_BASE_URL,
        api_key: Optional[str] = None,
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: int = DEFAULT_MAX_TOKENS,
    ) -> None:
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.tracker = tracker

        _api_key = api_key or os.environ.get("NEAR_AI_API_KEY", "")
        if not _api_key:
            # In TEE the key is always set; warn loudly for local dev.
            import warnings
            warnings.warn(
                "NEAR_AI_API_KEY is not set. "
                "LLM calls will fail unless a mock client is used.",
                stacklevel=2,
            )

        # openai.OpenAI accepts any base_url for OpenAI-compatible APIs.
        self._openai = OpenAI(
            api_key=_api_key or "placeholder-key",
            base_url=base_url,
            max_retries=1,
            http_client=httpx.Client(
                verify=certifi.where(),
                timeout=120.0,
            ),
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def chat(
        self,
        messages: List[Dict[str, str]],
        *,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **extra_kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Send a chat completion request.

        Args:
            messages:    List of {"role": "system"|"user"|"assistant",
                                  "content": "..."}
            model:       Override the default model for this call.
            temperature: Override the default temperature for this call.
            max_tokens:  Override the default max_tokens for this call.
            **extra_kwargs: Passed directly to the OpenAI SDK (e.g. top_p).

        Returns:
            {
                "content": str,           # assistant message text
                "model":   str,           # model that was used
                "usage":   {
                    "prompt_tokens":     int,
                    "completion_tokens": int,
                    "total_tokens":      int,
                },
            }

        Raises:
            openai.APIError: on network / auth / rate-limit errors.
        """
        _model = model or self.model
        _temperature = temperature if temperature is not None else self.temperature
        _max_tokens = max_tokens if max_tokens is not None else self.max_tokens

        response = self._openai.chat.completions.create(
            model=_model,
            messages=messages,          # type: ignore[arg-type]
            temperature=_temperature,
            max_tokens=_max_tokens,
            **extra_kwargs,
        )

        # Record usage (safe: usage may be None on some providers)
        usage = response.usage
        prompt_tokens = usage.prompt_tokens if usage else 0
        completion_tokens = usage.completion_tokens if usage else 0

        self.tracker.record_call(
            model=_model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )

        content = ""
        if response.choices:
            content = response.choices[0].message.content or ""

        return {
            "content": content,
            "model": response.model or _model,
            "usage": {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
            },
        }

    def complete(self, prompt: str, **kwargs: Any) -> str:
        """
        Convenience wrapper: send a single user message, return the
        assistant's text content as a plain string.

        Args:
            prompt:    The user message text.
            **kwargs:  Forwarded to chat().

        Returns:
            Assistant response text.
        """
        response = self.chat(
            messages=[{"role": "user", "content": prompt}],
            **kwargs,
        )
        return response["content"]


# ------------------------------------------------------------------
# Mock client for local testing without a real API key
# ------------------------------------------------------------------

class MockNearAIClient(SandboxedNearAIClient):
    """
    Drop-in replacement for SandboxedNearAIClient that returns canned
    responses. Used in tests and local dev when NEAR_AI_API_KEY is absent.

    Pass mock_responses as a list of strings; they are returned in order
    (cycling back to the start when exhausted).
    """

    def __init__(
        self,
        tracker: TokenTracker,
        mock_responses: Optional[List[str]] = None,
        model: str = "mock-model",
        **kwargs: Any,
    ) -> None:
        # Skip parent __init__ so we don't need a real key
        self.model = model
        self.temperature = kwargs.get("temperature", DEFAULT_TEMPERATURE)
        self.max_tokens = kwargs.get("max_tokens", DEFAULT_MAX_TOKENS)
        self.tracker = tracker
        self._mock_responses = mock_responses or [
            "This is a mock LLM response. Set NEAR_AI_API_KEY for real inference."
        ]
        self._response_index = 0
        self._openai = None  # type: ignore[assignment]

    def chat(
        self,
        messages: List[Dict[str, str]],
        *,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **extra_kwargs: Any,
    ) -> Dict[str, Any]:
        _model = model or self.model
        content = self._mock_responses[
            self._response_index % len(self._mock_responses)
        ]
        self._response_index += 1

        # Simulate minimal token counts
        prompt_tokens = sum(len(m.get("content", "").split()) for m in messages)
        completion_tokens = len(content.split())

        self.tracker.record_call(
            model=_model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )

        return {
            "content": content,
            "model": _model,
            "usage": {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
            },
        }

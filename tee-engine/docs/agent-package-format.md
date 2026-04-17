# Agent Package Format

This document defines the upload format for a user-submitted agent package in
TEE Engine.

## Overview

An agent package is a directory, or a `.zip` archive of that directory, with
the following structure:

```text
my-agent-package/
├── harness.py
├── agent.md
├── config.json
└── rag/
    └── documents/
        ├── doc1.txt
        └── doc2.md
```

## Required Files

### `harness.py`

Required. This is the executable agent entrypoint.

The runtime injects these globals into `harness.py`:

- `llm`: OpenAI-compatible Near AI client
- `challenge_input`: challenge payload dict
- `agent_prompt`: contents of `agent.md`
- `submission_config`: parsed `config.json`
- `rag_docs`: dict of `{filename: text}` loaded from `rag/documents/`

At the end of execution, `harness.py` must set:

```python
result = {
    "output": "...",
    "score": 0.0
}
```

`score` is a legacy/self-score field for compatibility.
When the challenge payload includes evaluation criteria (for example
`evaluationCriteria` with `key` and numeric `weight`), the platform runner may
recompute the final score from criterion-level scores and override this value.

Recommended per-criterion score payload:

```python
result = {
    "output": "...",
    "score": 0.0,  # optional legacy value
    "criterion_scores": {
        "accuracy": 92,      # 0~100 or 0.0~1.0
        "completeness": 0.88
    }
}
```

### `agent.md`

Required. Shared system prompt or base instructions for the agent workflow.

For multi-agent packages, this should contain the common rules shared by all
roles. Role-specific behavior can be added inside `harness.py`.

### `config.json`

Required. Runtime configuration for model routing and generation defaults.

### `rag/documents/`

Optional. Plain-text source files made available to the harness through
`rag_docs`.

## `config.json` Schema

The current engine officially reads these top-level keys:

```json
{
  "model": "openai/gpt-oss-120b",
  "temperature": 0.3,
  "max_tokens": 1024,
  "role_models": {
    "planner": "openai/gpt-5.2",
    "researcher": "deepseek-ai/DeepSeek-V3.1",
    "writer": "Qwen/Qwen3.5-122B-A10B",
    "reviewer": "openai/gpt-oss-120b",
    "reviser": "openai/gpt-oss-120b"
  }
}
```

### Supported Keys

- `model`: default fallback model used when a role-specific override is absent
- `temperature`: default sampling temperature
- `max_tokens`: default max completion tokens
- `role_models`: optional per-role model map for multi-agent workflows

Unknown keys are preserved in `submission_config.extra`, so future package
versions may include additional metadata.

## Role Model Routing

For a multi-agent harness, `role_models` is the recommended package format.

Suggested standard role names:

- `planner`
- `researcher`
- `writer`
- `reviewer`
- `reviser`
- `supervisor`

You may define additional roles if your `harness.py` uses them. When a role is
missing from `role_models`, the runtime should fall back to `model`.

## Allowed Model IDs

As of April 15, 2026, the following model IDs are listed on NEAR AI's official
Available Models page:

- `anthropic/claude-opus-4-6`
- `anthropic/claude-sonnet-4-5`
- `black-forest-labs/FLUX.2-klein-4B`
- `deepseek-ai/DeepSeek-V3.1`
- `google/gemini-3-pro`
- `openai/gpt-5.2`
- `openai/gpt-oss-120b`
- `Qwen/Qwen3-30B-A3B-Instruct-2507`
- `Qwen/Qwen3.5-122B-A10B`
- `zai-org/GLM-5-FP8`

Source:
[NEAR AI Available Models](https://docs.near.ai/cloud/models/)

## Minimal Single-Model Example

```json
{
  "model": "openai/gpt-oss-120b",
  "temperature": 0.2,
  "max_tokens": 512
}
```

## Multi-Agent Multi-Model Example

```json
{
  "model": "openai/gpt-oss-120b",
  "temperature": 0.3,
  "max_tokens": 1024,
  "role_models": {
    "planner": "openai/gpt-5.2",
    "researcher": "deepseek-ai/DeepSeek-V3.1",
    "writer": "Qwen/Qwen3.5-122B-A10B",
    "reviewer": "openai/gpt-oss-120b",
    "reviser": "openai/gpt-oss-120b"
  }
}
```

## Packaging Rules

- The uploaded archive should expand into a single top-level package directory.
- File names are case-sensitive.
- `harness.py`, `agent.md`, and `config.json` must exist at the package root.
- RAG files should be text-readable by Python `read_text()`.
- `harness.py` must be synchronous because the current sandbox is synchronous.
- The package should not assume access to local files outside the package.

## Validation Checklist

- `harness.py` exists
- `agent.md` exists
- `config.json` exists
- `config.json.model` is a valid NEAR AI model ID
- every `role_models.*` entry is a valid NEAR AI model ID
- `harness.py` sets `result`
- `result.output` exists
- `result.score` exists

## Recommended Submission Flow

1. Build the package directory locally.
2. Test it with `python3 run_sample.py`, `python3 run_cosmetics_agent.py`, or `run_submission(...)`.
3. Zip the package root directory.
4. Upload the archive to the platform.

## Example Package

A complete example package that follows this format is available at:
[samples/cosmetic1](/Users/jade/projects/buidl/buidlhack/tee-engine/samples/cosmetic1)

A higher-fidelity variant using the same assets and `brand_brief.txt` is also
available at:
[samples/cosmetic2](/Users/jade/projects/buidl/buidlhack/tee-engine/samples/cosmetic2)

A cinematic, motion-heavy variant with a different model mix is available at:
[samples/cosmetic3](/Users/jade/projects/buidl/buidlhack/tee-engine/samples/cosmetic3)

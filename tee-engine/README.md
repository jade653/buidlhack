# TEE Engine — Python Runtime Module

Executes user-submitted AI agents inside a sandboxed Python environment.
Part of the Agent Challenge Platform (Phala Cloud TEE layer).

---

## Directory layout

```
tee-engine/
├── engine/
│   ├── __init__.py     Public API re-exports
│   ├── models.py       SubmissionConfig, ExecutionResult dataclasses
│   ├── tracker.py      TokenTracker — per-call token counts + wall time
│   ├── client.py       SandboxedNearAIClient (OpenAI-compatible Near AI wrapper)
│   ├── sandbox.py      RestrictedPython sandbox: compile + exec with guards
│   └── runner.py       run_submission() — ties everything together
├── samples/
│   ├── cosmetics_challenge_input.json     Example cosmetics challenge payload
│   ├── cosmetic1/                         Baseline cosmetics landing package
│   ├── cosmetic2/                         Higher-fidelity cosmetics landing package
│   └── cosmetic3/                         Cinematic motion-heavy cosmetics package
├── docs/
│   └── agent-package-format.md     User upload package specification
├── run_sample.py       Local mock test runner
├── run_cosmetics_agent.py   Real Near AI runner for cosmetic1
├── run_cosmetic2_agent.py   Real Near AI runner for cosmetic2
├── run_cosmetic3_agent.py   Real Near AI runner for cosmetic3
└── requirements.txt
```

---

## What each file does

| File | Responsibility |
|------|---------------|
| `models.py` | Plain dataclasses. No side effects, no imports beyond stdlib. |
| `tracker.py` | Accumulates `(model, prompt_tokens, completion_tokens)` per LLM call. Also measures wall-clock time via `time.monotonic()`. |
| `client.py` | Wraps the OpenAI SDK pointed at `https://inference.near.ai/v1`. Hides the API key from user code. Calls `tracker.record_call()` after each response. `MockNearAIClient` is a drop-in for local testing. |
| `sandbox.py` | Compiles user source with `compile_restricted()` (RestrictedPython). Builds a controlled `globals` dict: restricted builtins, allowlist `__import__`, injected runtime objects. |
| `runner.py` | Loads submission files, creates tracker + client, compiles + executes harness.py in a timed daemon thread, extracts `result`, returns `ExecutionResult`. |

---

## Harness contract

For the end-user upload format, see
[docs/agent-package-format.md](/Users/jade/projects/buidl/buidlhack/tee-engine/docs/agent-package-format.md).
For the baseline cosmetics package, see
[samples/cosmetic1](/Users/jade/projects/buidl/buidlhack/tee-engine/samples/cosmetic1).
For a higher-fidelity version using the same assets and brief, see
[samples/cosmetic2](/Users/jade/projects/buidl/buidlhack/tee-engine/samples/cosmetic2).
For a cinematic, motion-heavy version using a different model mix, see
[samples/cosmetic3](/Users/jade/projects/buidl/buidlhack/tee-engine/samples/cosmetic3).

Every submission must contain `harness.py` and `agent.md`.

`harness.py` receives these injected globals at runtime:

| Name | Type | Description |
|------|------|-------------|
| `llm` | `SandboxedNearAIClient` | LLM client (API key hidden) |
| `challenge_input` | `dict` | Challenge payload from the platform |
| `agent_prompt` | `str` | Contents of `agent.md` |
| `submission_config` | `SubmissionConfig` | Parsed `config.json` (or defaults) |
| `rag_docs` | `dict[str, str]` | `{filename: text}` from `rag/documents/` |

Unknown keys from `config.json` are preserved in `submission_config.extra`, so
submission packages can carry extra metadata such as per-role model routing for
multi-agent workflows.

`harness.py` must produce a `result` dict before it exits:

```python
result = {
    "output": <any>,    # required
    "score":  <float>,  # required (legacy/self-score; platform may override)
}
```

If `challenge_input` contains `evaluationCriteria` (or `evaluation_criteria`),
the runner computes the final score from challenge weights and criterion scores,
ignoring this top-level harness `score`.

Expected criterion score fields (any one of these dicts):
- `result["criterion_scores"]`
- `result["criteria_scores"]`
- `result["evaluation"]`
- `result["scores"]`
- `result["output"][...]` with the same keys when output is a dict

Each criterion score can be either:
- normalized `0.0~1.0`, or
- percentage `0~100`

Final `ExecutionResult.score` is returned as `0~100`.

Two valid patterns:

```python
# Pattern A — script style (simplest)
answer = llm.complete("...")
result = {"output": answer, "score": 0.9}

# Pattern B — function style
def run():
    answer = llm.complete("...")
    return {"output": answer, "score": 0.9}
```

### LLM client interface

```python
# Full chat (returns dict)
response = llm.chat([
    {"role": "system", "content": agent_prompt},
    {"role": "user",   "content": "..."},
])
text = response["content"]

# One-shot convenience (returns string)
text = llm.complete("What is 2+2?")

# Override per-call params
response = llm.chat(messages, model="near:qwen3", temperature=0.0)
```

---

## How to run locally

### 1. Install dependencies

```bash
cd tee-engine
pip install -r requirements.txt
```

`requirements.txt` includes a Python-version-specific `RestrictedPython` pin,
so the setup works on both pre-3.14 environments and Python 3.14+.

### 2. Run the package locally with mock responses

```bash
python run_sample.py
```

This runs the baseline `cosmetic1` package with mocked copywriting responses and
returns a complete single-file storefront HTML string with three embedded
product illustrations.

### 3. Run against real Near AI Cloud

```bash
python run_cosmetics_agent.py
python run_cosmetic2_agent.py
python run_cosmetic3_agent.py
```

For local development, a `.env` file containing `NEAR_AI_API_KEY=...` is also
loaded automatically. In production, the service should inject
`NEAR_AI_API_KEY` as a real environment variable or secret.

### 4. Use the API programmatically

```python
import json
from engine import run_submission

result = run_submission(
    submission_dir="samples/cosmetic1",
    challenge_input=json.load(open("samples/cosmetics_challenge_input.json")),
)

print(result.status)          # "success" | "error" | "timeout"
print(result.score)           # final score (challenge-weighted 0~100 if criteria exist)
print(result.output)          # harness output value
print(result.wall_time_sec)   # execution time
print(result.token_usage)     # per-call token breakdown
```

---

## Security model

The sandbox uses `RestrictedPython` to:
- Compile user code with AST-level guards (`_getattr_`, `_write_`, `_print_`)
- Replace `__import__` with an allowlist-based importer
- Remove dangerous builtins (`open`, `eval`, `exec`, `compile`, `globals`)
- Block explicit dangerous modules: `os`, `subprocess`, `socket`, `sys`, `ctypes`, etc.

**This is a soft sandbox.** It prevents naive misuse but is not a full OS-level
isolation boundary. The Phala TEE container runtime provides the real security:
seccomp syscall filtering, read-only mounts, network policy, and cgroup limits.

See `sandbox.py` for the full list of blocked/allowed modules and all
`TODO (production)` hardening notes.

---

## Execution flow

```
run_submission(dir, challenge_input)
  │
  ├─ load harness.py, agent.md, config.json, rag/documents/
  ├─ compile harness.py  →  compile_restricted()
  ├─ create TokenTracker + SandboxedNearAIClient
  ├─ build_sandbox_globals(injected={llm, challenge_input, ...})
  ├─ tracker.start()
  ├─ execute_in_sandbox()  ←  runs in daemon thread with timeout
  │    exec(compiled_code, sandbox_globals)
  │    harness calls llm.chat()  →  tracker.record_call()
  │    harness sets result = {...}
  ├─ extract result["output"], result["score"] (legacy)
  ├─ if challenge criteria exist, compute weighted final score (0~100)
  └─ return ExecutionResult(status, output, score, wall_time_sec, token_usage)
```

---

## Extending

**Real vector RAG**: replace `_load_rag_docs()` in `runner.py` with a
chunked embedding pipeline. Inject a retriever object instead of the raw
`rag_docs` dict so harnesses can do semantic search.

**LangGraph / CrewAI harnesses**: these frameworks work out of the box —
they're on the module allowlist. The example
`samples/cosmetic1/harness.py` shows one practical pattern:
use small role-based LLM calls for copy, then assemble the final HTML
deterministically in Python so the storefront stays stable.

The example also shows role-based model routing via `submission_config.extra`:

```json
{
  "model": "openai/gpt-oss-120b",
  "role_models": {
    "copywriter": "openai/gpt-5.2",
    "reviewer": "openai/gpt-oss-120b"
  }
}
```

As of April 15, 2026, these model IDs are listed on NEAR AI's official
Available Models page:
[docs.near.ai/cloud/models](https://docs.near.ai/cloud/models/).

Async harnesses are not currently supported (the sandbox is synchronous).

**Streaming**: `SandboxedNearAIClient.chat()` uses non-streaming completions.
Add a `stream=True` path and a streaming-aware `TokenTracker.record_stream()`
for production.

**Subprocess isolation**: the current timeout uses a daemon thread (Python
can't hard-kill threads). Replace with `subprocess` or `multiprocessing` for
true timeout enforcement.

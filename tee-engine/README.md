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
│   ├── challenge_input.json        Example challenge payload
│   └── submission/
│       ├── harness.py              Example agent (single-turn QA)
│       ├── agent.md                System prompt for the agent
│       ├── config.json             Model + generation config
│       └── rag/documents/          Optional RAG source files
├── run_sample.py       Local test runner (no API key needed)
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

Every submission must contain `harness.py` and `agent.md`.

`harness.py` receives these injected globals at runtime:

| Name | Type | Description |
|------|------|-------------|
| `llm` | `SandboxedNearAIClient` | LLM client (API key hidden) |
| `challenge_input` | `dict` | Challenge payload from the platform |
| `agent_prompt` | `str` | Contents of `agent.md` |
| `submission_config` | `SubmissionConfig` | Parsed `config.json` (or defaults) |
| `rag_docs` | `dict[str, str]` | `{filename: text}` from `rag/documents/` |

`harness.py` must produce a `result` dict before it exits:

```python
result = {
    "output": <any>,    # required
    "score":  <float>,  # required — 0.0 to 1.0 typical
}
```

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

### 2. Run the sample (no API key needed)

```bash
python run_sample.py
```

The sample uses `MockNearAIClient` when `NEAR_AI_API_KEY` is not set.

### 3. Run against real Near AI Cloud

```bash
export NEAR_AI_API_KEY="your-key-here"
python run_sample.py
```

### 4. Use the API programmatically

```python
import json
from engine import run_submission

result = run_submission(
    submission_dir="samples/submission",
    challenge_input=json.load(open("samples/challenge_input.json")),
)

print(result.status)          # "success" | "error" | "timeout"
print(result.score)           # float from harness
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
  ├─ extract result["output"], result["score"]
  └─ return ExecutionResult(status, output, score, wall_time_sec, token_usage)
```

---

## Extending

**Real vector RAG**: replace `_load_rag_docs()` in `runner.py` with a
chunked embedding pipeline. Inject a retriever object instead of the raw
`rag_docs` dict so harnesses can do semantic search.

**LangGraph / CrewAI harnesses**: these frameworks work out of the box —
they're on the module allowlist. The harness can import and use them freely.
Async harnesses are not currently supported (the sandbox is synchronous).

**Streaming**: `SandboxedNearAIClient.chat()` uses non-streaming completions.
Add a `stream=True` path and a streaming-aware `TokenTracker.record_stream()`
for production.

**Subprocess isolation**: the current timeout uses a daemon thread (Python
can't hard-kill threads). Replace with `subprocess` or `multiprocessing` for
true timeout enforcement.

# Agent Package Format

This document is the **complete specification** for building a submission package.
You do not need access to the engine source to build a valid, high-scoring package.

---

## Package Structure

```text
my-agent/
├── harness.py          ← required: main executable
├── agent.md            ← required: system prompt / base instructions
├── config.json         ← required: model routing and generation defaults
└── rag/
    └── documents/      ← optional: .txt and .md files injected as rag_docs
        ├── brief.txt
        └── guide.md
```

Upload as a `.zip` of this directory, or submit the directory path directly.

---

## Required Files

### `harness.py`

The executable entrypoint. Runs inside a **RestrictedPython sandbox** (see constraints below).

At runtime the engine injects these globals — they are available directly, no import needed:

| Name                | Type             | Description                                                                                                           |
| ------------------- | ---------------- | --------------------------------------------------------------------------------------------------------------------- |
| `llm`               | client           | LLM client. Use `llm.chat()` or `llm.complete()`                                                                      |
| `challenge_input`   | `dict`           | The actual challenge data. Structure is defined by the provided `challenge_input.json` — refer to that file directly. |
| `agent_prompt`      | `str`            | Contents of your `agent.md`                                                                                           |
| `submission_config` | object           | Parsed `config.json`. Fields: `.model`, `.temperature`, `.max_tokens`, `.extra`                                       |
| `rag_docs`          | `dict[str, str]` | `{filename: text}` from `rag/documents/`                                                                              |

`harness.py` must set a module-level `result` before it exits:

```python
result = {
    "output": <any>,    # required — your deliverable (HTML string, dict, etc.)
}
```

Two valid patterns:

```python
# Pattern A — script style
answer = llm.complete("...")
result = {"output": answer}

# Pattern B — function style
def run():
    answer = llm.complete("...")
    return {"output": answer}
# (runner calls run() automatically if result is not set)
```

### `agent.md`

System prompt or base instructions injected as `agent_prompt`. Keep it focused —
it is prepended to every LLM call that uses it. Role-specific prompts can be
added inline in `harness.py`.

### `config.json`

```json
{
  "model": "openai/gpt-oss-120b",
  "temperature": 0.3,
  "max_tokens": 1024,
  "role_models": {
    "copywriter": "anthropic/claude-sonnet-4-5",
    "reviewer": "openai/gpt-oss-120b"
  }
}
```

Recognised top-level keys: `model`, `temperature`, `max_tokens`.
Everything else (including `role_models`) is passed through as-is and accessible
in `harness.py` via `submission_config.extra`:

```python
role_models  = submission_config.extra.get("role_models", {})
copy_model   = role_models.get("copywriter", submission_config.model)
review_model = role_models.get("reviewer",   submission_config.model)
```

---

## LLM Client Interface

```python
# Full chat — returns dict
response = llm.chat(
    [
        {"role": "system", "content": agent_prompt},
        {"role": "user",   "content": "..."},
    ],
    model="anthropic/claude-sonnet-4-5",   # optional override
    temperature=0.4,                        # optional override
    max_tokens=600,                         # optional override
)
text = response["content"]   # str

# One-shot convenience — returns str
text = llm.complete("What is the capital of France?")
```

Token usage is tracked automatically per call.

---

## Sandbox Constraints

`harness.py` runs inside a **RestrictedPython** sandbox. Read this section carefully
before writing your harness.

### Blocked builtins

These are **not available** — calling them raises `NameError` or `ImportError`:

```
open  eval  exec  compile  globals  locals  __import__ (replaced by allowlist)
```

**Consequence: you cannot read files at runtime.**
Assets (SVGs, images, templates) must be either:

- Hardcoded as string literals in `harness.py`, or
- Placed in `rag/documents/` as `.txt` or `.md` files and read via `rag_docs`.

Note: only `.txt` and `.md` files in `rag/documents/` are loaded. `.svg`, `.html`,
`.json`, etc. are ignored. To include SVG content via RAG, save it as `.txt`.

### Available builtins

All standard Python builtins are available except those listed above:

```
abs  all  any  bin  bool  bytes  callable  chr  dict  dir  divmod
enumerate  filter  float  format  frozenset  hasattr  hash  hex  int
isinstance  issubclass  iter  len  list  map  max  min  next  object
oct  ord  pow  print  range  repr  reversed  round  set  setattr  slice
sorted  str  sum  super  tuple  type  vars  zip
Exception  ValueError  TypeError  KeyError  IndexError  AttributeError
StopIteration  RuntimeError  NotImplementedError
```

### Allowed modules

These can be imported normally with `import`:

**Standard library**

```
json  re  math  time  datetime  collections  itertools  functools  operator
random  string  textwrap  typing  types  copy  dataclasses  enum  io  uuid
hashlib  hmac  base64  struct  decimal  fractions  statistics  heapq  bisect
array  queue  abc  contextlib  weakref  traceback  warnings  logging  pprint
pathlib  urllib  http  html  xml  csv  ast  inspect  asyncio  concurrent
threading
```

**HTTP / networking**

```
httpx  requests  aiohttp  urllib3  certifi
```

**AI / ML frameworks**

```
openai  anthropic  langgraph  crewai  langchain  langchain_core
langchain_community  langchain_openai  langsmith
```

**Data / utilities**

```
numpy  pandas  scipy  pydantic  pydantic_core  typing_extensions
attr  attrs  tenacity  tiktoken  tqdm  packaging  networkx
orjson  ujson  yaml  toml
```

### Blocked modules

These raise `ImportError` unconditionally:

```
os  subprocess  socket  sys  shutil  signal  ctypes  cffi
pickle  marshal  shelve  importlib  zipimport  runpy
multiprocessing  pty  tty  fcntl  mmap
```

### Python patterns to be aware of

All standard Python syntax works including classes, closures, generators,
comprehensions, and try/except.

String concatenation and f-strings both work. When embedding CSS or JavaScript
that contains `{` and `}` inside an f-string, use `{{` and `}}` to escape
literal braces, or build the string with concatenation:

```python
# f-string: CSS braces must be doubled
styles = f"body {{ background: {bg_color}; }}"

# Concatenation: no escaping needed
styles = "body { background: " + bg_color + "; }"

# Best practice for large CSS blocks: define as plain string, use CSS custom props
css_vars = ":root { --bg: " + bg_color + "; }"
css_body  = "body { background: var(--bg); }"   # plain string, no escaping
styles    = css_vars + css_body
```

---

## Working with Assets (SVGs, images)

Because `open` is blocked, you cannot load files at runtime. For visual assets:

**Option A — Inline SVG string in harness.py**

```python
ICON = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
    '<circle cx="50" cy="50" r="40" fill="#3B2314"/>'
    '</svg>'
)
html = "<div>" + ICON + "</div>"
```

**Option B — SVG via RAG documents**
Save the SVG markup as `rag/documents/logo.txt`. Access it in harness:

```python
logo_svg = rag_docs.get("logo.txt", "")
html = "<div>" + logo_svg + "</div>"
```

**Option C — External `<img>` reference**

```html
<img src="assets/logo.svg" alt="logo" />
```

Works only if the HTML output will be served with the `assets/` folder adjacent.

---

## RAG Documents

All `.txt` and `.md` files in `rag/documents/` are loaded and injected as a flat
dict before execution:

```python
# In harness.py — rag_docs is already available, no import needed
brief = rag_docs.get("brand_brief.txt", "")
guide = rag_docs.get("style_guide.md",  "")
```

Use RAG docs to supply brand briefs, style guides, product data, or any
text the LLM should reference without consuming prompt tokens up front.

---

## Allowed Model IDs

As of April 2026 the following model IDs are available on Near AI Cloud:

```
anthropic/claude-opus-4-6
anthropic/claude-sonnet-4-5
black-forest-labs/FLUX.2-klein-4B
deepseek-ai/DeepSeek-V3.1
google/gemini-3-pro
openai/gpt-5.2
openai/gpt-oss-120b
Qwen/Qwen3-30B-A3B-Instruct-2507
Qwen/Qwen3.5-122B-A10B
zai-org/GLM-5-FP8
```

Use the exact string as the `model` value. An unrecognised model ID will cause
the LLM call to fail.

---

## Execution Environment

| Property        | Value                                     |
| --------------- | ----------------------------------------- |
| Language        | Python 3                                  |
| Sandbox         | RestrictedPython (soft sandbox)           |
| Execution style | synchronous (no `async def` at top level) |
| Timeout         | 300 seconds wall clock                    |
| File system     | read-only; `open` blocked                 |
| Network         | LLM calls via injected `llm` client only  |

The harness runs as a **script** (not a module). Do not use relative imports.

---

## Minimal Example

```python
# harness.py — single LLM call, returns plain text

summary = llm.chat(
    [
        {"role": "system", "content": agent_prompt},
        {"role": "user",   "content": str(challenge_input)},
    ],
    max_tokens=512,
)["content"]

result = {"output": summary}
```

---

## Multi-Agent Example

```python
# harness.py — two roles, model routing via config.json
import re

role_models  = submission_config.extra.get("role_models", {})
write_model  = role_models.get("writer",   submission_config.model)
review_model = role_models.get("reviewer", submission_config.model)

draft = llm.chat(
    [{"role": "system", "content": agent_prompt},
     {"role": "user",   "content": "Write: " + str(challenge_input)}],
    model=write_model, max_tokens=800,
)["content"]

revised = llm.chat(
    [{"role": "system", "content": "You are an editor. Improve the following text."},
     {"role": "user",   "content": draft}],
    model=review_model, max_tokens=800,
)["content"]

result = {"output": revised}
```

---

## Validation Checklist

- [ ] `harness.py` exists at package root
- [ ] `agent.md` exists at package root
- [ ] `config.json` exists at package root
- [ ] `config.json` → `model` is a valid Near AI model ID
- [ ] every `role_models.*` entry is a valid Near AI model ID
- [ ] `harness.py` sets `result` (or defines `run()`)
- [ ] `result["output"]` is set
- [ ] No use of `open`, `os`, `subprocess`, `sys`
- [ ] No `async def` at module top level
- [ ] Assets are inlined or stored in `rag/documents/` as `.txt`/`.md`

You are given a spec, a challenge input, and visual assets. Your job is to build a complete agent package that, when executed by the engine, produces a single-file HTML landing page for the brand described in the challenge input.

---

## SPEC: Agent Package Format

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

| Name | Type | Description |
|------|------|-------------|
| `llm` | client | LLM client. Use `llm.chat()` or `llm.complete()` |
| `challenge_input` | `dict` | The actual challenge data. Structure is defined by the provided `challenge_input.json` — refer to that file directly. |
| `agent_prompt` | `str` | Contents of your `agent.md` |
| `submission_config` | object | Parsed `config.json`. Fields: `.model`, `.temperature`, `.max_tokens`, `.extra` |
| `rag_docs` | `dict[str, str]` | `{filename: text}` from `rag/documents/` |

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
    "reviewer":   "openai/gpt-oss-120b"
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
<img src="assets/logo.svg" alt="logo">
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

| Property | Value |
|----------|-------|
| Language | Python 3 |
| Sandbox | RestrictedPython (soft sandbox) |
| Execution style | synchronous (no `async def` at top level) |
| Timeout | 300 seconds wall clock |
| File system | read-only; `open` blocked |
| Network | LLM calls via injected `llm` client only |

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

---

## CHALLENGE INPUT (challenge.json)

```json
{
  "task_brief": "# 사이트 제작 의뢰서\n\n> 이 문서는 사이트 제작을 의뢰하는 분이 직접 작성하는 브리핑 파일입니다.\n> 각 항목을 최대한 구체적으로 채워주시면 AI 에이전트가 더 정확한 결과물을 생성합니다.\n\n---\n\n## 브랜드 정보\n\n**브랜드명:** Grain & Ground  \n**슬로건:** Every cup has a story.  \n**업종:** 스페셜티 커피 카페  \n**운영 형태:** 오프라인 매장 1곳 + 온라인 원두 판매  \n**매장 위치:** 서울시 성동구 성수동 (골목 안 독립 매장)  \n**설립 연도:** 2021  \n\n**브랜드 소개:**  \n성수동 골목 안에 자리한 스페셜티 커피 카페입니다. \"좋은 커피는 산지에서 시작된다\"는 철학 아래, 직접 생두를 소싱하고 소량 로스팅합니다. 산지별 원두의 개성을 살린 핸드드립과 에스프레소 베이스 음료를 제공하며, 커피를 통해 생산자와 소비자를 연결하는 경험을 지향합니다.\n\n---\n\n## 타겟 고객층\n\n**주요 타겟:** 25–40세 직장인 및 카페 투어 마니아  \n**특징:** 커피 품질과 브랜드 철학을 중시하며, SNS 공유 빈도가 높음. 원두 구매 경험이 있거나 홈카페에 관심 있는 층.\n\n---\n\n## 메뉴 라인업\n\n**대표 메뉴:**\n- 시그니처 핸드드립 (에티오피아 예가체프) — 7,500원\n- 콜드브루 토닉 — 8,000원\n- 카페 라떼 (자체 블렌드) — 6,500원\n- 시즌 음료 (분기별 변경) — 8,500원 내외\n\n**원두 / 굿즈 판매:**\n- 자체 로스팅 원두 (100g / 200g) — 12,000원 ~ 18,000원\n- 드립백 세트 (5개입) — 15,000원\n- 브랜드 텀블러 (단색, 두 가지 사이즈) — 32,000원\n\n---\n\n## 디자인 방향\n\n**키워드:** 미니멀, 따뜻함, 정직함, 장인정신  \n\n**색상 팔레트:**\n- 메인: 오프화이트 (#F5F0EB), 딥 브라운 (#3B2314)\n- 포인트: 더스티 테라코타 (#C07A5A)\n\n**무드:**  \n커피 본연의 색감에서 영감을 받은 따뜻한 중성 톤. 지나치게 트렌디하지 않고 5년 뒤에도 촌스럽지 않을 타임리스한 느낌을 원합니다. 사진보다는 여백과 타이포그래피가 살아있는 레이아웃을 선호합니다.\n\n**레퍼런스:**  \nBlue Bottle Coffee 웹사이트의 간결함과 구조감 — 단, 더 따뜻하고 덜 차갑게.\n\n---\n\n## 원하는 페이지 구성\n\n**페이지 형태:** 단일 스크롤 랜딩 페이지 (멀티 페이지 불필요)  \n\n**필수 섹션 (순서대로):**\n1. 히어로 — 브랜드명, 슬로건, 핵심 이미지 또는 배경\n2. 브랜드 스토리 — 짧은 소개 문단 (3–4줄 이내)\n3. 메뉴 소개 — 대표 메뉴 3–4개 카드형 나열\n4. 원두 & 굿즈 — 구매 유도 섹션 (외부 스토어 링크 연결)\n5. 매장 정보 — 주소, 영업시간, 오시는 길 (지도 링크)\n6. 푸터 — SNS 링크, 이메일 문의\n\n**선택 섹션:**\n- 인스타그램 피드 연동 (가능하면 포함)\n\n---\n\n## 특별 요청사항\n\n**언어:** 한국어 기본, 메뉴명과 섹션 제목에 영어 병기  \n**애니메이션:** 스크롤 시 요소 페이드인 정도. 과하지 않게.  \n**반응형:** 모바일 우선 (데스크탑도 지원)  \n\n**기타:**\n- 온라인 원두 주문은 외부 스마트스토어 링크 연결 (자체 결제 시스템 불필요)\n- 카페 내부 사진은 추후 제공 예정 — 우선 AI 생성 이미지 또는 플레이스홀더 사용 가능\n- 추후 온라인 예약 기능 추가 가능성 있으나 현재는 불필요\n"
}
```

---

## ASSETS

Three SVG illustrations are provided for the menu section. Embed them in your package (either inlined in `harness.py` or stored as `.txt` files in `rag/documents/`).

### cold-brew-tonic.svg
```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 240" fill="none">
  <!-- background -->
  <circle cx="120" cy="120" r="110" fill="#F5F0EB"/>

  <!-- glass shadow -->
  <ellipse cx="120" cy="202" rx="36" ry="5" fill="#3B2314" opacity="0.1"/>

  <!-- liquid fill (dark cold brew) -->
  <path d="M90 76 L85 196 Q120 203 155 196 L150 76 Z" fill="#1C0D06" opacity="0.88"/>

  <!-- tonic fizz layer at top -->
  <path d="M90 76 L91 98 Q120 103 149 98 L150 76 Z" fill="#C07A5A" opacity="0.28"/>

  <!-- ice cube 1 -->
  <rect x="93" y="118" width="24" height="24" rx="4" fill="#D6CFC8" opacity="0.55" transform="rotate(-8 105 130)"/>
  <!-- ice cube 2 -->
  <rect x="120" y="108" width="21" height="21" rx="4" fill="#D6CFC8" opacity="0.45" transform="rotate(7 130 118)"/>
  <!-- ice cube 3 -->
  <rect x="100" y="150" width="19" height="19" rx="4" fill="#D6CFC8" opacity="0.38" transform="rotate(-4 109 159)"/>

  <!-- glass outline -->
  <path d="M86 58 L82 196 Q120 205 158 196 L154 58 Z" stroke="#C07A5A" stroke-width="3" stroke-linejoin="round"/>

  <!-- glass rim -->
  <ellipse cx="120" cy="60" rx="34" ry="7" fill="#F5F0EB" stroke="#C07A5A" stroke-width="2.5"/>

  <!-- straw -->
  <rect x="136" y="36" width="6" height="96" rx="3" fill="#C07A5A" opacity="0.85" transform="rotate(4 139 84)"/>

  <!-- condensation -->
  <circle cx="76" cy="132" r="2" fill="#C07A5A" opacity="0.22"/>
  <circle cx="74" cy="152" r="1.5" fill="#C07A5A" opacity="0.18"/>
  <circle cx="166" cy="124" r="2" fill="#C07A5A" opacity="0.22"/>
  <circle cx="164" cy="148" r="1.5" fill="#C07A5A" opacity="0.18"/>
</svg>
```

### espresso-cup.svg
```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 240" fill="none">
  <!-- background -->
  <circle cx="120" cy="120" r="110" fill="#F5F0EB"/>

  <!-- steam -->
  <path d="M100 96 C96 86 101 76 97 66" stroke="#C07A5A" stroke-width="2.5" stroke-linecap="round" opacity="0.55"/>
  <path d="M120 90 C116 78 121 66 117 54" stroke="#C07A5A" stroke-width="2.5" stroke-linecap="round" opacity="0.55"/>
  <path d="M140 96 C136 86 141 76 137 66" stroke="#C07A5A" stroke-width="2.5" stroke-linecap="round" opacity="0.55"/>

  <!-- saucer -->
  <ellipse cx="120" cy="176" rx="56" ry="9" fill="#C07A5A"/>
  <ellipse cx="120" cy="172" rx="46" ry="7" fill="#A0623E"/>

  <!-- cup body -->
  <path d="M88 118 L94 166 Q120 174 146 166 L152 118 Z" fill="#3B2314"/>

  <!-- cup rim -->
  <ellipse cx="120" cy="118" rx="32" ry="8" fill="#C07A5A"/>

  <!-- coffee surface -->
  <ellipse cx="120" cy="118" rx="26" ry="6" fill="#1C0D06"/>
  <ellipse cx="120" cy="118" rx="22" ry="4.5" fill="none" stroke="#8B5E3C" stroke-width="2" opacity="0.5"/>

  <!-- handle -->
  <path d="M152 130 C174 126 174 162 152 158" stroke="#C07A5A" stroke-width="7" stroke-linecap="round"/>
</svg>
```

### signature-latte.svg
```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 240" fill="none">
  <!-- background -->
  <circle cx="120" cy="120" r="110" fill="#F5F0EB"/>

  <!-- saucer shadow -->
  <ellipse cx="120" cy="192" rx="64" ry="8" fill="#3B2314" opacity="0.1"/>

  <!-- saucer -->
  <ellipse cx="120" cy="188" rx="62" ry="9" fill="#C07A5A"/>
  <ellipse cx="120" cy="184" rx="52" ry="7" fill="#A0623E"/>

  <!-- cup body (wide latte style) -->
  <path d="M74 134 L80 178 Q120 188 160 178 L166 134 Z" fill="#3B2314"/>

  <!-- cup rim -->
  <ellipse cx="120" cy="134" rx="46" ry="10" fill="#C07A5A"/>

  <!-- milk foam surface -->
  <ellipse cx="120" cy="134" rx="40" ry="8.5" fill="#F0E6D8"/>

  <!-- latte art: simple tulip/leaf -->
  <ellipse cx="120" cy="134" rx="14" ry="5" fill="#C07A5A" opacity="0.45"/>
  <ellipse cx="120" cy="128" rx="9" ry="4" fill="#C07A5A" opacity="0.35"/>
  <ellipse cx="120" cy="123" rx="6" ry="3" fill="#C07A5A" opacity="0.28"/>
  <!-- center line -->
  <path d="M120 140 Q120 126 120 118" stroke="#C07A5A" stroke-width="1.5" stroke-linecap="round" opacity="0.4"/>

  <!-- handle -->
  <path d="M166 148 C188 144 190 176 166 172" stroke="#C07A5A" stroke-width="7" stroke-linecap="round"/>

  <!-- steam (subtle, latte is not as hot) -->
  <path d="M108 118 C105 110 109 102 106 94" stroke="#C07A5A" stroke-width="2" stroke-linecap="round" opacity="0.38"/>
  <path d="M132 118 C129 110 133 102 130 94" stroke="#C07A5A" stroke-width="2" stroke-linecap="round" opacity="0.38"/>
</svg>
```

---

## YOUR TASK

Build a complete agent package with the following files. Output each file's full content clearly labeled.

### Requirements

1. **`harness.py`** — orchestrates one or more LLM calls to produce a complete, self-contained HTML landing page. The HTML must be returned as `result = {"output": html_string}`.

2. **`agent.md`** — system prompt for the LLM(s). Should guide the model to produce high-quality, on-brand HTML.

3. **`config.json`** — model routing config. Use valid model IDs from the allowed list. You may use multiple role models (writer, reviewer, etc.) if it improves output quality.

4. **`rag/documents/`** — optional. If you store SVGs or brand content here as `.txt` files, list them.

### Constraints (from the spec)

- `open`, `os`, `sys`, `subprocess` are **blocked** — do not use them in `harness.py`
- No `async def` at module top level
- SVGs must be embedded as strings (either inlined in `harness.py` or in `rag/documents/*.txt`)
- Use `{{` `}}` to escape CSS/JS braces inside f-strings, or use string concatenation
- `challenge_input["task_brief"]` contains the full brand brief in Korean

### Output format

For each file, output a header and the full file content in a fenced code block:

```
## harness.py
\`\`\`python
...
\`\`\`

## agent.md
\`\`\`markdown
...
\`\`\`

## config.json
\`\`\`json
...
\`\`\`

## rag/documents/cold-brew-tonic.txt  (if used)
\`\`\`
...
\`\`\`
```

Produce working, complete files. Do not truncate or use placeholders.

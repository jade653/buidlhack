"""
Submission runner — the main entry point for executing a user agent.

Public API:
    result = run_submission(submission_dir, challenge_input)

The runner:
  1. Loads harness.py, agent.md, config.json (optional), and RAG docs (optional).
  2. Creates a TokenTracker and SandboxedNearAIClient.
  3. Compiles harness.py with RestrictedPython.
  4. Executes harness.py in the sandbox with a timeout.
  5. Extracts the `result` dict from the sandbox namespace.
  6. Returns a structured ExecutionResult.

EXECUTION CONVENTION
====================
harness.py is run as a script (not a function call). After execution,
the runner reads the `result` variable from the sandbox's global namespace:

    # At the bottom of harness.py:
    result = {
        "output": <any value>,   # required
        "score":  <float>,       # required (0.0 – 1.0 typical)
    }

If harness.py defines a `run()` function but doesn't set `result` directly,
the runner will call `run()` automatically and use its return value.
This gives users two equally valid patterns:

    # Pattern A — script style (simplest)
    answer = llm.complete("...")
    result = {"output": answer, "score": 1.0}

    # Pattern B — function style
    def run():
        answer = llm.complete("...")
        return {"output": answer, "score": 1.0}

TIMEOUT
=======
Default is 300 seconds. Execution runs in a daemon thread; the main thread
raises TimeoutError if the deadline is exceeded. The daemon thread is
abandoned (not killed — Python doesn't support thread termination).

TODO (production): run harness in a subprocess so it can be hard-killed.

RAG DOCS
========
If submission_dir/rag/documents/ exists, all *.txt and *.md files are
loaded and injected as rag_docs: Dict[str, str] (filename → text).

TODO (production): replace with a proper vector retrieval pipeline.
"""

from __future__ import annotations

import hashlib
import json
import os
import threading
import traceback
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional

from .client import MockNearAIClient, SandboxedNearAIClient
from .models import ExecutionResult, SubmissionConfig
from .sandbox import (
    SandboxError,
    build_sandbox_globals,
    compile_user_code,
    execute_in_sandbox,
)
from .tracker import TokenTracker

DEFAULT_TIMEOUT_SEC = 300
DEFAULT_AGENT_URL = "http://localhost:3000"


# ---------------------------------------------------------------------------
# On-chain submission helpers
# ---------------------------------------------------------------------------

def _post_json(url: str, payload: dict, secret: str) -> dict:
    """HTTP POST with JSON body. Uses stdlib only (no requests dependency)."""
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        url,
        data=data,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "x-internal-secret": secret,
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        body = exc.read().decode(errors="replace")
        raise RuntimeError(f"HTTP {exc.code} from {url}: {body}") from exc


def submit_to_chain(
    result: "ExecutionResult",
    *,
    challenge_id: str,
    user: str,
    agent_url: str = DEFAULT_AGENT_URL,
    internal_secret: str = "",
    lock_output: bool = True,
) -> Dict[str, Any]:
    """
    After a successful run, record the score (and optionally lock the output)
    on-chain via the TypeScript Shade Agent's HTTP API.

    Args:
        result:          ExecutionResult returned by run_submission().
        challenge_id:    NEAR contract challenge ID (e.g. "hack-001").
        user:            NEAR account ID of the participant.
        agent_url:       Base URL of the TypeScript agent (default localhost:3000).
        internal_secret: Value of INTERNAL_SECRET env var shared with the agent.
        lock_output:     If True, also call /api/lock-output with a SHA-256 hash
                         of the serialised output.

    Returns:
        Dict with "submit_score" and (optionally) "lock_output" response bodies.

    Raises:
        ValueError:   If result.status != "success" or score is None.
        RuntimeError: On HTTP error from the TypeScript agent.
    """
    if result.status != "success":
        raise ValueError(
            f"Cannot submit non-successful result to chain (status={result.status!r})"
        )
    if result.score is None:
        raise ValueError("result.score is None — cannot submit to chain")

    responses: Dict[str, Any] = {}

    # -- submit_score --------------------------------------------------------
    score_resp = _post_json(
        f"{agent_url.rstrip('/')}/api/submit-score",
        {"challenge_id": challenge_id, "user": user, "score": result.score},
        internal_secret,
    )
    responses["submit_score"] = score_resp

    # -- lock_output ---------------------------------------------------------
    if lock_output:
        # SHA-256 of the JSON-serialised output — proves content existed at
        # submission time.  (Real TEE setup would encrypt with a derived key
        # and store only the hash here; plaintext stays in the platform DB.)
        output_bytes = json.dumps(result.output, default=str, sort_keys=True).encode()
        encrypted_hash = hashlib.sha256(output_bytes).hexdigest()

        output_resp = _post_json(
            f"{agent_url.rstrip('/')}/api/lock-output",
            {
                "challenge_id": challenge_id,
                "user": user,
                "encrypted_hash": encrypted_hash,
            },
            internal_secret,
        )
        responses["lock_output"] = output_resp

    return responses


# ---------------------------------------------------------------------------
# File loading helpers
# ---------------------------------------------------------------------------

def _load_harness(submission_dir: Path) -> str:
    harness_path = submission_dir / "harness.py"
    if not harness_path.exists():
        raise FileNotFoundError(
            f"harness.py not found in {submission_dir}. "
            "Every submission must contain harness.py."
        )
    return harness_path.read_text(encoding="utf-8")


def _load_agent_prompt(submission_dir: Path) -> str:
    agent_md = submission_dir / "agent.md"
    if not agent_md.exists():
        raise FileNotFoundError(
            f"agent.md not found in {submission_dir}. "
            "Every submission must contain agent.md."
        )
    return agent_md.read_text(encoding="utf-8")


def _load_config(submission_dir: Path) -> SubmissionConfig:
    config_path = submission_dir / "config.json"
    if not config_path.exists():
        return SubmissionConfig.default()
    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
        return SubmissionConfig.from_dict(data)
    except (json.JSONDecodeError, ValueError) as exc:
        raise ValueError(f"config.json is invalid: {exc}") from exc


def _load_rag_docs(submission_dir: Path) -> Dict[str, str]:
    """
    Load all .txt and .md files from rag/documents/ as a flat dict.

    Returns {} if the directory doesn't exist.

    TODO (production): replace with chunked embedding + vector store.
    The dict here is intentionally simple so harness.py can iterate it
    or concatenate docs into a context string easily.
    """
    rag_dir = submission_dir / "rag" / "documents"
    if not rag_dir.is_dir():
        return {}

    docs: Dict[str, str] = {}
    for ext in ("*.txt", "*.md"):
        for path in sorted(rag_dir.glob(ext)):
            try:
                docs[path.name] = path.read_text(encoding="utf-8")
            except OSError:
                pass  # skip unreadable files silently

    return docs


# ---------------------------------------------------------------------------
# Timeout execution
# ---------------------------------------------------------------------------

def _run_in_thread(
    fn,
    args: tuple,
    timeout_sec: float,
) -> Any:
    """
    Run fn(*args) in a daemon thread with a hard wall-clock timeout.

    Raises:
        TimeoutError: if execution exceeds timeout_sec.
        Any exception raised by fn is re-raised in the calling thread.
    """
    result_holder: List[Any] = [None]
    error_holder:  List[Optional[BaseException]] = [None]
    done_event = threading.Event()

    def _target():
        try:
            result_holder[0] = fn(*args)
        except BaseException as exc:  # noqa: BLE001
            error_holder[0] = exc
        finally:
            done_event.set()

    thread = threading.Thread(target=_target, daemon=True)
    thread.start()

    finished = done_event.wait(timeout=timeout_sec)

    if not finished:
        raise TimeoutError(
            f"Submission exceeded the {timeout_sec}s execution time limit."
        )

    if error_holder[0] is not None:
        raise error_holder[0]

    return result_holder[0]


# ---------------------------------------------------------------------------
# Result extraction
# ---------------------------------------------------------------------------

def _extract_result(
    sandbox_globals: Dict[str, Any],
) -> tuple[Any, Optional[float], Dict[str, Any]]:
    """
    Extract output and score from the sandbox namespace after exec.

    Supports two harness patterns:
      - Pattern A: harness sets module-level `result = {"output": ..., "score": ...}`
      - Pattern B: harness defines `def run(): return {"output": ..., "score": ...}`

    Returns (output, score, raw_result_dict).
    Score may be None if the harness didn't provide one.
    """
    result_val = sandbox_globals.get("result")

    # Pattern B: call run() if no result and run is defined
    if result_val is None:
        run_fn = sandbox_globals.get("run")
        if callable(run_fn):
            result_val = run_fn()

    if result_val is None:
        raise ValueError(
            "harness.py did not set a `result` variable and did not define a "
            "`run()` function. Set `result = {'output': ..., 'score': ...}` "
            "at the end of your harness."
        )

    if not isinstance(result_val, dict):
        raise TypeError(
            f"harness.py `result` must be a dict, got {type(result_val).__name__}."
        )

    output = result_val.get("output")
    raw_score = result_val.get("score")

    score: Optional[float] = None
    if raw_score is not None:
        try:
            score = float(raw_score)
        except (TypeError, ValueError):
            score = None  # non-numeric score is treated as absent

    return output, score, result_val


def _normalize_criterion_score(raw_value: Any) -> Optional[float]:
    """
    Normalize a criterion score to 0~100.

    Accepted formats:
      - 0.0~1.0 float
      - 0~100 float/int
      - numeric strings
    """
    if raw_value is None:
        return None
    try:
        value = float(raw_value)
    except (TypeError, ValueError):
        return None

    # Interpret [0, 1] as normalized ratio.
    if 0.0 <= value <= 1.0:
        value *= 100.0

    # Clamp to a valid percentage range.
    return max(0.0, min(100.0, value))


def _collect_criterion_scores(
    result_payload: Dict[str, Any],
    output: Any,
) -> Dict[str, Any]:
    """
    Collect per-criterion scores from a few conventional field names.
    """
    score_maps: List[Dict[str, Any]] = []

    for key in ("criterion_scores", "criteria_scores", "evaluation", "scores"):
        candidate = result_payload.get(key)
        if isinstance(candidate, dict):
            score_maps.append(candidate)

    if isinstance(output, dict):
        for key in ("criterion_scores", "criteria_scores", "evaluation", "scores"):
            candidate = output.get(key)
            if isinstance(candidate, dict):
                score_maps.append(candidate)

    merged: Dict[str, Any] = {}
    for score_map in score_maps:
        for key, value in score_map.items():
            merged[str(key)] = value
    return merged


def _extract_evaluation_criteria(challenge_input: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Read challenge-level evaluation criteria.
    Supports both camelCase and snake_case keys.
    """
    raw_criteria = (
        challenge_input.get("evaluationCriteria")
        or challenge_input.get("evaluation_criteria")
        or challenge_input.get("criteria")
        or []
    )
    if not isinstance(raw_criteria, list):
        return []
    return [item for item in raw_criteria if isinstance(item, dict)]


def _compute_builtin_criterion_score(
    criterion_key: str,
    output: Any,
    wall_time_sec: float,
    token_usage: Dict[str, Any],
) -> Optional[float]:
    """
    Compute platform-side criterion scores when a submission doesn't provide one.
    """
    key = criterion_key.strip().lower()
    text = str(output or "")
    lowered = text.lower()

    if key in {"speed", "latency"}:
        # 10s => 100, 60s => 0 (linear clamp).
        return round(max(0.0, min(100.0, (60.0 - wall_time_sec) / 50.0 * 100.0)), 4)

    if key in {"efficiency", "token_efficiency", "cost_efficiency"}:
        total_tokens = token_usage.get("total_tokens", 0)
        try:
            tokens = float(total_tokens)
        except (TypeError, ValueError):
            tokens = 0.0
        # <=2k => high, >=20k => low.
        return round(max(0.0, min(100.0, (20000.0 - tokens) / 18000.0 * 100.0)), 4)

    if key in {"spec_compliance", "format", "format_compliance"}:
        checks = [
            "<!doctype html" in lowered,
            "<html" in lowered and "</html>" in lowered,
            "add to bag" in lowered,
            "data:image/svg+xml" in lowered,
            "__" not in text,  # unresolved template placeholders
        ]
        return round(sum(1 for item in checks if item) / len(checks) * 100.0, 4)

    if key in {"brand_consistency", "brand"}:
        # A simple platform-side proxy for now.
        return 100.0 if "brand" in lowered or "<title>" in lowered else 60.0

    if key in {"copy_quality", "writing_quality"}:
        length = len(text)
        if length < 1200:
            return 45.0
        if length < 2500:
            return 70.0
        if length < 4500:
            return 85.0
        return 92.0

    return None


def _compute_challenge_weighted_score(
    challenge_input: Dict[str, Any],
    result_payload: Dict[str, Any],
    output: Any,
    wall_time_sec: float,
    token_usage: Dict[str, Any],
) -> tuple[Optional[float], Dict[str, Any]]:
    """
    Compute weighted challenge score from criterion-level scores.

    The harness-provided top-level `score` is intentionally ignored here.
    """
    criteria = _extract_evaluation_criteria(challenge_input)
    if not criteria:
        return None, {"reason": "no_challenge_criteria"}

    criterion_scores = _collect_criterion_scores(result_payload, output)

    weighted_total = 0.0
    weight_sum = 0.0
    breakdown: List[Dict[str, Any]] = []

    for item in criteria:
        key = str(item.get("key", "")).strip()
        if not key:
            continue

        weight = item.get("weight")
        # Reference-only criteria are not part of numeric total.
        if not isinstance(weight, (int, float)):
            breakdown.append(
                {
                    "key": key,
                    "weight": weight,
                    "score": None,
                    "counted": False,
                    "reason": "non_numeric_weight",
                }
            )
            continue

        normalized_score = _normalize_criterion_score(criterion_scores.get(key))
        if normalized_score is None:
            builtin_score = _compute_builtin_criterion_score(
                criterion_key=key,
                output=output,
                wall_time_sec=wall_time_sec,
                token_usage=token_usage,
            )
            if builtin_score is None:
                normalized_score = 0.0
                reason = "missing_or_invalid_score"
            else:
                normalized_score = builtin_score
                reason = "platform_builtin"
        else:
            reason = "ok"

        weighted_total += normalized_score * float(weight)
        weight_sum += float(weight)
        breakdown.append(
            {
                "key": key,
                "weight": float(weight),
                "score": normalized_score,
                "counted": True,
                "reason": reason,
            }
        )

    if weight_sum <= 0:
        return None, {
            "reason": "no_numeric_weights",
            "criteria_breakdown": breakdown,
        }

    final_score = weighted_total / weight_sum
    final_score = round(max(0.0, min(100.0, final_score)), 4)

    return final_score, {
        "reason": "computed",
        "criteria_breakdown": breakdown,
        "weight_sum": weight_sum,
        "criterion_scores_source_keys": sorted(list(criterion_scores.keys())),
    }


def _get_printed_output(sandbox_globals: Dict[str, Any]) -> str:
    """
    Extract text captured by RestrictedPython's PrintCollector.

    RestrictedPython generates `_print = _print_(_getattr_)` at exec start,
    so after exec, sandbox_globals["_print"] is a PrintCollector instance.
    Calling it returns the collected text via PrintCollector.__call__().
    """
    printer = sandbox_globals.get("_print")
    if printer is None:
        return ""
    try:
        return printer()  # PrintCollector.__call__ returns ''.join(self.txt)
    except Exception:  # noqa: BLE001
        return ""


# ---------------------------------------------------------------------------
# Main public function
# ---------------------------------------------------------------------------

def run_submission(
    submission_dir: str | Path,
    challenge_input: Dict[str, Any],
    *,
    timeout_sec: float = DEFAULT_TIMEOUT_SEC,
    use_mock_client: bool = False,
    mock_responses: Optional[List[str]] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    # On-chain submission (optional). When challenge_id and user are provided,
    # a successful run automatically calls the TypeScript Shade Agent to
    # submit_score (and lock_output) on-chain.
    challenge_id: Optional[str] = None,
    user: Optional[str] = None,
    agent_url: str = DEFAULT_AGENT_URL,
    internal_secret: Optional[str] = None,
    lock_output_on_chain: bool = True,
) -> ExecutionResult:
    """
    Load and execute a user submission against a challenge input.

    Args:
        submission_dir:       Path to the submission directory containing
                              harness.py, agent.md, and optionally config.json
                              and rag/documents/.
        challenge_input:      Dict of challenge data injected as `challenge_input`
                              in harness.py.
        timeout_sec:          Max wall-clock seconds (default 300).
        use_mock_client:      If True, use MockNearAIClient (no real API needed).
                              Automatically set to True if NEAR_AI_API_KEY is unset.
        mock_responses:       List of response strings for MockNearAIClient.
        api_key:              Override NEAR_AI_API_KEY env var.
        base_url:             Override default Near AI Cloud base URL.
        challenge_id:         NEAR challenge ID. If set (with user), on-chain
                              submission is triggered automatically on success.
        user:                 NEAR account ID of the participant.
        agent_url:            TypeScript agent base URL (default localhost:3000).
        internal_secret:      Shared secret for the TypeScript agent. Falls back
                              to the INTERNAL_SECRET env var.
        lock_output_on_chain: Also call /api/lock-output after submit_score.

    Returns:
        ExecutionResult with status, output, score, wall_time_sec,
        token_usage, error, and metadata. On success with chain params set,
        metadata["chain"] contains the TypeScript agent response(s).
    """
    submission_dir = Path(submission_dir)

    # -- Step 1: Load submission files -----------------------------------
    try:
        harness_source = _load_harness(submission_dir)
        agent_prompt    = _load_agent_prompt(submission_dir)
        config          = _load_config(submission_dir)
        rag_docs        = _load_rag_docs(submission_dir)
    except (FileNotFoundError, ValueError) as exc:
        return ExecutionResult(
            status="error",
            error=str(exc),
            metadata={"phase": "load"},
        )

    # -- Step 2: Compile harness.py --------------------------------------
    try:
        compiled_code = compile_user_code(
            harness_source,
            filename=str(submission_dir / "harness.py"),
        )
    except SyntaxError as exc:
        return ExecutionResult(
            status="error",
            error=f"SyntaxError in harness.py: {exc}",
            metadata={"phase": "compile"},
        )

    # -- Step 3: Create runtime objects ----------------------------------
    tracker = TokenTracker()

    # Decide client type
    _use_mock = use_mock_client or (
        not (api_key or os.environ.get("NEAR_AI_API_KEY"))
    )

    if _use_mock:
        client: SandboxedNearAIClient = MockNearAIClient(
            tracker=tracker,
            mock_responses=mock_responses,
            model=config.model,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
        )
    else:
        kwargs: Dict[str, Any] = dict(
            tracker=tracker,
            model=config.model,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
        )
        if api_key:
            kwargs["api_key"] = api_key
        if base_url:
            kwargs["base_url"] = base_url
        client = SandboxedNearAIClient(**kwargs)

    # -- Step 4: Build sandbox globals -----------------------------------
    injected = {
        "llm":               client,
        "challenge_input":   challenge_input,
        "agent_prompt":      agent_prompt,
        "submission_config": config,
        "rag_docs":          rag_docs,
    }
    sandbox_globals = build_sandbox_globals(injected)

    # -- Step 5: Execute with timeout ------------------------------------
    tracker.start()

    try:
        final_globals = _run_in_thread(
            execute_in_sandbox,
            args=(compiled_code, sandbox_globals),
            timeout_sec=timeout_sec,
        )
    except TimeoutError as exc:
        return ExecutionResult(
            status="timeout",
            error=str(exc),
            wall_time_sec=tracker.elapsed(),
            token_usage=tracker.to_dict(),
            metadata={
                "phase": "execute",
                "printed_output": _get_printed_output(sandbox_globals),
            },
        )
    except SandboxError as exc:
        return ExecutionResult(
            status="error",
            error=str(exc),
            wall_time_sec=tracker.elapsed(),
            token_usage=tracker.to_dict(),
            metadata={
                "phase": "execute",
                "printed_output": _get_printed_output(sandbox_globals),
            },
        )
    except Exception as exc:  # noqa: BLE001
        return ExecutionResult(
            status="error",
            error=f"Unexpected runner error: {exc}\n{traceback.format_exc()}",
            wall_time_sec=tracker.elapsed(),
            token_usage=tracker.to_dict(),
            metadata={"phase": "execute"},
        )

    wall_time = tracker.elapsed()
    printed = _get_printed_output(final_globals)

    # -- Step 6: Extract result ------------------------------------------
    try:
        output, harness_score, result_payload = _extract_result(final_globals)
    except (ValueError, TypeError) as exc:
        return ExecutionResult(
            status="error",
            error=str(exc),
            wall_time_sec=wall_time,
            token_usage=tracker.to_dict(),
            metadata={
                "phase": "result_extraction",
                "printed_output": printed,
            },
        )

    challenge_score, evaluation_meta = _compute_challenge_weighted_score(
        challenge_input=challenge_input,
        result_payload=result_payload,
        output=output,
        wall_time_sec=wall_time,
        token_usage=tracker.to_dict(),
    )

    # Platform score priority:
    # 1) challenge weighted score (0~100)
    # 2) legacy harness score fallback (normalized to 0~100)
    final_score = challenge_score
    if final_score is None:
        final_score = _normalize_criterion_score(harness_score)

    exec_result = ExecutionResult(
        status="success",
        output=output,
        score=final_score,
        wall_time_sec=wall_time,
        token_usage=tracker.to_dict(),
        metadata={
            "printed_output": printed,
            "rag_docs_loaded": list(rag_docs.keys()),
            "mock_client": _use_mock,
            "evaluation": evaluation_meta,
            "harness_score_legacy": harness_score,
        },
    )

    # -- Step 7: Submit to chain (if challenge_id + user provided) -----------
    if challenge_id and user and final_score is not None:
        secret = internal_secret if internal_secret is not None else os.environ.get("INTERNAL_SECRET", "")
        try:
            chain_responses = submit_to_chain(
                exec_result,
                challenge_id=challenge_id,
                user=user,
                agent_url=agent_url,
                internal_secret=secret,
                lock_output=lock_output_on_chain,
            )
            exec_result.metadata["chain"] = chain_responses
        except Exception as exc:  # noqa: BLE001
            exec_result.metadata["chain_error"] = str(exc)

    return exec_result

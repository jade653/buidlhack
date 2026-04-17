"""
RestrictedPython-based sandbox for executing user harness.py files.

SECURITY MODEL (MVP):
  This is a *soft* sandbox. It prevents accidental or naive misuse of
  dangerous Python APIs (os, subprocess, socket, open). It does NOT
  provide OS-level process isolation — that comes from Phala TEE and
  the container runtime.

  For production hardening, combine this with:
    - seccomp / gVisor syscall filtering (Phala TEE provides this)
    - Network egress rules (TEE network policy)
    - Read-only filesystem mounts
    - Resource limits via cgroups
    - A stricter allowlist (deny-by-default instead of deny-known-bad)

HOW IT WORKS:
  1. User source is compiled with compile_restricted() from RestrictedPython.
     This transforms attribute access, writes, subscript access, iteration,
     and print calls into guarded function calls:
       - x.attr        → _getattr_(x, 'attr')
       - x[key]        → _getitem_(x, key)
       - for x in it:  → _getiter_(it)
       - x.attr = val  → _write_(x).attr = val
       - a, b = it     → _unpack_sequence_(it, ...)
       - print(x)      → _print._call_print(x)
       - x += y        → _inplacevar_('+=', x, y)

  2. We exec the compiled code with a controlled globals dict that:
     a) Supplies all required guard functions (listed above)
     b) Uses a custom __import__ (allowlist-based)
     c) Removes dangerous builtins (eval, exec, open, compile, ...)
     d) Injects runtime objects (llm, challenge_input, agent_prompt, ...)

  3. After exec, the caller reads the `result` variable the harness set,
     and `sandbox_globals['_print']()` for captured print output.

HARNESS CONTRACT:
  The user's harness.py must set a module-level `result` variable:
      result = {"output": <any>, "score": <float>}
  Missing `result` or wrong type is treated as an error by the runner.
"""

from __future__ import annotations

import builtins as _real_builtins
import traceback
from typing import Any, Dict, Set

from RestrictedPython import compile_restricted, safe_builtins
from RestrictedPython import PrintCollector
from RestrictedPython.Guards import (
    full_write_guard,
    guarded_unpack_sequence,
    safer_getattr,
)


# ---------------------------------------------------------------------------
# Module lists
# ---------------------------------------------------------------------------

# Hard block — always denied, regardless of allowlist position.
BLOCKED_MODULES: Set[str] = {
    "os",
    "subprocess",
    "socket",
    "sys",
    "shutil",
    "signal",
    "ctypes",
    "cffi",
    "pickle",
    "marshal",
    "shelve",
    "importlib",
    "zipimport",
    "runpy",
    "py_compile",
    "compileall",
    "distutils",
    "pty",
    "tty",
    "termios",
    "fcntl",
    "grp",
    "pwd",
    "resource",
    "syslog",
    "mmap",
    "multiprocessing",  # TODO: enable once we have subprocess isolation
}

# Modules explicitly allowed.
# TODO (production): flip to deny-by-default and enumerate every dep.
# Current MVP strategy: block known-dangerous, allow the rest so that
# LangGraph / CrewAI and their deep transitive deps work without an
# exhaustive whitelist.
ALLOWED_MODULES: Set[str] = {
    # Standard library — safe
    "json",
    "math",
    "time",
    "datetime",
    "collections",
    "itertools",
    "functools",
    "operator",
    "random",
    "string",
    "textwrap",
    "typing",
    "types",
    "re",
    "copy",
    "dataclasses",
    "enum",
    "io",
    "uuid",
    "hashlib",
    "hmac",
    "base64",
    "struct",
    "decimal",
    "fractions",
    "statistics",
    "heapq",
    "bisect",
    "array",
    "queue",
    "abc",
    "contextlib",
    "weakref",
    "gc",
    "traceback",
    "warnings",
    "logging",
    "pprint",
    "reprlib",
    "pathlib",
    "urllib",
    "http",
    "email",
    "html",
    "xml",
    "csv",
    "configparser",
    "ast",
    "inspect",
    # Async — needed by LangGraph internals
    "asyncio",
    "concurrent",
    "threading",
    # HTTP clients — needed by OpenAI / LLM SDKs
    "httpx",
    "httpcore",
    "requests",
    "aiohttp",
    "certifi",
    "urllib3",
    "charset_normalizer",
    "idna",
    "anyio",
    "sniffio",
    # AI / ML frameworks
    "openai",
    "anthropic",
    "langgraph",
    "crewai",
    "langchain",
    "langchain_core",
    "langchain_community",
    "langchain_openai",
    "langsmith",
    # Data
    "numpy",
    "pandas",
    "scipy",
    # Pydantic
    "pydantic",
    "pydantic_core",
    "pydantic_settings",
    "annotated_types",
    "typing_extensions",
    # Other common deps
    "attr",
    "attrs",
    "tenacity",
    "tiktoken",
    "tokenizers",
    "tqdm",
    "packaging",
    "more_itertools",
    "toolz",
    "networkx",
    "orjson",
    "ujson",
    "yaml",
    "tomllib",
    "toml",
    "dotenv",
}


# ---------------------------------------------------------------------------
# Custom importer
# ---------------------------------------------------------------------------

def _make_restricted_importer(
    allowed: Set[str],
    blocked: Set[str],
):
    """
    Return a __import__ replacement that enforces the module policy.

    Priority:
      1. root module in blocked → deny (ImportError).
      2. root module in allowed → permit (real import).
      3. Otherwise             → permit for now (MVP fallthrough).

    TODO (production): rule 3 should be another ImportError to make the
    sandbox deny-by-default. The MVP fallthrough exists so that LangGraph /
    CrewAI and all their transitive sub-packages work without a complete dep
    enumeration.
    """
    real_import = _real_builtins.__import__

    def _restricted_import(
        name: str,
        glbls=None,
        locs=None,
        fromlist=(),
        level: int = 0,
    ):
        # Allow relative imports within the sandbox context.
        if level > 0:
            return real_import(name, glbls, locs, fromlist, level)

        root = name.split(".")[0]

        if root in blocked:
            raise ImportError(
                f"Import of '{name}' is blocked for security reasons. "
                f"Module '{root}' is not permitted in this sandbox."
            )

        if root in allowed:
            return real_import(name, glbls, locs, fromlist, level)

        # TODO (production): raise ImportError here.
        return real_import(name, glbls, locs, fromlist, level)

    return _restricted_import


# ---------------------------------------------------------------------------
# Guard functions
# ---------------------------------------------------------------------------

def _getitem_(obj: Any, key: Any) -> Any:
    """
    Guard for subscript reads: x[key] → _getitem_(x, key).
    MVP: no restriction, passes through to normal indexing.
    TODO (production): add checks for protected dict keys.
    """
    return obj[key]


def _inplace_op(op: str, x: Any, y: Any) -> Any:
    """
    Guard for augmented assignments: x += y → _inplacevar_('+=', x, y).
    """
    _ops = {
        "+=":  lambda a, b: a + b,
        "-=":  lambda a, b: a - b,
        "*=":  lambda a, b: a * b,
        "/=":  lambda a, b: a / b,
        "//=": lambda a, b: a // b,
        "%=":  lambda a, b: a % b,
        "**=": lambda a, b: a ** b,
        "&=":  lambda a, b: a & b,
        "|=":  lambda a, b: a | b,
        "^=":  lambda a, b: a ^ b,
        ">>=": lambda a, b: a >> b,
        "<<=": lambda a, b: a << b,
    }
    fn = _ops.get(op)
    if fn is None:
        raise NotImplementedError(f"Unsupported inplace op: {op!r}")
    return fn(x, y)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_sandbox_globals(
    injected: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Build the globals dict for exec()ing restricted user code.

    Args:
        injected: Runtime objects to expose in user code.
                  Expected keys: llm, challenge_input, agent_prompt,
                                 submission_config, rag_docs.

    Returns:
        A globals dict ready for exec(compiled_code, globals_dict).

    After exec():
        - result output:   globals_dict["result"]
        - printed text:    globals_dict["_print"]()   ← call the collector
    """
    # Build restricted builtins from RestrictedPython's safe base.
    # safe_builtins removes: open, eval, exec, compile, globals, locals, ...
    restricted_builtins: Dict[str, Any] = dict(safe_builtins)

    # Add our allowlist-based importer.
    restricted_builtins["__import__"] = _make_restricted_importer(
        allowed=ALLOWED_MODULES,
        blocked=BLOCKED_MODULES,
    )

    # __build_class__ is required for class definitions in user code.
    restricted_builtins["__build_class__"] = _real_builtins.__build_class__

    # Add commonly needed builtins that safe_builtins omits but are safe.
    restricted_builtins.update(
        {
            "all":      _real_builtins.all,
            "any":      _real_builtins.any,
            "bin":      _real_builtins.bin,
            "dict":     _real_builtins.dict,
            "dir":      _real_builtins.dir,
            "enumerate":_real_builtins.enumerate,
            "filter":   _real_builtins.filter,
            "format":   _real_builtins.format,
            "frozenset":_real_builtins.frozenset,
            "getattr":  _real_builtins.getattr,
            "hasattr":  _real_builtins.hasattr,
            "list":     _real_builtins.list,
            "map":      _real_builtins.map,
            "max":      _real_builtins.max,
            "min":      _real_builtins.min,
            "next":     _real_builtins.next,
            "object":   _real_builtins.object,
            "reversed": _real_builtins.reversed,
            "set":      _real_builtins.set,
            "setattr":  _real_builtins.setattr,  # guarded by _write_ at call site
            "sum":      _real_builtins.sum,
            "super":    _real_builtins.super,
            "type":     _real_builtins.type,
            "vars":     _real_builtins.vars,
            "zip":      _real_builtins.zip,
            # Exceptions
            "Exception":         _real_builtins.Exception,
            "ValueError":        _real_builtins.ValueError,
            "TypeError":         _real_builtins.TypeError,
            "KeyError":          _real_builtins.KeyError,
            "IndexError":        _real_builtins.IndexError,
            "AttributeError":    _real_builtins.AttributeError,
            "StopIteration":     _real_builtins.StopIteration,
            "RuntimeError":      _real_builtins.RuntimeError,
            "NotImplementedError":_real_builtins.NotImplementedError,
            "OverflowError":     _real_builtins.OverflowError,
            "ZeroDivisionError": _real_builtins.ZeroDivisionError,
            "ImportError":       _real_builtins.ImportError,
        }
    )

    glbls: Dict[str, Any] = {
        "__builtins__": restricted_builtins,

        # --- RestrictedPython guards (required by compiled code) ---

        # Attribute access:  x.attr → _getattr_(x, 'attr')
        "_getattr_": safer_getattr,

        # Subscript reads:   x[key] → _getitem_(x, key)
        "_getitem_": _getitem_,

        # Iteration:         for x in it → _getiter_(it)
        "_getiter_": iter,

        # Attribute writes:  x.attr = v → _write_(x).attr = v
        "_write_": full_write_guard,

        # Augmented assign:  x += y → _inplacevar_('+=', x, y)
        "_inplacevar_": _inplace_op,

        # Sequence unpack:   a, b = it → _unpack_sequence_(it, ...)
        "_unpack_sequence_": guarded_unpack_sequence,

        # Iter unpack:  for a, b in it → _iter_unpack_sequence_(it, ...)
        # Used by RestrictedPython in generator expressions and for-loop targets.
        "_iter_unpack_sequence_": guarded_unpack_sequence,

        # Print:             print(x) → _print._call_print(x)
        # RestrictedPython generates: _print = _print_(_getattr_) at exec start.
        # After exec, call sandbox_globals["_print"]() to get captured text.
        "_print_": PrintCollector,
    }

    # Inject runtime objects last so they cannot shadow guards.
    glbls.update(injected)

    return glbls


def compile_user_code(source: str, filename: str = "<harness>") -> Any:
    """
    Compile user source code with RestrictedPython's AST transformation.

    Raises:
        SyntaxError:  on invalid Python syntax or RestrictedPython violations.
    """
    code = compile_restricted(source, filename=filename, mode="exec")
    return code


class SandboxError(Exception):
    """Raised when restricted execution encounters a runtime error."""


def execute_in_sandbox(
    code: Any,
    sandbox_globals: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Execute compiled restricted code in the sandbox globals.

    Args:
        code:            Compiled code from compile_user_code().
        sandbox_globals: Globals dict from build_sandbox_globals().

    Returns:
        The sandbox_globals dict after execution. Caller reads:
          - sandbox_globals["result"]      → harness output dict
          - sandbox_globals["_print"]()    → captured print text

    Raises:
        SandboxError:  wraps any runtime exception from user code.
        ImportError:   propagated directly (policy message is helpful).
    """
    try:
        exec(code, sandbox_globals)  # noqa: S102
    except ImportError:
        raise  # Pass through with the policy message intact.
    except Exception as exc:
        tb = traceback.format_exc()
        raise SandboxError(
            f"User code raised {type(exc).__name__}: {exc}\n\n{tb}"
        ) from exc

    return sandbox_globals

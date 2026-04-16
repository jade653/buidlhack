"""
CLI entry point for the TEE engine.

Usage:
    python -m engine <package_dir> <challenge_input.json> [--out result.json]

Examples:
    python -m engine samples/codex samples/challenge_input.json
    python -m engine samples/codex samples/challenge_input.json --out result.json

Output (stdout, JSON):
    {
        "status":        "success" | "error" | "timeout",
        "output":        <any>,
        "wall_time_sec": <float>,
        "total_tokens":  <int>,
        "token_usage":   { ... },
        "error":         <str | null>
    }
"""

import argparse
import json
import sys
from pathlib import Path

from .runner import run_submission


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="python -m engine",
        description="Run an agent package against a challenge input.",
    )
    parser.add_argument("package",       help="Path to the agent package directory")
    parser.add_argument("challenge",     help="Path to challenge_input.json")
    parser.add_argument("--out", "-o",   help="Write JSON result to this file (optional)")
    parser.add_argument("--timeout",     type=float, default=300.0,
                        help="Execution timeout in seconds (default: 300)")
    args = parser.parse_args()

    challenge_path = Path(args.challenge)
    if not challenge_path.exists():
        print(f"Error: {challenge_path} not found.", file=sys.stderr)
        sys.exit(1)

    challenge_input = json.loads(challenge_path.read_text(encoding="utf-8"))

    result = run_submission(
        submission_dir=args.package,
        challenge_input=challenge_input,
        timeout_sec=args.timeout,
    )

    out = {
        "status":        result.status,
        "output":        result.output,
        "wall_time_sec": result.wall_time_sec,
        "total_tokens":  result.token_usage.get("total_tokens", 0),
        "token_usage":   result.token_usage,
        "error":         result.error,
    }

    json_str = json.dumps(out, ensure_ascii=False, indent=2)

    print(json_str)

    if args.out:
        Path(args.out).write_text(json_str, encoding="utf-8")
        print(f"\nSaved → {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()

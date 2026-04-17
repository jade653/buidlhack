#!/usr/bin/env python3
"""
Run the cosmetics storefront generation sample and save the generated HTML.

Usage:
    python run_cosmetics_agent.py

Use a real NEAR AI Cloud key:
    python run_cosmetics_agent.py
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from engine import run_submission

ROOT = Path(__file__).parent
SUBMISSION_DIR = ROOT / "samples" / "cosmetic1"
CHALLENGE_INPUT = ROOT / "samples" / "cosmetics_challenge_input.json"
OUTPUT_HTML = ROOT / "outputs" / "luma-dew-storefront.html"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=OUTPUT_HTML,
        help=f"Where to save the generated HTML (default: {OUTPUT_HTML})",
    )
    return parser.parse_args()

def normalize_html_output(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines:
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()
    return cleaned


def looks_like_complete_html(text: str) -> bool:
    lowered = text.lower()
    return (
        "<!doctype html" in lowered
        and "<html" in lowered
        and "</html>" in lowered
        and "<body" in lowered
        and "</body>" in lowered
    )


def main() -> int:
    args = parse_args()
    challenge_input = json.loads(CHALLENGE_INPUT.read_text(encoding="utf-8"))

    print("=" * 60)
    print("TEE Engine — Cosmetics Storefront Sample")
    print("=" * 60)
    print(f"Submission : {SUBMISSION_DIR}")
    print(f"Challenge   : {CHALLENGE_INPUT}")
    print(f"Output HTML : {args.output}")
    print()

    MAX_ATTEMPTS = 3
    output_html = ""
    result = None

    for attempt in range(1, MAX_ATTEMPTS + 1):
        if attempt > 1:
            print(f"\n[RETRY] Attempt {attempt}/{MAX_ATTEMPTS}...")

        result = run_submission(
            submission_dir=SUBMISSION_DIR,
            challenge_input=challenge_input,
            use_mock_client=False,
        )

        print("--- Execution Result ---")
        print(f"Status      : {result.status}")
        print(f"Score (/100): {result.score}")
        print(f"Wall time   : {result.wall_time_sec:.3f}s")
        print(f"Token usage : {result.token_usage}")

        if result.error:
            print(f"\n[ERROR]\n{result.error}")
            if attempt == MAX_ATTEMPTS:
                return 1
            continue

        output_html = normalize_html_output(str(result.output or ""))
        if not output_html:
            print("\n[WARN] No HTML returned by harness.")
            if attempt == MAX_ATTEMPTS:
                return 1
            continue

        if not looks_like_complete_html(output_html):
            print("\n[WARN] Incomplete HTML — retrying.")
            if attempt == MAX_ATTEMPTS:
                print("[ERROR] All attempts produced incomplete HTML. Nothing was saved.")
                return 1
            continue

        break  # success

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(output_html, encoding="utf-8")

    print(f"\nSaved HTML to: {args.output}")
    if result.metadata.get("printed_output"):
        print("\n--- Captured print output ---")
        print(result.metadata["printed_output"])

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

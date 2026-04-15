#!/usr/bin/env python3
"""
Run the UI-generation sample submission and save the generated HTML to disk.

Usage:
    python run_ui_agent.py

Use a real NEAR AI Cloud key:
    export NEAR_AI_API_KEY="your-key"
    python run_ui_agent.py --real
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from engine import run_submission

ROOT = Path(__file__).parent
SUBMISSION_DIR = ROOT / "samples" / "ui_submission"
CHALLENGE_INPUT = ROOT / "samples" / "ui_challenge_input.json"
OUTPUT_HTML = ROOT / "samples" / "generated" / "tee-engine-intro.html"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--real",
        action="store_true",
        help="Use the real NEAR AI Cloud client. Requires NEAR_AI_API_KEY.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=OUTPUT_HTML,
        help=f"Where to save the generated HTML (default: {OUTPUT_HTML})",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    challenge_input = json.loads(CHALLENGE_INPUT.read_text(encoding="utf-8"))

    print("=" * 60)
    print("TEE Engine — UI Generation Sample")
    print("=" * 60)
    print(f"Submission : {SUBMISSION_DIR}")
    print(f"Challenge   : {CHALLENGE_INPUT}")
    print(f"Output HTML : {args.output}")
    print()

    mock_html = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>TEE Engine</title>
  <style>
    :root { --bg: #f5efe6; --fg: #172033; --accent: #0f766e; --card: #fffdf8; }
    body { margin: 0; font-family: Georgia, serif; background: linear-gradient(180deg, #f5efe6, #dbeafe); color: var(--fg); }
    main { max-width: 960px; margin: 0 auto; padding: 48px 20px 72px; }
    .hero, .grid article { background: rgba(255,255,255,0.72); backdrop-filter: blur(10px); border-radius: 24px; padding: 24px; box-shadow: 0 18px 50px rgba(23,32,51,0.10); }
    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; margin-top: 20px; }
    h1, h2 { margin: 0 0 12px; }
    .pill { display: inline-block; padding: 6px 10px; border-radius: 999px; background: var(--accent); color: white; font-size: 14px; }
  </style>
</head>
<body>
  <main>
    <section class="hero">
      <span class="pill">Near AI Cloud + TEE</span>
      <h1>TEE Engine</h1>
      <p>Sandboxed runtime for user-submitted AI agents with structured execution results.</p>
    </section>
    <section class="grid">
      <article><h2>Overview</h2><p>Runs harness-based agent submissions in a restricted Python environment.</p></article>
      <article><h2>Architecture</h2><p>Runner, sandbox, client, and tracker modules keep execution isolated and observable.</p></article>
      <article><h2>Execution Flow</h2><p>Load submission, inject llm, execute sandboxed code, collect output and score.</p></article>
    </section>
  </main>
</body>
</html>
"""

    result = run_submission(
        submission_dir=SUBMISSION_DIR,
        challenge_input=challenge_input,
        use_mock_client=not args.real,
        mock_responses=None if args.real else [mock_html],
    )

    print("--- Execution Result ---")
    print(f"Status      : {result.status}")
    print(f"Score       : {result.score}")
    print(f"Wall time   : {result.wall_time_sec:.3f}s")
    print(f"Token usage : {result.token_usage}")

    if result.error:
        print(f"\n[ERROR]\n{result.error}")
        return 1

    output_html = str(result.output or "").strip()
    if not output_html:
        print("\n[ERROR]\nNo HTML was returned by the harness.")
        return 1

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(output_html, encoding="utf-8")

    print(f"\nSaved HTML to: {args.output}")
    if result.metadata.get("printed_output"):
        print("\n--- Captured print output ---")
        print(result.metadata["printed_output"])

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

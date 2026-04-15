#!/usr/bin/env python3
"""
Local test runner for the sample submission.

Run from tee-engine/:
    python run_sample.py

Uses MockNearAIClient by default so no API key is needed.
Set NEAR_AI_API_KEY to use the real Near AI Cloud endpoint.

Options:
    --real   Force the real client even if NEAR_AI_API_KEY is set in env.
"""

import json
import sys
from pathlib import Path

# Allow running from the tee-engine/ directory without installing the package.
sys.path.insert(0, str(Path(__file__).parent))

from engine import run_submission

SUBMISSION_DIR   = Path(__file__).parent / "samples" / "submission"
CHALLENGE_INPUT  = Path(__file__).parent / "samples" / "challenge_input.json"


def main():
    challenge_input = json.loads(CHALLENGE_INPUT.read_text())

    print("=" * 60)
    print("Agent Challenge Platform — Local Test Runner")
    print("=" * 60)
    print(f"Submission : {SUBMISSION_DIR}")
    print(f"Challenge  : {CHALLENGE_INPUT}")
    print()

    # MockNearAIClient returns a canned answer that intentionally contains
    # "Nightshade" and "proof-of-stake" so the score comes out > 0.
    mock_answers = [
        "NEAR Protocol uses Nightshade, a proof-of-stake consensus mechanism "
        "that enables dynamic sharding of the network."
    ]

    result = run_submission(
        submission_dir=SUBMISSION_DIR,
        challenge_input=challenge_input,
        mock_responses=mock_answers,
    )

    print("--- Execution Result ---")
    print(f"Status       : {result.status}")
    print(f"Score        : {result.score}")
    print(f"Wall time    : {result.wall_time_sec:.3f}s")
    print(f"Token usage  : {result.token_usage}")
    print()
    print(f"Output:\n{result.output}")
    print()

    if result.metadata.get("printed_output"):
        print("--- Captured print output ---")
        print(result.metadata["printed_output"])

    if result.error:
        print(f"\n[ERROR] {result.error}")
        sys.exit(1)

    rag = result.metadata.get("rag_docs_loaded", [])
    if rag:
        print(f"RAG docs loaded: {rag}")

    print("\nDone.")


if __name__ == "__main__":
    main()

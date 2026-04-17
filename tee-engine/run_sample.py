#!/usr/bin/env python3
"""
Local test runner for the cosmetics landing package.

Run from tee-engine/:
    python run_sample.py

Uses MockNearAIClient by default so no API key is needed.
"""

import json
import sys
from pathlib import Path

# Allow running from the tee-engine/ directory without installing the package.
sys.path.insert(0, str(Path(__file__).parent))

from engine import run_submission

SUBMISSION_DIR   = Path(__file__).parent / "samples" / "cosmetic1"
CHALLENGE_INPUT  = Path(__file__).parent / "samples" / "cosmetics_challenge_input.json"


def main():
    challenge_input = json.loads(CHALLENGE_INPUT.read_text())

    print("=" * 60)
    print("Agent Challenge Platform — Local Test Runner")
    print("=" * 60)
    print(f"Submission : {SUBMISSION_DIR}")
    print(f"Challenge  : {CHALLENGE_INPUT}")
    print()

    # The cosmetics package makes two short LLM calls for copywriting and review.
    mock_answers = [
        "badge: Soft ritual edit\ntitle: Clinical glow, softened into a beautiful daily ritual.\nbody: Three tactile essentials for cleansing, brightening, and sealing in comfort with a polished shelf presence.\ncta: Shop Luma Dew\nbenefit_title: Built for skin that wants radiance without overload.\nbenefit_body: A concise lineup of cruelty-free formulas designed to feel elegant from sink to vanity.",
        "badge: Soft ritual edit\ntitle: Clinical glow, softened into a beautiful daily ritual.\nbody: Three tactile essentials for cleansing, brightening, and sealing in comfort with a polished shelf presence.\ncta: Shop Luma Dew\nbenefit_title: Built for skin that wants radiance without overload.\nbenefit_body: A concise lineup of cruelty-free formulas designed to feel elegant from sink to vanity.",
    ]

    result = run_submission(
        submission_dir=SUBMISSION_DIR,
        challenge_input=challenge_input,
        use_mock_client=True,
        mock_responses=mock_answers,
    )

    print("--- Execution Result ---")
    print(f"Status       : {result.status}")
    print(f"Score (/100) : {result.score}")
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

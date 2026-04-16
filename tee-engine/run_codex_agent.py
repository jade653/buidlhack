#!/usr/bin/env python3
"""
Runner for the codex cafe landing page package.

Mock (no API key needed):
    python3 run_codex_agent.py

Real Near AI Cloud:
    NEAR_AI_API_KEY=<key> python3 run_codex_agent.py

Parse task.md first if challenge_input.json is missing:
    python3 parse_task.py && python3 run_codex_agent.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from engine import run_submission

SUBMISSION_DIR   = Path(__file__).parent / "samples" / "codex"
CHALLENGE_INPUT  = Path(__file__).parent / "samples" / "challenge_input.json"


def main():
    if not CHALLENGE_INPUT.exists():
        print(f"challenge_input.json not found. Run: python3 parse_task.py")
        sys.exit(1)

    challenge_input = json.loads(CHALLENGE_INPUT.read_text())

    print("=" * 60)
    print("Codex — Cafe Landing Page Agent")
    print("=" * 60)
    print(f"Package   : {SUBMISSION_DIR}")
    print(f"Brand     : {challenge_input.get('brand', {}).get('name', '?')}")
    print()

    # Mock responses matching the harness's expected key: value format.
    # Used automatically when NEAR_AI_API_KEY is unset.
    mock_responses = [
        (
            "BRAND_NAME: Grain & Ground\n"
            "HERO_BADGE: Specialty · Craft · Seoul\n"
            "HERO_TITLE: 산지에서 시작되는, 한 잔의 이야기\n"
            "STORY_BODY: 성수동 골목 안, 정직한 커피 한 잔을 위해 문을 열었습니다. "
            "직접 소싱한 생두를 소량 로스팅해 산지 본연의 맛을 그대로 전합니다.\n"
            "CTA: 메뉴 보러 가기\n"
            "MENU_TITLE: 시그니처 드링크\n"
            "SHOP_TEASER: 집에서도 즐기는 Grain & Ground — 직접 로스팅한 원두를 온라인으로 만나보세요."
        ),
    ]

    result = run_submission(
        submission_dir=SUBMISSION_DIR,
        challenge_input=challenge_input,
        mock_responses=mock_responses,
    )

    print(f"Status    : {result.status}")
    print(f"Score     : {result.score}")
    print(f"Wall time : {result.wall_time_sec:.2f}s")
    print(f"Tokens    : {result.token_usage}")

    if result.error:
        print(f"\n[ERROR] {result.error}")
        sys.exit(1)

    if result.output:
        out_path = Path(__file__).parent / "outputs" / "codex-cafe.html"
        out_path.parent.mkdir(exist_ok=True)
        out_path.write_text(result.output, encoding="utf-8")
        print(f"\nHTML saved: {out_path}")

    rag = result.metadata.get("rag_docs_loaded", [])
    if rag:
        print(f"RAG docs  : {rag}")

    mock = result.metadata.get("mock_client", False)
    if mock:
        print("\n[mock client — set NEAR_AI_API_KEY to use real API]")


if __name__ == "__main__":
    main()

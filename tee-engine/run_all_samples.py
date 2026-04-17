#!/usr/bin/env python3
"""
Run claude-package, codex-package, and gemini-package against the shared
challenge.json and write each output HTML to outputs/.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from engine import run_submission

BASE      = Path(__file__).parent
CHALLENGE = BASE / "samples" / "challenge.json"
OUT_DIR   = BASE / "outputs"
OUT_DIR.mkdir(exist_ok=True)

PACKAGES = [
    ("claude-package", BASE / "samples" / "claude-agent"),
    ("codex-package",  BASE / "samples" / "codex-agent"),
]


def main():
    challenge_input = json.loads(CHALLENGE.read_text())

    for name, pkg_dir in PACKAGES:
        print(f"\n{'='*60}")
        print(f"Running {name} ...")
        print(f"{'='*60}")

        result = run_submission(
            submission_dir=pkg_dir,
            challenge_input=challenge_input,
        )

        print(f"Status     : {result.status}")
        print(f"Wall time  : {result.wall_time_sec:.1f}s")
        print(f"Tokens     : {result.token_usage}")

        if result.error:
            print(f"[ERROR] {result.error}")

        if result.output:
            out_path = OUT_DIR / f"{name}.html"
            out_path.write_text(str(result.output), encoding="utf-8")
            print(f"Output     : {out_path} ({len(str(result.output))} chars)")
        else:
            print("Output     : (none)")

    print("\nDone.")


if __name__ == "__main__":
    main()

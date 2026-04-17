#!/usr/bin/env python3
"""
End-to-end test: Python engine executes harness.py → Shade Agent submits score on-chain.

Prerequisites
-------------
1. TypeScript agent is running:
       cd tee-engine/agent && npm start

2. A challenge exists on-chain.  If not, create one first:
       near call contract.sehun.testnet create_challenge \
         '{"challenge_id":"e2e-test","deadline_ms":9999999999000}' \
         --accountId sehun.testnet --deposit 1

3. INTERNAL_SECRET in tee-engine/agent/.env matches INTERNAL_SECRET below
   (or is empty / unset in both places).

Usage
-----
    cd tee-engine
    python test_e2e_chain.py

    # override defaults:
    CHALLENGE_ID=e2e-test USER_ID=alice.testnet python test_e2e_chain.py
"""

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from engine import run_submission

# ── Config ────────────────────────────────────────────────────────────────────

CHALLENGE_ID     = os.environ.get("CHALLENGE_ID", "e2e-test")
USER_ID          = os.environ.get("USER_ID", "alice.testnet")
AGENT_URL        = os.environ.get("AGENT_URL", "http://localhost:3000")
INTERNAL_SECRET  = os.environ.get("INTERNAL_SECRET", "buidlhack-secret-123")

SUBMISSION_DIR   = Path(__file__).parent / "samples" / "cosmetic1"
CHALLENGE_INPUT  = Path(__file__).parent / "samples" / "cosmetics_challenge_input.json"

# ── Mock LLM answers (avoids needing a real API key) ─────────────────────────

MOCK_ANSWERS = [
    "badge: Soft ritual edit\ntitle: Clinical glow, softened into a beautiful daily ritual.\nbody: Three tactile essentials.\ncta: Shop Luma Dew\nbenefit_title: Built for radiance.\nbenefit_body: A concise lineup of cruelty-free formulas.",
    "badge: Soft ritual edit\ntitle: Clinical glow, softened into a beautiful daily ritual.\nbody: Three tactile essentials.\ncta: Shop Luma Dew\nbenefit_title: Built for radiance.\nbenefit_body: A concise lineup of cruelty-free formulas.",
]


def main():
    challenge_input = json.loads(CHALLENGE_INPUT.read_text())

    print("=" * 60)
    print("E2E test: engine → Shade Agent → NEAR contract")
    print("=" * 60)
    print(f"  challenge_id : {CHALLENGE_ID}")
    print(f"  user         : {USER_ID}")
    print(f"  agent_url    : {AGENT_URL}")
    print(f"  submission   : {SUBMISSION_DIR.name}")
    print()

    result = run_submission(
        submission_dir=SUBMISSION_DIR,
        challenge_input=challenge_input,
        use_mock_client=True,
        mock_responses=MOCK_ANSWERS,
        # ── chain submission params ──
        challenge_id=CHALLENGE_ID,
        user=USER_ID,
        agent_url=AGENT_URL,
        internal_secret=INTERNAL_SECRET,
        lock_output_on_chain=True,
    )

    print(f"Status     : {result.status}")
    print(f"Score      : {result.score}")
    print(f"Wall time  : {result.wall_time_sec:.3f}s")
    print()

    if result.status != "success":
        print(f"[FAIL] Execution failed: {result.error}")
        sys.exit(1)

    chain = result.metadata.get("chain")
    chain_err = result.metadata.get("chain_error")

    if chain_err:
        print(f"[FAIL] Chain submission error: {chain_err}")
        print()
        print("Possible causes:")
        print("  - TypeScript agent not running (cd tee-engine/agent && npm start)")
        print("  - Challenge does not exist on-chain")
        print("  - INTERNAL_SECRET mismatch")
        sys.exit(1)

    print("Chain responses:")
    print(f"  submit_score : {chain.get('submit_score')}")
    print(f"  lock_output  : {chain.get('lock_output')}")
    print()
    print("[OK] Score submitted on-chain successfully.")
    print()
    print("Verify on-chain:")
    print(f"  near view contract.sehun.testnet get_score")
    print(f"    '{{\"challenge_id\":\"{CHALLENGE_ID}\",\"user\":\"{USER_ID}\"}}'")


if __name__ == "__main__":
    main()

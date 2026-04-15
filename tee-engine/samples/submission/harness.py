"""
Sample harness.py — Question-Answering Agent

Demonstrates the standard harness interface:
  - Injected globals: llm, challenge_input, agent_prompt, submission_config, rag_docs
  - Must set module-level `result = {"output": ..., "score": float}` at the end.

This harness does simple single-turn QA:
  1. Reads the context and question from challenge_input.
  2. Calls llm.chat() with the agent_prompt as the system message.
  3. Scores the answer by checking for expected keywords.
  4. Sets `result`.

For a multi-agent example with LangGraph, see samples/submission_langgraph/.
"""

# -----------------------------------------------------------------------
# Build the prompt
# -----------------------------------------------------------------------

context  = challenge_input["context"]
question = challenge_input["question"]

user_message = (
    "Context:\n"
    + context
    + "\n\n"
    + "Question: "
    + question
)

# -----------------------------------------------------------------------
# Call the LLM
# -----------------------------------------------------------------------

print("[harness] Sending request to LLM...")

response = llm.chat(
    messages=[
        {"role": "system", "content": agent_prompt},
        {"role": "user",   "content": user_message},
    ]
)

answer = response["content"].strip()
print("[harness] Answer:", answer)

# -----------------------------------------------------------------------
# Score: fraction of expected keywords found in the answer (case-insensitive)
# -----------------------------------------------------------------------

expected_keywords = challenge_input.get("expected_keywords", [])

if expected_keywords:
    answer_lower = answer.lower()
    hits = sum(1 for kw in expected_keywords if kw.lower() in answer_lower)
    score = hits / len(expected_keywords)
else:
    # No expected keywords provided; default to a moderate score.
    score = 0.5

print("[harness] Score:", score)

# -----------------------------------------------------------------------
# Required: set result dict
# -----------------------------------------------------------------------

result = {
    "output": answer,
    "score":  score,
}

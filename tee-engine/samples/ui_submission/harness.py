"""
Simple UI-generation harness for NEAR AI Cloud.

This sample asks the model to generate a single self-contained HTML landing page
that introduces the tee-engine project. The HTML is returned in `result["output"]`
so the local runner can save it to disk outside the sandbox.
"""

task = challenge_input["task"]
project_name = challenge_input["project_name"]
project_summary = challenge_input["project_summary"]
project_highlights = challenge_input.get("project_highlights", [])

highlight_lines = "\n".join(f"- {item}" for item in project_highlights)

user_message = f"""
Build a simple but polished landing page for this project.

Task:
{task}

Project name:
{project_name}

Project summary:
{project_summary}

Highlights:
{highlight_lines}

Requirements:
- Return exactly one complete HTML document.
- Inline CSS and minimal inline JavaScript only.
- Make it mobile-friendly.
- Include sections for overview, architecture, and execution flow.
- Mention that the project runs user-submitted AI agents in a sandbox.
- Mention Near AI Cloud and TEE-based privacy.
- Do not use external assets or external CDN dependencies.
- Use short, readable copy.
- Output HTML only.
""".strip()

print("[ui-harness] Requesting landing page HTML...")

response = llm.chat(
    messages=[
        {"role": "system", "content": agent_prompt},
        {"role": "user", "content": user_message},
    ]
)

html = response["content"].strip()

checks = [
    "<!DOCTYPE html" in html or "<!doctype html" in html,
    project_name.lower() in html.lower(),
    "Near AI Cloud".lower() in html.lower(),
    "sandbox".lower() in html.lower(),
]
score = sum(1 for passed in checks if passed) / len(checks)

result = {
    "output": html,
    "score": score,
}

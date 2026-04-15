"""
Cosmetics storefront UI-generation harness.

This harness asks the model to generate a complete single-file HTML storefront
for a cosmetics brand. The generated HTML is returned so the local runner can
save it outside the sandbox.
"""

brand = challenge_input["brand"]
tagline = challenge_input["tagline"]
audience = challenge_input["audience"]
theme = challenge_input["theme"]
products = challenge_input.get("products", [])
features = challenge_input.get("features", [])

product_lines = "\n".join(
    f"- {item['name']}: {item['description']} ({item['price']})"
    for item in products
)
feature_lines = "\n".join(f"- {item}" for item in features)

user_message = f"""
Create a cosmetics e-commerce landing page as a single self-contained HTML file.

Brand:
{brand}

Tagline:
{tagline}

Audience:
{audience}

Theme:
{theme}

Products:
{product_lines}

Features:
{feature_lines}

Requirements:
- Return exactly one complete HTML document.
- Inline CSS and minimal inline JavaScript only.
- No external images, fonts, CDNs, or dependencies.
- Make it polished, editorial, and mobile-friendly.
- Keep the page compact and under roughly 250 lines of HTML/CSS combined.
- Include only these sections: header, hero, featured products, brand benefits, and footer.
- Include exactly 3 product cards with names, descriptions, prices, and call-to-action buttons.
- Add a cart or bag indicator in the header.
- Use short beauty-brand copy and short CSS.
- Do not include testimonials, long routines, FAQs, extra sections, or placeholder paragraphs.
- Output HTML only.
""".strip()

print("[cosmetics-harness] Requesting storefront HTML...")

response = llm.chat(
    messages=[
        {"role": "system", "content": agent_prompt},
        {"role": "user", "content": user_message},
    ]
)

html = response["content"].strip()

checks = [
    "<!DOCTYPE html" in html or "<!doctype html" in html,
    brand.lower() in html.lower(),
    "featured".lower() in html.lower() or "products".lower() in html.lower(),
    "cart".lower() in html.lower() or "bag".lower() in html.lower(),
]
score = sum(1 for passed in checks if passed) / len(checks)

result = {
    "output": html,
    "score": score,
}

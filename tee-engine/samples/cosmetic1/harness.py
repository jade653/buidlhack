"""
Cosmetics landing page example agent package.

This example uses a small multi-agent flow for short brand copy and then
assembles a polished single-file HTML storefront with three embedded product
illustrations.
"""

from urllib.parse import quote


ALLOWED_MODELS = {
    "anthropic/claude-opus-4-6",
    "anthropic/claude-sonnet-4-5",
    "black-forest-labs/FLUX.2-klein-4B",
    "deepseek-ai/DeepSeek-V3.1",
    "google/gemini-3-pro",
    "openai/gpt-5.2",
    "openai/gpt-oss-120b",
    "Qwen/Qwen3-30B-A3B-Instruct-2507",
    "Qwen/Qwen3.5-122B-A10B",
    "zai-org/GLM-5-FP8",
}

SVG_LIBRARY = {
    "Petal Clean Gel Cleanser": """<svg width="800" height="960" viewBox="0 0 800 960" fill="none" xmlns="http://www.w3.org/2000/svg"><rect width="800" height="960" rx="48" fill="#F8ECE7"/><ellipse cx="402" cy="816" rx="196" ry="48" fill="#D3C1B9" fill-opacity="0.35"/><rect x="248" y="164" width="304" height="560" rx="68" fill="url(#tubeBody)"/><rect x="300" y="122" width="200" height="88" rx="34" fill="#F5D8CF"/><rect x="322" y="244" width="156" height="10" rx="5" fill="#E8B8AB"/><rect x="322" y="274" width="124" height="10" rx="5" fill="#E8B8AB"/><rect x="282" y="336" width="236" height="182" rx="34" fill="#FFF9F6" fill-opacity="0.9"/><text x="400" y="394" text-anchor="middle" fill="#874A41" font-family="Georgia, serif" font-size="34">PETAL</text><text x="400" y="438" text-anchor="middle" fill="#874A41" font-family="Arial, sans-serif" font-size="24" letter-spacing="3">CLEAN GEL</text><text x="400" y="478" text-anchor="middle" fill="#A96D62" font-family="Arial, sans-serif" font-size="16" letter-spacing="2">CAMELLIA DAILY WASH</text><rect x="288" y="700" width="224" height="92" rx="22" fill="#E9C9BF"/><rect x="324" y="728" width="152" height="20" rx="10" fill="#D7AAA0"/><defs><linearGradient id="tubeBody" x1="248" y1="164" x2="552" y2="724" gradientUnits="userSpaceOnUse"><stop stop-color="#FFE9E0"/><stop offset="1" stop-color="#E9C6BC"/></linearGradient></defs></svg>""",
    "Glass Drop Niacinamide Serum": """<svg width="800" height="960" viewBox="0 0 800 960" fill="none" xmlns="http://www.w3.org/2000/svg"><rect width="800" height="960" rx="48" fill="#EEEAF8"/><ellipse cx="402" cy="814" rx="184" ry="42" fill="#BEB6D8" fill-opacity="0.32"/><rect x="320" y="138" width="160" height="140" rx="28" fill="#CABFE8"/><rect x="352" y="104" width="96" height="74" rx="20" fill="#1E2238"/><rect x="246" y="246" width="308" height="462" rx="68" fill="url(#bottleBody)" fill-opacity="0.92"/><rect x="286" y="326" width="228" height="196" rx="34" fill="#FFFFFF" fill-opacity="0.84"/><text x="400" y="392" text-anchor="middle" fill="#4C4971" font-family="Georgia, serif" font-size="32">GLASS DROP</text><text x="400" y="434" text-anchor="middle" fill="#4C4971" font-family="Arial, sans-serif" font-size="22" letter-spacing="3">NIACINAMIDE</text><text x="400" y="474" text-anchor="middle" fill="#75719C" font-family="Arial, sans-serif" font-size="16" letter-spacing="2">TEXTURE REFINING SERUM</text><rect x="302" y="744" width="196" height="36" rx="18" fill="#B6A8DD"/><defs><linearGradient id="bottleBody" x1="246" y1="246" x2="554" y2="708" gradientUnits="userSpaceOnUse"><stop stop-color="#FAF8FF" stop-opacity="0.95"/><stop offset="1" stop-color="#CDBEEB" stop-opacity="0.98"/></linearGradient></defs></svg>""",
    "Velvet Barrier Cream": """<svg width="800" height="960" viewBox="0 0 800 960" fill="none" xmlns="http://www.w3.org/2000/svg"><rect width="800" height="960" rx="48" fill="#EAF1F4"/><ellipse cx="400" cy="812" rx="212" ry="44" fill="#ACC3CE" fill-opacity="0.3"/><rect x="210" y="446" width="380" height="220" rx="76" fill="url(#jarBody)"/><rect x="248" y="352" width="304" height="128" rx="42" fill="#D8E7EE"/><rect x="264" y="380" width="272" height="44" rx="22" fill="#C1D8E2"/><rect x="260" y="506" width="280" height="118" rx="34" fill="#FCFFFF" fill-opacity="0.92"/><text x="400" y="548" text-anchor="middle" fill="#4E6973" font-family="Georgia, serif" font-size="31">VELVET BARRIER</text><text x="400" y="590" text-anchor="middle" fill="#4E6973" font-family="Arial, sans-serif" font-size="22" letter-spacing="3">CERAMIDE CREAM</text><defs><linearGradient id="jarBody" x1="210" y1="446" x2="590" y2="666" gradientUnits="userSpaceOnUse"><stop stop-color="#F8FCFF"/><stop offset="1" stop-color="#D4E4EB"/></linearGradient></defs></svg>""",
}


def resolve_role_model(role_name):
    role_models = submission_config.extra.get("role_models", {})
    model_name = role_models.get(role_name, submission_config.model)
    if model_name not in ALLOWED_MODELS:
        raise ValueError(
            "Unsupported model for role '" + role_name + "': " + model_name
        )
    return model_name


def chat_role(role_name, instructions, prompt):
    response = llm.chat(
        messages=[
            {
                "role": "system",
                "content": agent_prompt + "\n\nRole: " + role_name + "\n" + instructions,
            },
            {"role": "user", "content": prompt},
        ],
        model=resolve_role_model(role_name),
        temperature=submission_config.temperature,
        max_tokens=submission_config.max_tokens,
    )
    return response["content"].strip()


def parse_fields(raw_text):
    defaults = {
        "badge": "Luma Dew Ritual",
        "title": "Soft-focus skincare for luminous everyday skin.",
        "body": "A calm three-step edit for cleansing, brightening, and barrier comfort.",
        "cta": "Shop the ritual",
        "benefit_title": "Designed for glow without the noise.",
        "benefit_body": "Elegant formulas, tactile textures, and a simple shelf-ready routine.",
    }

    parsed = {}
    for raw_line in raw_text.splitlines():
        line = raw_line.strip()
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip().lower()
        value = value.strip()
        if key in defaults and value:
            parsed[key] = value

    for key in defaults:
        if key not in parsed:
            parsed[key] = defaults[key]
    return parsed


def encode_svg_data_uri(svg_text):
    return "data:image/svg+xml;utf8," + quote(svg_text)


brand = challenge_input["brand"]
tagline = challenge_input["tagline"]
audience = challenge_input["audience"]
theme = challenge_input["theme"]
products = challenge_input.get("products", [])[:3]
features = challenge_input.get("features", [])

feature_lines = "\n".join("- " + item for item in features)
product_lines = "\n".join(
    "- " + item["name"] + ": " + item["description"] + " (" + item["price"] + ")"
    for item in products
)
rag_context = "\n\n".join(item[0] + ":\n" + item[1] for item in sorted(rag_docs.items()))

copy_prompt = (
    "Create compact premium beauty-brand landing page copy.\n\n"
    "Brand: " + brand + "\n"
    "Tagline: " + tagline + "\n"
    "Audience: " + audience + "\n"
    "Theme: " + theme + "\n\n"
    "Products:\n" + product_lines + "\n\n"
    "Features:\n" + feature_lines + "\n\n"
    "RAG notes:\n" + rag_context + "\n\n"
    "Return exactly six lines in this format:\n"
    "badge: ...\n"
    "title: ...\n"
    "body: ...\n"
    "cta: ...\n"
    "benefit_title: ...\n"
    "benefit_body: ..."
)

copy_draft = chat_role(
    "copywriter",
    "Write elegant short landing page copy. Keep each line concise and polished.",
    copy_prompt,
)

review_draft = chat_role(
    "reviewer",
    (
        "Review premium beauty landing page copy. "
        "If it is strong, rewrite it only lightly and keep the same six-line format."
    ),
    copy_draft,
)

copy = parse_fields(review_draft)

cards_html = []
for index in range(len(products)):
    product = products[index]
    image_src = encode_svg_data_uri(SVG_LIBRARY[product["name"]])
    card_html = (
        '<article class="product-card">'
        + '<div class="product-art"><img src="'
        + image_src
        + '" alt="'
        + product["name"]
        + '" /></div>'
        + '<div class="product-meta">'
        + '<p class="product-kicker">Step 0'
        + str(index + 1)
        + "</p>"
        + "<h3>"
        + product["name"]
        + "</h3>"
        + "<p>"
        + product["description"]
        + "</p>"
        + '<div class="product-row"><span class="price">'
        + product["price"]
        + '</span><button type="button">Add to bag</button></div>'
        + "</div>"
        + "</article>"
    )
    cards_html.append(card_html)

benefits_html = "".join(
    '<li><span class="dot"></span><span>' + item + "</span></li>"
    for item in features
)

html = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>__BRAND__</title>
  <style>
    :root {
      --bg: #f6efe8;
      --panel: rgba(255, 251, 247, 0.82);
      --card: rgba(255, 255, 255, 0.78);
      --ink: #1d2028;
      --muted: #6e6764;
      --rose: #d98a93;
      --rose-deep: #b96472;
      --sky: #cfdce6;
      --line: rgba(29, 32, 40, 0.08);
      --shadow: 0 24px 60px rgba(68, 45, 39, 0.12);
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: "Helvetica Neue", Arial, sans-serif;
      color: var(--ink);
      background:
        radial-gradient(circle at top left, rgba(255,255,255,0.75), transparent 32%),
        linear-gradient(180deg, #f8f0ea 0%, #f1e7df 45%, #efe9e8 100%);
    }
    .shell { max-width: 1200px; margin: 0 auto; padding: 24px; }
    .topbar, .hero, .benefits, footer {
      backdrop-filter: blur(18px);
      background: var(--panel);
      border: 1px solid rgba(255,255,255,0.55);
      box-shadow: var(--shadow);
    }
    .topbar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 16px 20px;
      border-radius: 24px;
      margin-bottom: 20px;
    }
    .brandmark { display: flex; align-items: center; gap: 12px; }
    .brandmark .orb {
      width: 16px; height: 16px; border-radius: 999px;
      background: linear-gradient(135deg, var(--rose), #f4c5ca);
      box-shadow: 0 0 0 8px rgba(217,138,147,0.12);
    }
    .brandmark strong {
      font-family: Georgia, serif;
      font-size: 20px;
      letter-spacing: 0.03em;
    }
    .bag {
      border: 0;
      border-radius: 999px;
      padding: 12px 18px;
      background: #fff;
      color: var(--ink);
      font-weight: 600;
    }
    .hero {
      border-radius: 34px;
      padding: 28px;
      display: grid;
      grid-template-columns: 1.15fr 0.85fr;
      gap: 24px;
      align-items: stretch;
    }
    .eyebrow {
      display: inline-flex;
      align-items: center;
      gap: 10px;
      padding: 8px 14px;
      border-radius: 999px;
      background: rgba(255,255,255,0.72);
      color: var(--rose-deep);
      font-size: 13px;
      text-transform: uppercase;
      letter-spacing: 0.12em;
    }
    h1 {
      margin: 18px 0 16px;
      font-family: Georgia, serif;
      font-size: clamp(42px, 6vw, 76px);
      line-height: 0.96;
      letter-spacing: -0.04em;
    }
    .hero-copy {
      max-width: 520px;
      color: var(--muted);
      font-size: 18px;
      line-height: 1.6;
      margin-bottom: 26px;
    }
    .hero-actions {
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      margin-bottom: 28px;
    }
    .hero-actions button, .hero-actions a {
      text-decoration: none;
      border-radius: 999px;
      padding: 14px 22px;
      font-weight: 600;
      border: none;
    }
    .hero-actions .primary { background: var(--ink); color: #fff; }
    .hero-actions .secondary { background: rgba(255,255,255,0.74); color: var(--ink); }
    .metrics {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 12px;
    }
    .metric {
      background: rgba(255,255,255,0.7);
      border: 1px solid var(--line);
      border-radius: 20px;
      padding: 16px;
    }
    .metric strong {
      display: block;
      font-size: 22px;
      margin-bottom: 6px;
      font-family: Georgia, serif;
    }
    .hero-stage {
      border-radius: 28px;
      padding: 24px;
      background:
        radial-gradient(circle at top right, rgba(217,138,147,0.32), transparent 28%),
        radial-gradient(circle at bottom left, rgba(207,220,230,0.45), transparent 28%),
        rgba(255,255,255,0.62);
      display: grid;
      place-items: center;
      overflow: hidden;
    }
    .hero-stage img {
      width: 100%;
      max-width: 440px;
      aspect-ratio: 5 / 6;
      object-fit: cover;
      filter: drop-shadow(0 30px 48px rgba(76, 52, 47, 0.18));
    }
    .section-head {
      display: flex;
      justify-content: space-between;
      gap: 24px;
      align-items: end;
      margin: 42px 4px 20px;
    }
    .section-head h2 {
      margin: 0;
      font-family: Georgia, serif;
      font-size: clamp(30px, 4vw, 46px);
      letter-spacing: -0.03em;
    }
    .section-head p {
      margin: 0;
      color: var(--muted);
      max-width: 420px;
      line-height: 1.6;
    }
    .products {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 18px;
    }
    .product-card {
      border-radius: 28px;
      padding: 18px;
      background: var(--card);
      border: 1px solid rgba(255,255,255,0.7);
      box-shadow: var(--shadow);
    }
    .product-art {
      border-radius: 22px;
      overflow: hidden;
      background: rgba(255,255,255,0.72);
      aspect-ratio: 5 / 6;
      margin-bottom: 16px;
    }
    .product-art img {
      width: 100%;
      height: 100%;
      object-fit: cover;
      display: block;
    }
    .product-kicker {
      margin: 0 0 8px;
      font-size: 12px;
      letter-spacing: 0.14em;
      color: var(--rose-deep);
      text-transform: uppercase;
    }
    .product-card h3 {
      margin: 0 0 8px;
      font-family: Georgia, serif;
      font-size: 28px;
      line-height: 1.05;
    }
    .product-card p {
      margin: 0 0 18px;
      color: var(--muted);
      line-height: 1.6;
    }
    .product-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
    }
    .price {
      font-weight: 700;
      font-size: 18px;
    }
    .product-row button {
      border: 0;
      border-radius: 999px;
      background: rgba(29,32,40,0.92);
      color: #fff;
      padding: 12px 18px;
      font-weight: 600;
    }
    .benefits {
      margin-top: 24px;
      border-radius: 30px;
      padding: 24px;
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 20px;
    }
    .benefits h3 {
      margin: 0 0 12px;
      font-family: Georgia, serif;
      font-size: 34px;
      letter-spacing: -0.03em;
    }
    .benefits p {
      margin: 0;
      color: var(--muted);
      line-height: 1.7;
    }
    .benefits ul {
      list-style: none;
      margin: 0;
      padding: 0;
      display: grid;
      gap: 12px;
    }
    .benefits li {
      display: flex;
      gap: 12px;
      align-items: center;
      padding: 16px 18px;
      border-radius: 18px;
      background: rgba(255,255,255,0.72);
      border: 1px solid var(--line);
    }
    .dot {
      width: 10px;
      height: 10px;
      border-radius: 999px;
      background: linear-gradient(135deg, var(--rose), #f3c3ca);
      flex: none;
    }
    footer {
      margin: 24px 0 8px;
      border-radius: 24px;
      padding: 18px 20px;
      display: flex;
      justify-content: space-between;
      gap: 16px;
      align-items: center;
      color: var(--muted);
    }
    @media (max-width: 980px) {
      .hero, .benefits, .products { grid-template-columns: 1fr; }
      .section-head, footer { display: block; }
      footer p { margin: 10px 0 0; }
    }
  </style>
</head>
<body>
  <div class="shell">
    <header class="topbar">
      <div class="brandmark">
        <span class="orb"></span>
        <strong>__BRAND__</strong>
      </div>
      <button class="bag" type="button">Bag (3)</button>
    </header>
    <section class="hero">
      <div>
        <span class="eyebrow">__BADGE__</span>
        <h1>__TITLE__</h1>
        <p class="hero-copy">__BODY__</p>
        <div class="hero-actions">
          <button class="primary" type="button">__CTA__</button>
          <a class="secondary" href="#products">Meet the trio</a>
        </div>
        <div class="metrics">
          <div class="metric"><strong>3-step</strong><span>Cleanse, treat, cushion.</span></div>
          <div class="metric"><strong>Soft glow</strong><span>Calm, polished, everyday skin.</span></div>
          <div class="metric"><strong>Routine-ready</strong><span>Built to sit beautifully on shelf and skin.</span></div>
        </div>
      </div>
      <div class="hero-stage">
        <img src="__HERO_IMAGE__" alt="__HERO_ALT__" />
      </div>
    </section>
    <div class="section-head" id="products">
      <div>
        <h2>Three products. One luminous routine.</h2>
      </div>
      <p>__TAGLINE__</p>
    </div>
    <section class="products">
      __CARDS__
    </section>
    <section class="benefits">
      <div>
        <h3>__BENEFIT_TITLE__</h3>
        <p>__BENEFIT_BODY__</p>
      </div>
      <ul>
        __BENEFITS__
      </ul>
    </section>
    <footer>
      <strong>__BRAND__</strong>
      <p>__AUDIENCE__</p>
    </footer>
  </div>
</body>
</html>
"""

html = html.replace("__BRAND__", brand)
html = html.replace("__BADGE__", copy["badge"])
html = html.replace("__TITLE__", copy["title"])
html = html.replace("__BODY__", copy["body"])
html = html.replace("__CTA__", copy["cta"])
html = html.replace("__TAGLINE__", tagline)
html = html.replace("__BENEFIT_TITLE__", copy["benefit_title"])
html = html.replace("__BENEFIT_BODY__", copy["benefit_body"])
html = html.replace("__AUDIENCE__", audience)
html = html.replace("__CARDS__", "".join(cards_html))
html = html.replace("__BENEFITS__", benefits_html)
html = html.replace("__HERO_IMAGE__", encode_svg_data_uri(SVG_LIBRARY[products[1]["name"]]))
html = html.replace("__HERO_ALT__", products[1]["name"])

checks = [
    "<!DOCTYPE html>" in html,
    brand.lower() in html.lower(),
    html.count("Add to bag") == 3,
    html.count("data:image/svg+xml") >= 3,
]

score = sum(1 for item in checks if item) / len(checks)

result = {
    "output": html,
    "score": score,
}

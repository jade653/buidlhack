"""
Cosmetic2 — higher-fidelity editorial cosmetics landing page package.

This version uses richer multi-agent copy generation and assembles a more
designed storefront with the same product assets and brand brief as cosmetic1.
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


def parse_fields(raw_text, defaults):
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

strategy_defaults = {
    "positioning": "A quiet luxury skincare edit shaped around glow, tactility, and restraint.",
    "moodline": "A shelf of soft light, subtle texture, and daily polish.",
    "editorial_note": "Make the brand feel styled, calm, and modern rather than promotional.",
}

strategy_prompt = (
    "Build a concise creative direction for a luxury cosmetics storefront.\n\n"
    "Brand: " + brand + "\n"
    "Tagline: " + tagline + "\n"
    "Audience: " + audience + "\n"
    "Theme: " + theme + "\n"
    "Products:\n" + product_lines + "\n\n"
    "Features:\n" + feature_lines + "\n\n"
    "RAG notes:\n" + rag_context + "\n\n"
    "Return exactly three lines:\n"
    "positioning: ...\n"
    "moodline: ...\n"
    "editorial_note: ..."
)

strategy_raw = chat_role(
    "brand_strategist",
    "Define concise luxury-beauty positioning and art direction cues.",
    strategy_prompt,
)
strategy = parse_fields(strategy_raw, strategy_defaults)

copy_defaults = {
    "badge": "Editorial glow edit",
    "hero_title": "Skincare composed with the softness of a morning ritual.",
    "hero_body": "Three formulas designed to cleanse, refine, and cushion the skin with a polished, premium calm.",
    "primary_cta": "Shop the collection",
    "secondary_cta": "See the ritual",
    "section_title": "A complete shelf-worthy routine in three precise textures.",
    "section_body": "Each formula carries a distinct tactile role, but the trio reads as one composed ritual.",
    "ritual_title": "The routine is built to feel elegant at every step.",
    "ritual_body": "Fresh gel, glassy treatment, and velvety barrier care create a sequence that looks as good as it feels.",
    "footer_note": "Clean formulas, refined textures, and modern vanity presence.",
}

copy_prompt = (
    "Write high-end beauty commerce copy using the strategy below.\n\n"
    "Positioning: " + strategy["positioning"] + "\n"
    "Moodline: " + strategy["moodline"] + "\n"
    "Editorial note: " + strategy["editorial_note"] + "\n\n"
    "Brand: " + brand + "\n"
    "Tagline: " + tagline + "\n"
    "Audience: " + audience + "\n"
    "Products:\n" + product_lines + "\n\n"
    "Return exactly ten lines:\n"
    "badge: ...\n"
    "hero_title: ...\n"
    "hero_body: ...\n"
    "primary_cta: ...\n"
    "secondary_cta: ...\n"
    "section_title: ...\n"
    "section_body: ...\n"
    "ritual_title: ...\n"
    "ritual_body: ...\n"
    "footer_note: ..."
)

copy_raw = chat_role(
    "copywriter",
    "Write refined editorial beauty copy with short, elegant lines and strong rhythm.",
    copy_prompt,
)
copy = parse_fields(copy_raw, copy_defaults)

merch_defaults = {
    "spotlight_title": "Three textures, one luminous rhythm.",
    "spotlight_body": "A cleanser for clarity, a serum for glass-skin sheen, and a cream that seals everything in with plush comfort.",
    "texture_note": "Designed to move from airy cleanse to watery glow to soft final cushion.",
}

merch_prompt = (
    "Create compact merchandising copy for a premium skincare landing page.\n\n"
    "Brand: " + brand + "\n"
    "Products:\n" + product_lines + "\n\n"
    "Return exactly three lines:\n"
    "spotlight_title: ...\n"
    "spotlight_body: ...\n"
    "texture_note: ..."
)

merch_raw = chat_role(
    "merch_editor",
    "Sharpen the merchandising language so the lineup feels premium and tactile.",
    merch_prompt,
)
merch = parse_fields(merch_raw, merch_defaults)

review_defaults = copy_defaults.copy()
review_defaults.update(merch_defaults)

review_prompt = (
    "Polish the final copy set for a premium cosmetics landing page.\n\n"
    "Positioning: " + strategy["positioning"] + "\n"
    "Moodline: " + strategy["moodline"] + "\n"
    "Editorial note: " + strategy["editorial_note"] + "\n\n"
    "Copy set:\n"
    "badge: " + copy["badge"] + "\n"
    "hero_title: " + copy["hero_title"] + "\n"
    "hero_body: " + copy["hero_body"] + "\n"
    "primary_cta: " + copy["primary_cta"] + "\n"
    "secondary_cta: " + copy["secondary_cta"] + "\n"
    "section_title: " + copy["section_title"] + "\n"
    "section_body: " + copy["section_body"] + "\n"
    "ritual_title: " + copy["ritual_title"] + "\n"
    "ritual_body: " + copy["ritual_body"] + "\n"
    "footer_note: " + copy["footer_note"] + "\n"
    "spotlight_title: " + merch["spotlight_title"] + "\n"
    "spotlight_body: " + merch["spotlight_body"] + "\n"
    "texture_note: " + merch["texture_note"] + "\n\n"
    "Return the same thirteen lines, polished but still concise."
)

reviewed_raw = chat_role(
    "reviewer",
    "Edit the full copy set so it reads expensive, coherent, and display-ready.",
    review_prompt,
)
final_copy = parse_fields(reviewed_raw, review_defaults)

cards_html = []
for index in range(len(products)):
    product = products[index]
    image_src = encode_svg_data_uri(SVG_LIBRARY[product["name"]])
    card_html = (
        '<article class="product-card">'
        + '<div class="product-frame"><img src="'
        + image_src
        + '" alt="'
        + product["name"]
        + '" /></div>'
        + '<div class="product-copy">'
        + '<p class="step">0'
        + str(index + 1)
        + "</p>"
        + "<h3>"
        + product["name"]
        + "</h3>"
        + "<p>"
        + product["description"]
        + "</p>"
        + '<div class="row"><span class="price">'
        + product["price"]
        + '</span><button type="button">Add to bag</button></div>'
        + "</div>"
        + "</article>"
    )
    cards_html.append(card_html)

benefits_html = "".join(
    '<li><span class="mark"></span><span>' + item + "</span></li>"
    for item in features
)

hero_src = encode_svg_data_uri(SVG_LIBRARY[products[1]["name"]])
left_src = encode_svg_data_uri(SVG_LIBRARY[products[0]["name"]])
right_src = encode_svg_data_uri(SVG_LIBRARY[products[2]["name"]])

html = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>__BRAND__</title>
  <style>
    :root {
      --ink: #17181e;
      --muted: #6a6568;
      --stone: #f3ece7;
      --sand: #fff9f6;
      --rose: #d9919d;
      --plum: #6f668f;
      --sage: #cad6d8;
      --glass: rgba(255,255,255,0.68);
      --line: rgba(23,24,30,0.08);
      --shadow: 0 30px 90px rgba(64, 45, 44, 0.12);
    }
    * { box-sizing: border-box; }
    html { scroll-behavior: smooth; }
    body {
      margin: 0;
      color: var(--ink);
      font-family: "Helvetica Neue", Arial, sans-serif;
      background:
        radial-gradient(circle at 10% 10%, rgba(255,255,255,0.9), transparent 26%),
        radial-gradient(circle at 88% 16%, rgba(217,145,157,0.18), transparent 24%),
        linear-gradient(180deg, #f8f0ea 0%, #f0e6e1 44%, #eee9e7 100%);
    }
    .shell { max-width: 1260px; margin: 0 auto; padding: 26px; }
    .nav, .hero, .quote-band, .spotlight, footer {
      backdrop-filter: blur(20px);
      background: var(--glass);
      border: 1px solid rgba(255,255,255,0.64);
      box-shadow: var(--shadow);
    }
    .nav {
      border-radius: 26px;
      padding: 16px 20px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 18px;
    }
    .wordmark {
      display: flex;
      align-items: center;
      gap: 14px;
      font-family: Georgia, serif;
      letter-spacing: 0.03em;
      font-size: 22px;
    }
    .wordmark .seed {
      width: 18px;
      height: 18px;
      border-radius: 999px;
      background: linear-gradient(135deg, var(--rose), #f3ccd2);
      box-shadow: 0 0 0 9px rgba(217,145,157,0.12);
    }
    .nav-meta {
      display: flex;
      align-items: center;
      gap: 10px;
      color: var(--muted);
      font-size: 14px;
    }
    .bag {
      border: none;
      border-radius: 999px;
      padding: 12px 18px;
      background: #fff;
      font-weight: 700;
      color: var(--ink);
    }
    .hero {
      border-radius: 36px;
      padding: 28px;
      display: grid;
      grid-template-columns: 1.05fr 0.95fr;
      gap: 24px;
      overflow: hidden;
    }
    .eyebrow {
      display: inline-flex;
      align-items: center;
      gap: 10px;
      border-radius: 999px;
      padding: 8px 14px;
      background: rgba(255,255,255,0.72);
      color: #9f5662;
      text-transform: uppercase;
      font-size: 12px;
      letter-spacing: 0.14em;
    }
    h1 {
      margin: 18px 0 14px;
      font-family: Georgia, serif;
      font-size: clamp(48px, 7vw, 88px);
      line-height: 0.92;
      letter-spacing: -0.05em;
      max-width: 680px;
    }
    .lede {
      max-width: 540px;
      color: var(--muted);
      font-size: 18px;
      line-height: 1.7;
      margin: 0 0 24px;
    }
    .hero-actions {
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      margin-bottom: 28px;
    }
    .hero-actions button, .hero-actions a {
      border: none;
      border-radius: 999px;
      padding: 14px 22px;
      font-weight: 700;
      text-decoration: none;
    }
    .hero-actions .primary { background: var(--ink); color: #fff; }
    .hero-actions .secondary { background: rgba(255,255,255,0.76); color: var(--ink); }
    .micro-grid {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 12px;
    }
    .micro-card {
      border-radius: 22px;
      background: rgba(255,255,255,0.72);
      border: 1px solid var(--line);
      padding: 16px;
    }
    .micro-card strong {
      display: block;
      font-family: Georgia, serif;
      font-size: 22px;
      margin-bottom: 6px;
    }
    .stage {
      position: relative;
      min-height: 620px;
      border-radius: 32px;
      background:
        radial-gradient(circle at top right, rgba(217,145,157,0.34), transparent 28%),
        radial-gradient(circle at bottom left, rgba(202,214,216,0.42), transparent 28%),
        rgba(255,255,255,0.66);
      overflow: hidden;
    }
    .stage img {
      position: absolute;
      display: block;
      filter: drop-shadow(0 30px 52px rgba(62, 42, 47, 0.18));
    }
    .stage .center {
      width: 54%;
      left: 23%;
      top: 9%;
    }
    .stage .left {
      width: 34%;
      left: -4%;
      bottom: -2%;
      transform: rotate(-6deg);
    }
    .stage .right {
      width: 34%;
      right: -4%;
      bottom: 4%;
      transform: rotate(6deg);
    }
    .quote-band {
      margin-top: 18px;
      border-radius: 28px;
      padding: 24px 26px;
      display: grid;
      grid-template-columns: 0.9fr 1.1fr;
      gap: 20px;
      align-items: center;
    }
    .quote-band h2,
    .spotlight h2,
    .products-head h2 {
      margin: 0;
      font-family: Georgia, serif;
      letter-spacing: -0.04em;
    }
    .quote-band h2 { font-size: clamp(30px, 4vw, 44px); }
    .quote-band p {
      margin: 0;
      color: var(--muted);
      line-height: 1.7;
      font-size: 16px;
    }
    .products-head {
      display: flex;
      justify-content: space-between;
      gap: 18px;
      align-items: end;
      margin: 42px 4px 18px;
    }
    .products-head h2 { font-size: clamp(34px, 4vw, 52px); }
    .products-head p {
      margin: 0;
      max-width: 420px;
      color: var(--muted);
      line-height: 1.7;
    }
    .products {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 18px;
    }
    .product-card {
      border-radius: 30px;
      padding: 18px;
      background: rgba(255,255,255,0.76);
      border: 1px solid rgba(255,255,255,0.72);
      box-shadow: var(--shadow);
    }
    .product-frame {
      border-radius: 24px;
      overflow: hidden;
      background: rgba(255,255,255,0.84);
      aspect-ratio: 5 / 6;
      margin-bottom: 16px;
    }
    .product-frame img {
      width: 100%;
      height: 100%;
      object-fit: cover;
      display: block;
    }
    .step {
      margin: 0 0 8px;
      color: #9f5662;
      font-size: 12px;
      letter-spacing: 0.18em;
      text-transform: uppercase;
    }
    .product-copy h3 {
      margin: 0 0 8px;
      font-family: Georgia, serif;
      font-size: 29px;
      line-height: 1.05;
    }
    .product-copy p {
      margin: 0 0 18px;
      color: var(--muted);
      line-height: 1.65;
    }
    .row {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 12px;
    }
    .price {
      font-size: 19px;
      font-weight: 700;
    }
    .row button {
      border: none;
      border-radius: 999px;
      background: var(--ink);
      color: #fff;
      padding: 12px 18px;
      font-weight: 700;
    }
    .spotlight {
      margin-top: 22px;
      border-radius: 34px;
      padding: 24px;
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 20px;
    }
    .spotlight h2 { font-size: clamp(32px, 4vw, 46px); }
    .spotlight p {
      margin: 0;
      color: var(--muted);
      line-height: 1.75;
    }
    .benefits {
      list-style: none;
      margin: 0;
      padding: 0;
      display: grid;
      gap: 12px;
    }
    .benefits li {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 16px 18px;
      border-radius: 18px;
      background: rgba(255,255,255,0.74);
      border: 1px solid var(--line);
    }
    .mark {
      width: 10px;
      height: 10px;
      border-radius: 999px;
      background: linear-gradient(135deg, var(--rose), #f1cdd3);
      flex: none;
    }
    footer {
      margin-top: 24px;
      border-radius: 28px;
      padding: 20px 22px;
      display: flex;
      justify-content: space-between;
      gap: 16px;
      align-items: center;
      color: var(--muted);
    }
    footer strong {
      font-family: Georgia, serif;
      color: var(--ink);
      font-size: 22px;
    }
    @media (max-width: 1024px) {
      .hero, .quote-band, .spotlight, .products { grid-template-columns: 1fr; }
      .products-head, footer { display: block; }
      .stage { min-height: 520px; }
      footer p { margin: 8px 0 0; }
    }
  </style>
</head>
<body>
  <div class="shell">
    <header class="nav">
      <div class="wordmark"><span class="seed"></span><strong>__BRAND__</strong></div>
      <div class="nav-meta"><span>__POSITIONING__</span><button class="bag" type="button">Bag (3)</button></div>
    </header>
    <section class="hero">
      <div>
        <span class="eyebrow">__BADGE__</span>
        <h1>__HERO_TITLE__</h1>
        <p class="lede">__HERO_BODY__</p>
        <div class="hero-actions">
          <button class="primary" type="button">__PRIMARY_CTA__</button>
          <a class="secondary" href="#collection">__SECONDARY_CTA__</a>
        </div>
        <div class="micro-grid">
          <div class="micro-card"><strong>3 formulas</strong><span>Curated to read as one complete shelf edit.</span></div>
          <div class="micro-card"><strong>Soft luxury</strong><span>Modern calm, luminous texture, no excess.</span></div>
          <div class="micro-card"><strong>Daily ritual</strong><span>Built for vanity presence and everyday use.</span></div>
        </div>
      </div>
      <div class="stage">
        <img class="center" src="__HERO_SRC__" alt="__HERO_ALT__" />
        <img class="left" src="__LEFT_SRC__" alt="__LEFT_ALT__" />
        <img class="right" src="__RIGHT_SRC__" alt="__RIGHT_ALT__" />
      </div>
    </section>
    <section class="quote-band">
      <h2>__RITUAL_TITLE__</h2>
      <div>
        <p>__RITUAL_BODY__</p>
        <p style="margin-top:14px;"><strong style="color:var(--ink);">__MOODLINE__</strong></p>
      </div>
    </section>
    <div class="products-head" id="collection">
      <div>
        <h2>__SECTION_TITLE__</h2>
      </div>
      <p>__SECTION_BODY__</p>
    </div>
    <section class="products">
      __CARDS__
    </section>
    <section class="spotlight">
      <div>
        <h2>__SPOTLIGHT_TITLE__</h2>
      </div>
      <div>
        <p>__SPOTLIGHT_BODY__</p>
        <p style="margin-top:14px;">__TEXTURE_NOTE__</p>
        <ul class="benefits" style="margin-top:18px;">__BENEFITS__</ul>
      </div>
    </section>
    <footer>
      <strong>__BRAND__</strong>
      <p>__FOOTER_NOTE__</p>
    </footer>
  </div>
</body>
</html>
"""

html = html.replace("__BRAND__", brand)
html = html.replace("__POSITIONING__", strategy["positioning"])
html = html.replace("__BADGE__", final_copy["badge"])
html = html.replace("__HERO_TITLE__", final_copy["hero_title"])
html = html.replace("__HERO_BODY__", final_copy["hero_body"])
html = html.replace("__PRIMARY_CTA__", final_copy["primary_cta"])
html = html.replace("__SECONDARY_CTA__", final_copy["secondary_cta"])
html = html.replace("__RITUAL_TITLE__", final_copy["ritual_title"])
html = html.replace("__RITUAL_BODY__", final_copy["ritual_body"])
html = html.replace("__MOODLINE__", strategy["moodline"])
html = html.replace("__SECTION_TITLE__", final_copy["section_title"])
html = html.replace("__SECTION_BODY__", final_copy["section_body"])
html = html.replace("__SPOTLIGHT_TITLE__", final_copy["spotlight_title"])
html = html.replace("__SPOTLIGHT_BODY__", final_copy["spotlight_body"])
html = html.replace("__TEXTURE_NOTE__", final_copy["texture_note"])
html = html.replace("__FOOTER_NOTE__", final_copy["footer_note"])
html = html.replace("__CARDS__", "".join(cards_html))
html = html.replace("__BENEFITS__", benefits_html)
html = html.replace("__HERO_SRC__", hero_src)
html = html.replace("__HERO_ALT__", products[1]["name"])
html = html.replace("__LEFT_SRC__", left_src)
html = html.replace("__LEFT_ALT__", products[0]["name"])
html = html.replace("__RIGHT_SRC__", right_src)
html = html.replace("__RIGHT_ALT__", products[2]["name"])

checks = [
    "<!DOCTYPE html>" in html,
    brand.lower() in html.lower(),
    html.count("Add to bag") == 3,
    html.count("data:image/svg+xml") >= 4,
    "spotlight" in html.lower(),
]

score = sum(1 for item in checks if item) / len(checks)

result = {
    "output": html,
    "score": score,
}

"""
Cosmetic3 — cinematic, motion-heavy premium cosmetics landing page package.

This package spends more tokens than cosmetic1/2 by running a richer set of
role-specific model calls and assembling a denser editorial storefront with
motion layers, reveal choreography, and multiple narrative sections.
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
    "positioning": "A cinematic skincare launch shaped around glow, materiality, and modern restraint.",
    "moodline": "Soft chrome light, quiet glass reflections, and a vanity ritual staged like an editorial set.",
    "visual_axis": "Rose warmth meets lilac sheen and pale mineral neutrals.",
    "hero_scene": "Three products suspended in an atmosphere of slow light and floating texture.",
    "launch_phrase": "A routine presented with the drama of a beauty film and the calm of a private ritual.",
}

strategy_prompt = (
    "Build a premium visual strategy for a cinematic skincare storefront.\n\n"
    "Brand: " + brand + "\n"
    "Tagline: " + tagline + "\n"
    "Audience: " + audience + "\n"
    "Theme: " + theme + "\n\n"
    "Products:\n" + product_lines + "\n\n"
    "Features:\n" + feature_lines + "\n\n"
    "RAG notes:\n" + rag_context + "\n\n"
    "Return exactly five lines:\n"
    "positioning: ...\n"
    "moodline: ...\n"
    "visual_axis: ...\n"
    "hero_scene: ...\n"
    "launch_phrase: ..."
)

strategy_raw = chat_role(
    "brand_strategist",
    "Create a luxury-beauty launch concept with cinematic visual language and strong art direction.",
    strategy_prompt,
)
strategy = parse_fields(strategy_raw, strategy_defaults)

campaign_defaults = {
    "badge": "Launch sequence",
    "hero_title": "Skincare staged with the glow, motion, and atmosphere of a beauty short film.",
    "hero_body": "A three-piece ritual for cleansing, glass-skin brightness, and barrier comfort, presented with quiet drama and tactile polish.",
    "primary_cta": "Enter the launch",
    "secondary_cta": "Watch the ritual",
    "marquee": "Clinical glow. Slow motion texture. Vanity-light calm. Editorial skin ritual.",
    "manifesto_title": "A shelf that looks lit from within.",
    "manifesto_body": "The ritual is built to feel composed in motion: a clean beginning, a reflective middle layer, and a final velvet seal.",
    "ritual_title": "Three textures move like one continuous gesture.",
    "ritual_body": "Fresh gel clarity, liquid light treatment, and plush barrier finish unfold as a measured sequence rather than three isolated products.",
    "section_title": "A launch composition built around three formulas and one luminous point of view.",
    "section_body": "The range reads like a beauty editorial: distinct silhouettes, distinct textures, and a single cinematic mood.",
}

campaign_prompt = (
    "Write cinematic luxury-beauty campaign copy using the strategy below.\n\n"
    "Positioning: " + strategy["positioning"] + "\n"
    "Moodline: " + strategy["moodline"] + "\n"
    "Visual axis: " + strategy["visual_axis"] + "\n"
    "Hero scene: " + strategy["hero_scene"] + "\n"
    "Launch phrase: " + strategy["launch_phrase"] + "\n\n"
    "Brand: " + brand + "\n"
    "Tagline: " + tagline + "\n"
    "Audience: " + audience + "\n"
    "Products:\n" + product_lines + "\n\n"
    "Return exactly twelve lines:\n"
    "badge: ...\n"
    "hero_title: ...\n"
    "hero_body: ...\n"
    "primary_cta: ...\n"
    "secondary_cta: ...\n"
    "marquee: ...\n"
    "manifesto_title: ...\n"
    "manifesto_body: ...\n"
    "ritual_title: ...\n"
    "ritual_body: ...\n"
    "section_title: ...\n"
    "section_body: ..."
)

campaign_raw = chat_role(
    "campaign_writer",
    "Write elevated campaign copy with cinematic image-making, strong rhythm, and short luxurious sentences.",
    campaign_prompt,
)
campaign = parse_fields(campaign_raw, campaign_defaults)

motion_defaults = {
    "motion_concept": "Float, shimmer, drift, and reveal with the pace of a luxury campaign microsite.",
    "motion_tagline": "Everything should feel suspended in slow editorial motion.",
    "aura_label": "Aurora glow field",
    "sequence_label": "Launch sequence",
    "texture_label": "Texture in motion",
    "shimmer_label": "Glass-skin shimmer pass",
    "rail_phrase": "Floating surfaces. Lit edges. Slow glow. Modern vanity theatre.",
    "hover_phrase": "Objects should rise subtly, catch light, and settle back with softness.",
}

motion_prompt = (
    "Define motion direction for a premium cosmetics landing page.\n\n"
    "Strategy:\n"
    "Positioning: " + strategy["positioning"] + "\n"
    "Moodline: " + strategy["moodline"] + "\n"
    "Hero scene: " + strategy["hero_scene"] + "\n\n"
    "Return exactly eight lines:\n"
    "motion_concept: ...\n"
    "motion_tagline: ...\n"
    "aura_label: ...\n"
    "sequence_label: ...\n"
    "texture_label: ...\n"
    "shimmer_label: ...\n"
    "rail_phrase: ...\n"
    "hover_phrase: ..."
)

motion_raw = chat_role(
    "motion_director",
    "Describe premium, restrained motion cues for a cinematic beauty landing page.",
    motion_prompt,
)
motion = parse_fields(motion_raw, motion_defaults)

conversion_defaults = {
    "spotlight_title": "A launch ritual built to be watched, hovered, and shopped.",
    "spotlight_body": "The collection balances shelf appeal with a clearly merchandised route into purchase, keeping the experience luxurious but legible.",
    "detail_note": "Each card should feel collectible, tactile, and softly theatrical.",
    "footer_note": "Luxury skincare composed for motion, display, and daily ritual.",
    "product_1_story": "An airy first cleanse that clears the frame and resets the skin.",
    "product_2_story": "A glassy treatment layer that catches light and smooths the whole composition.",
    "product_3_story": "A velvet final step that seals the ritual with softness and calm.",
}

conversion_prompt = (
    "Write merchandising and conversion copy for a cinematic beauty storefront.\n\n"
    "Brand: " + brand + "\n"
    "Products:\n" + product_lines + "\n\n"
    "Return exactly seven lines:\n"
    "spotlight_title: ...\n"
    "spotlight_body: ...\n"
    "detail_note: ...\n"
    "footer_note: ...\n"
    "product_1_story: ...\n"
    "product_2_story: ...\n"
    "product_3_story: ..."
)

conversion_raw = chat_role(
    "conversion_editor",
    "Refine the page so it still converts while preserving a luxurious editorial feel.",
    conversion_prompt,
)
conversion = parse_fields(conversion_raw, conversion_defaults)

review_defaults = {}
for item in strategy_defaults:
    review_defaults[item] = strategy_defaults[item]
for item in campaign_defaults:
    review_defaults[item] = campaign_defaults[item]
for item in motion_defaults:
    review_defaults[item] = motion_defaults[item]
for item in conversion_defaults:
    review_defaults[item] = conversion_defaults[item]

review_prompt = (
    "Polish the full launch copy set so it feels premium, coherent, and display-ready.\n\n"
    "Strategy:\n"
    "positioning: " + strategy["positioning"] + "\n"
    "moodline: " + strategy["moodline"] + "\n"
    "visual_axis: " + strategy["visual_axis"] + "\n"
    "hero_scene: " + strategy["hero_scene"] + "\n"
    "launch_phrase: " + strategy["launch_phrase"] + "\n\n"
    "Campaign:\n"
    "badge: " + campaign["badge"] + "\n"
    "hero_title: " + campaign["hero_title"] + "\n"
    "hero_body: " + campaign["hero_body"] + "\n"
    "primary_cta: " + campaign["primary_cta"] + "\n"
    "secondary_cta: " + campaign["secondary_cta"] + "\n"
    "marquee: " + campaign["marquee"] + "\n"
    "manifesto_title: " + campaign["manifesto_title"] + "\n"
    "manifesto_body: " + campaign["manifesto_body"] + "\n"
    "ritual_title: " + campaign["ritual_title"] + "\n"
    "ritual_body: " + campaign["ritual_body"] + "\n"
    "section_title: " + campaign["section_title"] + "\n"
    "section_body: " + campaign["section_body"] + "\n\n"
    "Motion:\n"
    "motion_concept: " + motion["motion_concept"] + "\n"
    "motion_tagline: " + motion["motion_tagline"] + "\n"
    "aura_label: " + motion["aura_label"] + "\n"
    "sequence_label: " + motion["sequence_label"] + "\n"
    "texture_label: " + motion["texture_label"] + "\n"
    "shimmer_label: " + motion["shimmer_label"] + "\n"
    "rail_phrase: " + motion["rail_phrase"] + "\n"
    "hover_phrase: " + motion["hover_phrase"] + "\n\n"
    "Conversion:\n"
    "spotlight_title: " + conversion["spotlight_title"] + "\n"
    "spotlight_body: " + conversion["spotlight_body"] + "\n"
    "detail_note: " + conversion["detail_note"] + "\n"
    "footer_note: " + conversion["footer_note"] + "\n"
    "product_1_story: " + conversion["product_1_story"] + "\n"
    "product_2_story: " + conversion["product_2_story"] + "\n"
    "product_3_story: " + conversion["product_3_story"] + "\n\n"
    "Return the same thirty-two lines with the same keys, only polished."
)

review_raw = chat_role(
    "reviewer",
    "Act as the final editorial reviewer for a high-budget beauty launch microsite. Keep the output rich but concise.",
    review_prompt,
)
final_copy = parse_fields(review_raw, review_defaults)

product_story_keys = [
    "product_1_story",
    "product_2_story",
    "product_3_story",
]

cards_html = []
for index in range(len(products)):
    product = products[index]
    story_key = product_story_keys[index]
    image_src = encode_svg_data_uri(SVG_LIBRARY[product["name"]])
    card_html = (
        '<article class="product-card reveal" style="transition-delay: '
        + str(index * 120)
        + 'ms;">'
        + '<div class="product-shell">'
        + '<div class="product-aura"></div>'
        + '<div class="product-frame"><img src="'
        + image_src
        + '" alt="'
        + product["name"]
        + '" /></div>'
        + "</div>"
        + '<div class="product-copy">'
        + '<p class="step">STEP 0'
        + str(index + 1)
        + "</p>"
        + "<h3>"
        + product["name"]
        + "</h3>"
        + '<p class="story">'
        + final_copy[story_key]
        + "</p>"
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

benefits_html = ""
for feature in features:
    benefits_html += (
        '<li><span class="mark"></span><span>' + feature + "</span></li>"
    )

ritual_steps_html = ""
for index in range(len(products)):
    product = products[index]
    story_key = product_story_keys[index]
    ritual_steps_html += (
        '<article class="ritual-step reveal" style="transition-delay: '
        + str(index * 100)
        + 'ms;">'
        + "<strong>0"
        + str(index + 1)
        + "</strong>"
        + "<h4>"
        + product["name"]
        + "</h4>"
        + "<p>"
        + final_copy[story_key]
        + "</p>"
        + "</article>"
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
      --ink: #14151b;
      --muted: #6c6870;
      --paper: #f7f0ea;
      --glass: rgba(255,255,255,0.64);
      --rose: #d78f9a;
      --violet: #9383c9;
      --mist: #cad8dd;
      --line: rgba(20,21,27,0.08);
      --shadow: 0 36px 120px rgba(61, 41, 45, 0.16);
      --shadow-soft: 0 18px 44px rgba(61, 41, 45, 0.10);
    }
    * { box-sizing: border-box; }
    html { scroll-behavior: smooth; }
    body {
      margin: 0;
      color: var(--ink);
      font-family: "Helvetica Neue", Arial, sans-serif;
      background:
        radial-gradient(circle at 10% 10%, rgba(255,255,255,0.92), transparent 24%),
        radial-gradient(circle at 86% 12%, rgba(147,131,201,0.22), transparent 26%),
        radial-gradient(circle at 80% 86%, rgba(215,143,154,0.18), transparent 20%),
        linear-gradient(180deg, #fbf3ed 0%, #f3e8e1 42%, #efe8e6 100%);
      overflow-x: hidden;
    }
    .ambient,
    .ambient::before,
    .ambient::after {
      position: fixed;
      inset: 0;
      pointer-events: none;
      content: "";
    }
    .ambient::before {
      background:
        radial-gradient(circle at 15% 20%, rgba(255,255,255,0.55), transparent 20%),
        radial-gradient(circle at 82% 18%, rgba(215,143,154,0.22), transparent 22%),
        radial-gradient(circle at 74% 80%, rgba(147,131,201,0.18), transparent 20%);
      animation: auraDrift 14s ease-in-out infinite alternate;
    }
    .ambient::after {
      background:
        linear-gradient(120deg, transparent 20%, rgba(255,255,255,0.22) 48%, transparent 76%);
      transform: translateX(-120%);
      animation: shineSweep 12s linear infinite;
      opacity: 0.55;
    }
    .shell {
      position: relative;
      max-width: 1320px;
      margin: 0 auto;
      padding: 28px;
      z-index: 2;
    }
    .nav, .hero, .marquee, .manifesto, .spotlight, .ritual, footer {
      backdrop-filter: blur(22px);
      background: var(--glass);
      border: 1px solid rgba(255,255,255,0.64);
      box-shadow: var(--shadow);
    }
    .nav {
      border-radius: 28px;
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
      font-size: 22px;
      letter-spacing: 0.03em;
    }
    .seed {
      width: 18px;
      height: 18px;
      border-radius: 999px;
      background: linear-gradient(135deg, var(--rose), #f2ccd2);
      box-shadow: 0 0 0 9px rgba(215,143,154,0.12);
      animation: pulseHalo 4.2s ease-in-out infinite;
    }
    .nav-meta {
      display: flex;
      gap: 14px;
      align-items: center;
      color: var(--muted);
      font-size: 14px;
    }
    .bag {
      border: none;
      border-radius: 999px;
      padding: 12px 18px;
      background: rgba(255,255,255,0.88);
      color: var(--ink);
      font-weight: 700;
      box-shadow: var(--shadow-soft);
    }
    .hero {
      border-radius: 38px;
      padding: 30px;
      display: grid;
      grid-template-columns: 1.04fr 0.96fr;
      gap: 24px;
      overflow: hidden;
      position: relative;
    }
    .hero::before {
      content: "";
      position: absolute;
      inset: 0;
      background:
        radial-gradient(circle at 18% 22%, rgba(255,255,255,0.48), transparent 24%),
        radial-gradient(circle at 80% 18%, rgba(147,131,201,0.16), transparent 24%),
        radial-gradient(circle at 76% 76%, rgba(215,143,154,0.18), transparent 24%);
      mix-blend-mode: screen;
      animation: auraDrift 16s ease-in-out infinite alternate;
    }
    .eyebrow {
      position: relative;
      z-index: 1;
      display: inline-flex;
      align-items: center;
      gap: 10px;
      border-radius: 999px;
      padding: 8px 14px;
      background: rgba(255,255,255,0.76);
      color: #a15763;
      text-transform: uppercase;
      font-size: 12px;
      letter-spacing: 0.16em;
    }
    h1 {
      position: relative;
      z-index: 1;
      margin: 18px 0 14px;
      max-width: 700px;
      font-family: Georgia, serif;
      font-size: clamp(54px, 7vw, 96px);
      line-height: 0.9;
      letter-spacing: -0.06em;
    }
    .lede, .sublede {
      position: relative;
      z-index: 1;
      max-width: 560px;
      color: var(--muted);
      line-height: 1.75;
      font-size: 18px;
      margin: 0 0 14px;
    }
    .hero-actions {
      position: relative;
      z-index: 1;
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      margin: 24px 0 28px;
    }
    .hero-actions button, .hero-actions a {
      border: none;
      border-radius: 999px;
      padding: 14px 22px;
      text-decoration: none;
      font-weight: 700;
    }
    .hero-actions .primary { background: var(--ink); color: #fff; }
    .hero-actions .secondary { background: rgba(255,255,255,0.78); color: var(--ink); }
    .micro-grid {
      position: relative;
      z-index: 1;
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 12px;
    }
    .micro-card {
      border-radius: 22px;
      background: rgba(255,255,255,0.72);
      border: 1px solid var(--line);
      padding: 16px;
      box-shadow: var(--shadow-soft);
      transform: translateY(0);
      animation: slowLift 8s ease-in-out infinite;
    }
    .micro-card:nth-child(2) { animation-delay: 1.2s; }
    .micro-card:nth-child(3) { animation-delay: 2.4s; }
    .micro-card strong {
      display: block;
      margin-bottom: 6px;
      font-family: Georgia, serif;
      font-size: 22px;
    }
    .hero-stage {
      position: relative;
      min-height: 700px;
      border-radius: 34px;
      overflow: hidden;
      background:
        radial-gradient(circle at 80% 18%, rgba(255,255,255,0.34), transparent 18%),
        radial-gradient(circle at 22% 78%, rgba(202,216,221,0.42), transparent 20%),
        linear-gradient(180deg, rgba(255,255,255,0.54), rgba(255,255,255,0.18));
    }
    .hero-stage::before {
      content: "";
      position: absolute;
      inset: 12% 18% auto auto;
      width: 180px;
      height: 180px;
      border-radius: 999px;
      background: radial-gradient(circle, rgba(255,255,255,0.42), transparent 68%);
      filter: blur(10px);
      animation: haloFloat 7s ease-in-out infinite;
    }
    .hero-stage .product {
      position: absolute;
      display: block;
      filter: drop-shadow(0 34px 64px rgba(51, 37, 44, 0.18));
      transform-origin: center;
      transition: transform 0.5s ease;
    }
    .hero-stage:hover .product { transform: translateY(-8px) scale(1.02); }
    .hero-stage .center {
      width: 54%;
      left: 23%;
      top: 6%;
      animation: heroFloat 7.8s ease-in-out infinite;
      z-index: 3;
    }
    .hero-stage .left {
      width: 34%;
      left: -2%;
      bottom: 2%;
      transform: rotate(-7deg);
      animation: heroFloatAlt 9.4s ease-in-out infinite;
      z-index: 2;
    }
    .hero-stage .right {
      width: 34%;
      right: -2%;
      bottom: 8%;
      transform: rotate(7deg);
      animation: heroFloat 8.6s ease-in-out infinite;
      z-index: 1;
    }
    .motion-tag {
      position: absolute;
      right: 20px;
      bottom: 20px;
      padding: 12px 14px;
      border-radius: 16px;
      background: rgba(255,255,255,0.72);
      border: 1px solid rgba(255,255,255,0.66);
      font-size: 12px;
      letter-spacing: 0.14em;
      text-transform: uppercase;
      color: var(--muted);
      z-index: 4;
      box-shadow: var(--shadow-soft);
    }
    .marquee {
      margin-top: 18px;
      border-radius: 24px;
      overflow: hidden;
      padding: 14px 0;
    }
    .marquee-track {
      display: flex;
      width: max-content;
      gap: 28px;
      white-space: nowrap;
      animation: railMove 18s linear infinite;
      padding-left: 20px;
      font-weight: 700;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      color: #8e5863;
      font-size: 12px;
    }
    .manifesto {
      margin-top: 18px;
      border-radius: 32px;
      padding: 24px 26px;
      display: grid;
      grid-template-columns: 0.96fr 1.04fr;
      gap: 20px;
      align-items: center;
    }
    .manifesto h2,
    .section-head h2,
    .spotlight h2,
    .ritual h2 {
      margin: 0;
      font-family: Georgia, serif;
      letter-spacing: -0.04em;
    }
    .manifesto h2 { font-size: clamp(34px, 4vw, 50px); }
    .manifesto p {
      margin: 0;
      color: var(--muted);
      line-height: 1.78;
    }
    .section-head {
      display: flex;
      justify-content: space-between;
      gap: 20px;
      align-items: end;
      margin: 42px 4px 18px;
    }
    .section-head h2 { font-size: clamp(38px, 4vw, 58px); }
    .section-head p {
      margin: 0;
      max-width: 450px;
      color: var(--muted);
      line-height: 1.75;
    }
    .products {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 18px;
    }
    .product-card {
      border-radius: 32px;
      padding: 18px;
      background: rgba(255,255,255,0.74);
      border: 1px solid rgba(255,255,255,0.74);
      box-shadow: var(--shadow);
      transform: translateY(0);
      transition: transform 0.45s ease, box-shadow 0.45s ease;
    }
    .product-card:hover {
      transform: translateY(-10px);
      box-shadow: 0 44px 120px rgba(61, 41, 45, 0.18);
    }
    .product-shell {
      position: relative;
      border-radius: 24px;
      overflow: hidden;
      background: rgba(255,255,255,0.86);
      aspect-ratio: 5 / 6;
      margin-bottom: 16px;
    }
    .product-aura {
      position: absolute;
      inset: auto;
      width: 60%;
      height: 24%;
      left: 20%;
      bottom: 5%;
      border-radius: 999px;
      background: radial-gradient(circle, rgba(215,143,154,0.18), transparent 72%);
      animation: auraPulse 5.2s ease-in-out infinite;
    }
    .product-frame {
      position: relative;
      width: 100%;
      height: 100%;
      z-index: 1;
    }
    .product-frame img {
      width: 100%;
      height: 100%;
      object-fit: cover;
      display: block;
    }
    .step {
      margin: 0 0 8px;
      color: #9c5a66;
      font-size: 12px;
      letter-spacing: 0.18em;
      text-transform: uppercase;
    }
    .product-copy h3 {
      margin: 0 0 8px;
      font-family: Georgia, serif;
      font-size: 30px;
      line-height: 1.04;
    }
    .product-copy p {
      margin: 0 0 14px;
      color: var(--muted);
      line-height: 1.72;
    }
    .story {
      color: var(--ink);
      font-weight: 600;
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
      color: var(--ink);
    }
    .row button {
      border: none;
      border-radius: 999px;
      padding: 12px 18px;
      background: var(--ink);
      color: #fff;
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
    .spotlight h2 { font-size: clamp(34px, 4vw, 48px); }
    .spotlight p {
      margin: 0 0 14px;
      color: var(--muted);
      line-height: 1.78;
    }
    .benefits {
      list-style: none;
      margin: 10px 0 0;
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
    .ritual {
      margin-top: 22px;
      border-radius: 34px;
      padding: 24px;
    }
    .ritual-header {
      display: flex;
      justify-content: space-between;
      gap: 20px;
      align-items: end;
      margin-bottom: 18px;
    }
    .ritual-header h2 { font-size: clamp(34px, 4vw, 48px); }
    .ritual-header p {
      margin: 0;
      max-width: 500px;
      color: var(--muted);
      line-height: 1.78;
    }
    .ritual-grid {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 16px;
    }
    .ritual-step {
      border-radius: 24px;
      padding: 20px;
      background: rgba(255,255,255,0.74);
      border: 1px solid var(--line);
      box-shadow: var(--shadow-soft);
    }
    .ritual-step strong {
      display: block;
      margin-bottom: 10px;
      color: #9c5a66;
      letter-spacing: 0.18em;
      font-size: 12px;
    }
    .ritual-step h4 {
      margin: 0 0 8px;
      font-family: Georgia, serif;
      font-size: 28px;
      line-height: 1.06;
    }
    .ritual-step p {
      margin: 0;
      color: var(--muted);
      line-height: 1.72;
    }
    footer {
      margin-top: 24px;
      border-radius: 30px;
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
    .reveal {
      opacity: 0;
      transform: translateY(22px);
      transition: opacity 0.8s ease, transform 0.8s ease;
    }
    .reveal.is-visible {
      opacity: 1;
      transform: translateY(0);
    }
    @keyframes heroFloat {
      0% { transform: translateY(0px) rotate(0deg); }
      50% { transform: translateY(-14px) rotate(1.2deg); }
      100% { transform: translateY(0px) rotate(0deg); }
    }
    @keyframes heroFloatAlt {
      0% { transform: translateY(0px) rotate(-7deg); }
      50% { transform: translateY(-12px) rotate(-4deg); }
      100% { transform: translateY(0px) rotate(-7deg); }
    }
    @keyframes auraDrift {
      0% { transform: translate3d(0, 0, 0) scale(1); }
      100% { transform: translate3d(1.5%, -1.5%, 0) scale(1.04); }
    }
    @keyframes shineSweep {
      0% { transform: translateX(-120%); }
      100% { transform: translateX(120%); }
    }
    @keyframes pulseHalo {
      0%, 100% { box-shadow: 0 0 0 9px rgba(215,143,154,0.12); }
      50% { box-shadow: 0 0 0 15px rgba(215,143,154,0.06); }
    }
    @keyframes haloFloat {
      0% { transform: translateY(0px) scale(1); opacity: 0.8; }
      50% { transform: translateY(-10px) scale(1.05); opacity: 1; }
      100% { transform: translateY(0px) scale(1); opacity: 0.8; }
    }
    @keyframes railMove {
      0% { transform: translateX(0); }
      100% { transform: translateX(-30%); }
    }
    @keyframes slowLift {
      0%, 100% { transform: translateY(0px); }
      50% { transform: translateY(-6px); }
    }
    @keyframes auraPulse {
      0%, 100% { opacity: 0.45; transform: scale(1); }
      50% { opacity: 0.8; transform: scale(1.06); }
    }
    @media (max-width: 1080px) {
      .hero, .manifesto, .spotlight, .products, .ritual-grid { grid-template-columns: 1fr; }
      .section-head, .ritual-header, footer { display: block; }
      .hero-stage { min-height: 560px; }
      footer p { margin: 8px 0 0; }
    }
  </style>
</head>
<body>
  <div class="ambient"></div>
  <div class="shell">
    <header class="nav reveal is-visible">
      <div class="wordmark"><span class="seed"></span><strong>__BRAND__</strong></div>
      <div class="nav-meta"><span>__POSITIONING__</span><button class="bag" type="button">Bag (3)</button></div>
    </header>
    <section class="hero reveal is-visible">
      <div>
        <span class="eyebrow">__BADGE__</span>
        <h1>__HERO_TITLE__</h1>
        <p class="lede">__HERO_BODY__</p>
        <p class="sublede">__LAUNCH_PHRASE__</p>
        <div class="hero-actions">
          <button class="primary" type="button">__PRIMARY_CTA__</button>
          <a class="secondary" href="#collection">__SECONDARY_CTA__</a>
        </div>
        <div class="micro-grid">
          <article class="micro-card"><strong>__AURA_LABEL__</strong><span>__MOTION_TAGLINE__</span></article>
          <article class="micro-card"><strong>__SEQUENCE_LABEL__</strong><span>__MOTION_CONCEPT__</span></article>
          <article class="micro-card"><strong>__SHIMMER_LABEL__</strong><span>__HOVER_PHRASE__</span></article>
        </div>
      </div>
      <div class="hero-stage" id="hero-stage">
        <img class="product center" src="__HERO_SRC__" alt="__HERO_ALT__" />
        <img class="product left" src="__LEFT_SRC__" alt="__LEFT_ALT__" />
        <img class="product right" src="__RIGHT_SRC__" alt="__RIGHT_ALT__" />
        <div class="motion-tag">__TEXTURE_LABEL__</div>
      </div>
    </section>
    <section class="marquee reveal">
      <div class="marquee-track">
        <span>__MARQUEE__</span><span>__RAIL_PHRASE__</span><span>__VISUAL_AXIS__</span><span>__MARQUEE__</span><span>__RAIL_PHRASE__</span><span>__VISUAL_AXIS__</span>
      </div>
    </section>
    <section class="manifesto reveal">
      <h2>__MANIFESTO_TITLE__</h2>
      <div>
        <p>__MANIFESTO_BODY__</p>
        <p style="margin-top:14px;"><strong style="color:var(--ink);">__MOODLINE__</strong></p>
      </div>
    </section>
    <div class="section-head">
      <div>
        <h2 id="collection">__SECTION_TITLE__</h2>
      </div>
      <p>__SECTION_BODY__</p>
    </div>
    <section class="products">
      __CARDS__
    </section>
    <section class="spotlight reveal">
      <div>
        <h2>__SPOTLIGHT_TITLE__</h2>
      </div>
      <div>
        <p>__SPOTLIGHT_BODY__</p>
        <p>__DETAIL_NOTE__</p>
        <ul class="benefits">__BENEFITS__</ul>
      </div>
    </section>
    <section class="ritual reveal">
      <div class="ritual-header">
        <div>
          <h2>__RITUAL_TITLE__</h2>
        </div>
        <p>__RITUAL_BODY__</p>
      </div>
      <div class="ritual-grid">__RITUAL_STEPS__</div>
    </section>
    <footer class="reveal">
      <strong>__BRAND__</strong>
      <p>__FOOTER_NOTE__</p>
    </footer>
  </div>
  <script>
    (function () {
      const revealItems = document.querySelectorAll('.reveal');
      const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('is-visible');
          }
        });
      }, { threshold: 0.16 });
      revealItems.forEach((item) => observer.observe(item));

      const stage = document.getElementById('hero-stage');
      if (!stage) return;

      stage.addEventListener('mousemove', (event) => {
        const rect = stage.getBoundingClientRect();
        const x = (event.clientX - rect.left) / rect.width - 0.5;
        const y = (event.clientY - rect.top) / rect.height - 0.5;
        const center = stage.querySelector('.center');
        const left = stage.querySelector('.left');
        const right = stage.querySelector('.right');
        if (center) center.style.transform = `translate(${x * 10}px, ${y * 12}px)`;
        if (left) left.style.transform = `translate(${x * -12}px, ${y * 8}px) rotate(-7deg)`;
        if (right) right.style.transform = `translate(${x * 12}px, ${y * -8}px) rotate(7deg)`;
      });

      stage.addEventListener('mouseleave', () => {
        const items = stage.querySelectorAll('.product');
        items.forEach((item) => { item.style.transform = ''; });
      });
    }());
  </script>
</body>
</html>
"""

html = html.replace("__BRAND__", brand)
html = html.replace("__POSITIONING__", final_copy["positioning"])
html = html.replace("__BADGE__", final_copy["badge"])
html = html.replace("__HERO_TITLE__", final_copy["hero_title"])
html = html.replace("__HERO_BODY__", final_copy["hero_body"])
html = html.replace("__LAUNCH_PHRASE__", final_copy["launch_phrase"])
html = html.replace("__PRIMARY_CTA__", final_copy["primary_cta"])
html = html.replace("__SECONDARY_CTA__", final_copy["secondary_cta"])
html = html.replace("__AURA_LABEL__", final_copy["aura_label"])
html = html.replace("__SEQUENCE_LABEL__", final_copy["sequence_label"])
html = html.replace("__SHIMMER_LABEL__", final_copy["shimmer_label"])
html = html.replace("__MOTION_TAGLINE__", final_copy["motion_tagline"])
html = html.replace("__MOTION_CONCEPT__", final_copy["motion_concept"])
html = html.replace("__HOVER_PHRASE__", final_copy["hover_phrase"])
html = html.replace("__TEXTURE_LABEL__", final_copy["texture_label"])
html = html.replace("__MARQUEE__", final_copy["marquee"])
html = html.replace("__RAIL_PHRASE__", final_copy["rail_phrase"])
html = html.replace("__VISUAL_AXIS__", final_copy["visual_axis"])
html = html.replace("__MANIFESTO_TITLE__", final_copy["manifesto_title"])
html = html.replace("__MANIFESTO_BODY__", final_copy["manifesto_body"])
html = html.replace("__MOODLINE__", final_copy["moodline"])
html = html.replace("__SECTION_TITLE__", final_copy["section_title"])
html = html.replace("__SECTION_BODY__", final_copy["section_body"])
html = html.replace("__SPOTLIGHT_TITLE__", final_copy["spotlight_title"])
html = html.replace("__SPOTLIGHT_BODY__", final_copy["spotlight_body"])
html = html.replace("__DETAIL_NOTE__", final_copy["detail_note"])
html = html.replace("__RITUAL_TITLE__", final_copy["ritual_title"])
html = html.replace("__RITUAL_BODY__", final_copy["ritual_body"])
html = html.replace("__FOOTER_NOTE__", final_copy["footer_note"])
html = html.replace("__CARDS__", "".join(cards_html))
html = html.replace("__BENEFITS__", benefits_html)
html = html.replace("__RITUAL_STEPS__", ritual_steps_html)
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
    html.count("data:image/svg+xml") >= 6,
    "IntersectionObserver" in html,
    "@keyframes heroFloat" in html,
]

score = sum(1 for item in checks if item) / len(checks)

result = {
    "output": html,
    "score": score,
}

import json
import re
import textwrap
from html import escape
from string import Template
from urllib.parse import quote


SEASONAL_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 240" fill="none">
  <circle cx="120" cy="120" r="110" fill="#F5F0EB"/>
  <ellipse cx="120" cy="186" rx="58" ry="8" fill="#3B2314" opacity="0.08"/>
  <path d="M78 112 C78 82 98 64 120 64 C142 64 162 82 162 112 C162 142 146 170 120 188 C94 170 78 142 78 112 Z" fill="#C07A5A" opacity="0.92"/>
  <path d="M96 116 C96 100 106 88 120 88 C134 88 144 100 144 116 C144 132 134 144 120 156 C106 144 96 132 96 116 Z" fill="#F5F0EB" opacity="0.72"/>
  <circle cx="120" cy="116" r="20" fill="#3B2314" opacity="0.92"/>
  <path d="M120 44 C126 58 136 68 150 76" stroke="#C07A5A" stroke-width="3" stroke-linecap="round" opacity="0.5"/>
  <path d="M90 80 C104 72 114 62 120 48" stroke="#C07A5A" stroke-width="3" stroke-linecap="round" opacity="0.35"/>
</svg>
""".strip()


def compact_text(value):
    text = str(value or "").strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    text = text.replace("\u2014", "-")
    text = re.sub(r"\s+", " ", text)
    return text.strip(" \n\"'")


def split_sections(markdown):
    sections = {}
    if not markdown:
        return sections
    matches = list(re.finditer(r"^##\s+(.+?)\s*$", markdown, re.M))
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(markdown)
        sections[match.group(1).strip()] = markdown[start:end].strip()
    return sections


def extract_inline(section, label, default=""):
    pattern = r"\*\*" + re.escape(label) + r":\*\*\s*(.+)"
    match = re.search(pattern, section or "")
    return compact_text(match.group(1)) if match else default


def extract_block(section, label, default=""):
    pattern = r"\*\*" + re.escape(label) + r":\*\*\s*(.*?)(?:\n\s*\n|\Z)"
    match = re.search(pattern, section or "", re.S)
    if not match:
        return default
    lines = [line.strip() for line in match.group(1).splitlines() if line.strip()]
    return compact_text(" ".join(lines))


def extract_bullets(section, label):
    pattern = r"\*\*" + re.escape(label) + r":\*\*\s*((?:\n(?:- |\d+\. ).+)+)"
    match = re.search(pattern, section or "")
    if not match:
        return []
    lines = []
    for raw_line in match.group(1).splitlines():
        line = raw_line.strip()
        if line.startswith("- "):
            lines.append(compact_text(line[2:]))
        else:
            numbered = re.match(r"\d+\.\s+(.+)", line)
            if numbered:
                lines.append(compact_text(numbered.group(1)))
    return lines


def parse_catalog_item(line):
    parts = re.split(r"\s+[—-]\s+", line, maxsplit=1)
    left = compact_text(parts[0])
    price = compact_text(parts[1]) if len(parts) > 1 else ""
    detail = ""
    detail_match = re.match(r"(.+?)\s*\((.+)\)\s*$", left)
    if detail_match:
        left = compact_text(detail_match.group(1))
        detail = compact_text(detail_match.group(2))
    return {"name": left, "detail": detail, "price": price}


def parse_brief(markdown):
    sections = split_sections(markdown)
    brand_section = sections.get("Brand Information", "")
    target_section = sections.get("Target Audience", "")
    menu_section = sections.get("Menu Lineup", "")
    design_section = sections.get("Design Direction", "")
    page_section = sections.get("Page Structure", "")
    special_section = sections.get("Special Requirements", "")

    palette_text = " ".join(extract_bullets(design_section, "Color Palette"))
    palette_hexes = re.findall(r"#[0-9A-Fa-f]{6}", palette_text)
    bg = palette_hexes[0] if len(palette_hexes) > 0 else "#F5F0EB"
    ink = palette_hexes[1] if len(palette_hexes) > 1 else "#3B2314"
    accent = palette_hexes[2] if len(palette_hexes) > 2 else "#C07A5A"

    signature_items = [parse_catalog_item(line) for line in extract_bullets(menu_section, "Signature Menu")]
    goods_items = [parse_catalog_item(line) for line in extract_bullets(menu_section, "Beans & Goods")]
    keywords = [compact_text(item) for item in extract_inline(design_section, "Keywords").split(",") if compact_text(item)]
    required_sections = [compact_text(item) for item in extract_bullets(page_section, "Required Sections (in order)")]
    brand_name = extract_inline(brand_section, "Brand Name", "Grain & Ground")
    location = extract_inline(brand_section, "Location", "Seongsu-dong, Seoul")
    location_short = location.split(",")[0].strip() if location else "Seongsu-dong"

    return {
        "brand_name": brand_name,
        "slogan": extract_inline(brand_section, "Slogan", "Every cup has a story."),
        "industry": extract_inline(brand_section, "Industry", "Specialty coffee cafe"),
        "business_type": extract_inline(brand_section, "Business Type", "Cafe and online beans"),
        "location": location,
        "location_short": location_short,
        "founded": extract_inline(brand_section, "Founded", "2021"),
        "brand_description": extract_block(brand_section, "Brand Description"),
        "primary_target": extract_inline(target_section, "Primary Target"),
        "target_profile": extract_inline(target_section, "Profile"),
        "signature_items": signature_items,
        "goods_items": goods_items,
        "keywords": keywords,
        "mood": extract_block(design_section, "Mood"),
        "reference": extract_inline(design_section, "Reference"),
        "page_type": extract_inline(page_section, "Page Type"),
        "required_sections": required_sections,
        "language": extract_inline(special_section, "Language", "English"),
        "animation": extract_inline(special_section, "Animation", "Subtle fade-in on scroll"),
        "responsive": extract_inline(special_section, "Responsive", "Mobile-first"),
        "notes": extract_block(special_section, "Other"),
        "colors": {"bg": bg, "ink": ink, "accent": accent},
    }


def hex_to_rgb_string(hex_value, fallback):
    code = str(hex_value or "").strip().lstrip("#")
    if len(code) != 6 or re.search(r"[^0-9A-Fa-f]", code):
        return fallback
    return ", ".join(str(int(code[index:index + 2], 16)) for index in (0, 2, 4))


def slugify(value):
    cleaned = re.sub(r"[^a-z0-9]+", "-", (value or "").lower())
    return cleaned.strip("-") or "brand"


def brand_initials(value):
    letters = re.findall(r"[A-Za-z]+", value or "")
    initials = "".join(item[0] for item in letters[:2]).upper()
    return initials or "G"


def extract_json_object(text):
    cleaned = str(text or "").strip()
    try:
        return json.loads(cleaned)
    except Exception:
        pass
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(cleaned[start:end + 1])
        except Exception:
            return {}
    return {}


def normalize_list(candidate, fallback, size):
    values = candidate if isinstance(candidate, list) else []
    output = []
    for index in range(size):
        raw = values[index] if index < len(values) else fallback[index]
        output.append(compact_text(raw or fallback[index]))
    return output


def normalize_copy_pack(candidate, fallback, menu_count):
    scalar_keys = [
        "hero_eyebrow",
        "hero_body",
        "story_title",
        "story_body",
        "menu_intro",
        "beans_title",
        "beans_body",
        "beans_cta_label",
        "store_title",
        "store_body",
        "hours_label",
        "visit_note",
        "footer_tagline",
        "instagram_title",
        "instagram_body",
        "meta_title",
        "meta_description",
    ]
    normalized = {}
    for key in scalar_keys:
        normalized[key] = compact_text(candidate.get(key) or fallback[key])
    normalized["menu_descriptions"] = normalize_list(
        candidate.get("menu_descriptions"),
        fallback["menu_descriptions"],
        menu_count,
    )
    normalized["beans_highlights"] = normalize_list(
        candidate.get("beans_highlights"),
        fallback["beans_highlights"],
        3,
    )
    normalized["instagram_labels"] = normalize_list(
        candidate.get("instagram_labels"),
        fallback["instagram_labels"],
        4,
    )
    return normalized


def build_fallback_copy(brief):
    menu_fallbacks = []
    for item in brief["signature_items"]:
        name = item["name"].lower()
        detail = item["detail"]
        if "drip" in name:
            menu_fallbacks.append("Clean floral aromatics and a bright, tea-like finish that rewards a slower sip.")
        elif "tonic" in name:
            menu_fallbacks.append("Dark cold brew lifted by sparkling citrus bite and a crisp, refreshing finish.")
        elif "latte" in name:
            menu_fallbacks.append("House blend espresso folded into silky milk for a balanced, everyday cup.")
        elif "seasonal" in name:
            menu_fallbacks.append("A rotating quarterly special that keeps the menu expressive and the bar playful.")
        else:
            base = "A composed house favorite built around clarity, balance, and ingredient character."
            if detail:
                base = detail + ". " + base
            menu_fallbacks.append(base)

    while len(menu_fallbacks) < len(brief["signature_items"]):
        menu_fallbacks.append("A composed house favorite built around clarity, balance, and ingredient character.")

    return {
        "hero_eyebrow": brief["location_short"],
        "hero_body": (
            "Small-batch roasting, origin-led drinks, and a calm Seoul rhythm "
            "for people who care how coffee is sourced and served."
        ),
        "story_title": "Coffee that lets origin speak first.",
        "story_body": (
            "Grain & Ground is a specialty cafe tucked into the alleys of Seongsu-dong. "
            "Green beans are sourced directly, roasted in small batches, and brewed in ways "
            "that keep each origin clear, honest, and easy to return to."
        ),
        "menu_intro": (
            "A short list of signature drinks shaped by clarity, balance, and the natural color "
            "of each origin."
        ),
        "menu_descriptions": menu_fallbacks,
        "beans_title": "Bring the roastery home.",
        "beans_body": (
            "Pick up house-roasted bags, easy drip kits, and understated goods designed for "
            "daily brewing, gifting, and slower mornings."
        ),
        "beans_highlights": [
            "Direct-sourcing mindset with small-batch roasting.",
            "Formats for both home brewers and easy desk-side coffee.",
            "Quiet essentials that match the cafe's warm visual language.",
        ],
        "beans_cta_label": "Order Beans and Goods",
        "store_title": "Visit the alley, stay for the detail.",
        "store_body": (
            "Designed for espresso stops, slower hand-drip moments, and bean pick-ups between "
            "meetings in Seongsu."
        ),
        "hours_label": "Daily 11:00 - 20:00",
        "visit_note": "Directions and seasonal updates can be checked before you head over.",
        "footer_tagline": "Roasted in small batches. Poured with intention.",
        "instagram_title": "A feed-ready corner of the brand.",
        "instagram_body": (
            "Use the placeholder tiles for launches, quiet bar moments, and future interior "
            "photography once the live feed is connected."
        ),
        "instagram_labels": [
            "Morning prep",
            "Bar detail",
            "Fresh roast",
            "Weekend rhythm",
        ],
        "meta_title": brief["brand_name"] + " | Specialty Coffee in Seongsu",
        "meta_description": (
            brief["brand_name"] + " is a warm specialty coffee destination in Seongsu-dong, "
            "serving origin-led drinks and small-batch roasted beans."
        ),
    }


def request_copy_pack(brief, fallback, quality_guide, model, reviewer_model, temperature, max_tokens):
    prompt_brief = {
        "brand_name": brief["brand_name"],
        "slogan": brief["slogan"],
        "industry": brief["industry"],
        "business_type": brief["business_type"],
        "location": brief["location"],
        "founded": brief["founded"],
        "brand_description": brief["brand_description"],
        "primary_target": brief["primary_target"],
        "target_profile": brief["target_profile"],
        "signature_items": brief["signature_items"],
        "goods_items": brief["goods_items"],
        "keywords": brief["keywords"],
        "mood": brief["mood"],
        "reference": brief["reference"],
        "required_sections": brief["required_sections"],
        "special_requirements": {
            "language": brief["language"],
            "animation": brief["animation"],
            "responsive": brief["responsive"],
            "other": brief["notes"],
        },
        "known_missing_details": [
            "No confirmed store URL",
            "No confirmed social handle",
            "No confirmed email address",
            "No confirmed operating hours",
        ],
    }

    schema_guide = {
        "hero_eyebrow": "short location label",
        "hero_body": "1 concise paragraph",
        "story_title": "short section headline",
        "story_body": "1 paragraph, 40-70 words",
        "menu_intro": "1 sentence",
        "menu_descriptions": ["1 line per signature item"],
        "beans_title": "short headline",
        "beans_body": "1 paragraph",
        "beans_highlights": ["3 short bullets"],
        "beans_cta_label": "3-5 words",
        "store_title": "short headline",
        "store_body": "1 paragraph",
        "hours_label": "tasteful fallback if missing",
        "visit_note": "1 concise sentence",
        "footer_tagline": "short closing line",
        "instagram_title": "short headline",
        "instagram_body": "1 concise paragraph",
        "instagram_labels": ["4 short tile labels"],
        "meta_title": "under 70 chars",
        "meta_description": "under 160 chars",
    }

    draft = fallback
    try:
        copy_messages = [
            {
                "role": "system",
                "content": agent_prompt
                + "\n\nWrite only the copy pack for the landing page. Return valid JSON and nothing else.",
            },
            {
                "role": "user",
                "content": textwrap.dedent(
                    """
                    Create a premium but restrained copy pack for a single-scroll coffee landing page.

                    Brief:
                    $brief_json

                    Quality guide:
                    $quality_guide

                    Rules:
                    - English only.
                    - Keep the tone warm, precise, and calm.
                    - No hype, no fake testimonials, no invented awards.
                    - Do not invent phone numbers or street numbers.
                    - If an operational detail is missing, keep it tasteful and generic.
                    - Keep menu descriptions concrete and concise.
                    - Return valid JSON only.

                    Required JSON schema:
                    $schema_json
                    """
                )
                .strip()
                .replace("$brief_json", json.dumps(prompt_brief, ensure_ascii=False, indent=2))
                .replace("$quality_guide", quality_guide or "Keep the page timeless, typography-led, and gently premium.")
                .replace("$schema_json", json.dumps(schema_guide, ensure_ascii=False, indent=2)),
            },
        ]
        response = llm.chat(
            copy_messages,
            model=model,
            temperature=min(max(temperature, 0.25), 0.55),
            max_tokens=max_tokens,
        )
        parsed = extract_json_object(response.get("content", ""))
        draft = normalize_copy_pack(parsed, fallback, len(brief["signature_items"]))
    except Exception:
        draft = normalize_copy_pack({}, fallback, len(brief["signature_items"]))

    try:
        review_messages = [
            {
                "role": "system",
                "content": (
                    "You are a creative director reviewing website copy. Improve the copy only if it becomes "
                    "clearer, calmer, more accurate, and better aligned to the brief. Return valid JSON only."
                ),
            },
            {
                "role": "user",
                "content": textwrap.dedent(
                    """
                    Review this draft copy pack against the brief and quality guide.
                    Keep the same keys and the same overall structure.

                    Brief:
                    $brief_json

                    Quality guide:
                    $quality_guide

                    Draft copy pack:
                    $draft_json
                    """
                )
                .strip()
                .replace("$brief_json", json.dumps(prompt_brief, ensure_ascii=False, indent=2))
                .replace("$quality_guide", quality_guide or "Keep the page timeless, typography-led, and gently premium.")
                .replace("$draft_json", json.dumps(draft, ensure_ascii=False, indent=2)),
            },
        ]
        reviewed = llm.chat(
            review_messages,
            model=reviewer_model,
            temperature=0.15,
            max_tokens=max_tokens,
        )
        parsed_review = extract_json_object(reviewed.get("content", ""))
        return normalize_copy_pack(parsed_review, draft, len(brief["signature_items"]))
    except Exception:
        return draft


def asset_for_item(item, assets, index):
    name = item["name"].lower()
    if "tonic" in name:
        return assets.get("cold-brew-tonic", "")
    if "latte" in name:
        return assets.get("signature-latte", "")
    if "seasonal" in name:
        return SEASONAL_SVG
    if "espresso" in name or "drip" in name or "coffee" in name:
        return assets.get("espresso-cup", "")
    ordered = [
        assets.get("espresso-cup", ""),
        assets.get("cold-brew-tonic", ""),
        assets.get("signature-latte", ""),
        SEASONAL_SVG,
    ]
    return ordered[index] if index < len(ordered) and ordered[index] else SEASONAL_SVG


def safe_svg(svg_markup):
    svg_text = str(svg_markup or "").strip()
    return svg_text if svg_text.startswith("<svg") else SEASONAL_SVG


def render_menu_cards(items, copy_pack, assets):
    cards = []
    card_template = Template(
        """
        <article class="menu-card reveal">
          <div class="card-visual" aria-hidden="true">$svg</div>
          <div class="card-copy">
            <div class="card-meta">$detail</div>
            <h3>$name</h3>
            <p>$description</p>
          </div>
          <div class="card-price">$price</div>
        </article>
        """
    )
    for index, item in enumerate(items):
        detail = item["detail"] or ("Quarterly Rotation" if "seasonal" in item["name"].lower() else "Signature Pour")
        description = copy_pack["menu_descriptions"][index] if index < len(copy_pack["menu_descriptions"]) else ""
        cards.append(
            card_template.safe_substitute(
                svg=safe_svg(asset_for_item(item, assets, index)),
                detail=escape(detail),
                name=escape(item["name"]),
                description=escape(description),
                price=escape(item["price"] or "Ask In Store"),
            )
        )
    return "\n".join(cards)


def render_goods_list(goods_items):
    rows = []
    row_template = Template(
        """
        <div class="goods-row">
          <div>
            <strong>$name</strong>
            <span>$detail</span>
          </div>
          <em>$price</em>
        </div>
        """
    )
    for item in goods_items:
        detail = item["detail"] or "House selection"
        rows.append(
            row_template.safe_substitute(
                name=escape(item["name"]),
                detail=escape(detail),
                price=escape(item["price"] or "Inquire"),
            )
        )
    return "\n".join(rows)


def render_keyword_pills(keywords):
    return "".join('<span class="pill">' + escape(keyword) + "</span>" for keyword in keywords[:4])


def render_highlights(highlights):
    return "".join("<li>" + escape(item) + "</li>" for item in highlights[:3])


def render_feed_tiles(labels):
    tiles = []
    for label in labels[:4]:
        tiles.append(
            '<div class="feed-tile reveal"><span>' + escape(label) + "</span></div>"
        )
    return "\n".join(tiles)


def build_html(brief, copy_pack, assets):
    colors = brief["colors"]
    accent_rgb = hex_to_rgb_string(colors["accent"], "192, 122, 90")
    ink_rgb = hex_to_rgb_string(colors["ink"], "59, 35, 20")
    brand_slug = slugify(brief["brand_name"]).replace("-", "")
    store_url = "https://search.shopping.naver.com/search/all?query=" + quote(brief["brand_name"] + " coffee beans")
    map_url = "https://www.google.com/maps/search/?api=1&query=" + quote(brief["location"])
    instagram_url = "https://www.instagram.com/" + brand_slug + "/"
    email_address = "hello@" + brand_slug + ".kr"
    mark = brand_initials(brief["brand_name"])

    hero_assets = [
        safe_svg(assets.get("espresso-cup", "")),
        safe_svg(assets.get("signature-latte", "")),
        safe_svg(assets.get("cold-brew-tonic", "")),
    ]

    facts = [
        brief["founded"],
        "Single Seoul location",
        "Small-batch roasted",
    ]
    fact_markup = "".join("<li>" + escape(item) + "</li>" for item in facts if item)

    template = Template(
        textwrap.dedent(
            """
            <!DOCTYPE html>
            <html lang="en">
            <head>
              <meta charset="utf-8" />
              <meta name="viewport" content="width=device-width, initial-scale=1" />
              <title>$meta_title</title>
              <meta name="description" content="$meta_description" />
              <meta name="theme-color" content="$accent" />
              <link rel="preconnect" href="https://fonts.googleapis.com" />
              <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
              <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap" rel="stylesheet" />
              <style>
                :root {
                  --bg: $bg;
                  --ink: $ink;
                  --accent: $accent;
                  --accent-rgb: $accent_rgb;
                  --ink-rgb: $ink_rgb;
                  --paper: rgba(255, 252, 249, 0.72);
                  --panel: rgba(255, 249, 244, 0.8);
                  --line: rgba($ink_rgb, 0.12);
                  --shadow: 0 24px 60px rgba($ink_rgb, 0.10);
                  --radius-lg: 28px;
                  --radius-md: 20px;
                  --radius-sm: 14px;
                }

                * {
                  box-sizing: border-box;
                }

                html {
                  scroll-behavior: smooth;
                }

                body {
                  margin: 0;
                  background:
                    radial-gradient(circle at top left, rgba($accent_rgb, 0.14), transparent 34%),
                    radial-gradient(circle at 85% 15%, rgba($ink_rgb, 0.05), transparent 26%),
                    linear-gradient(180deg, #fbf7f2 0%, var(--bg) 42%, #f2ece6 100%);
                  color: var(--ink);
                  font-family: "Manrope", "Avenir Next", "Segoe UI", sans-serif;
                  line-height: 1.55;
                  min-width: 320px;
                }

                body::before {
                  content: "";
                  position: fixed;
                  inset: 0;
                  pointer-events: none;
                  background-image:
                    radial-gradient(rgba($ink_rgb, 0.06) 0.7px, transparent 0.7px);
                  background-size: 18px 18px;
                  opacity: 0.16;
                  mix-blend-mode: multiply;
                }

                a {
                  color: inherit;
                  text-decoration: none;
                }

                img,
                svg {
                  display: block;
                  max-width: 100%;
                }

                .page-shell {
                  position: relative;
                  max-width: 1320px;
                  margin: 0 auto;
                  padding: 20px 20px 36px;
                }

                .nav {
                  display: flex;
                  align-items: center;
                  justify-content: space-between;
                  gap: 20px;
                  padding: 14px 0 26px;
                }

                .brand-lockup {
                  display: inline-flex;
                  align-items: center;
                  gap: 12px;
                  font-weight: 800;
                  letter-spacing: 0.08em;
                  text-transform: uppercase;
                  font-size: 0.82rem;
                }

                .brand-lockup strong {
                  display: grid;
                  place-items: center;
                  width: 40px;
                  height: 40px;
                  border-radius: 999px;
                  background: rgba($ink_rgb, 0.92);
                  color: var(--bg);
                  font-family: "Cormorant Garamond", Georgia, serif;
                  font-size: 1.15rem;
                  letter-spacing: 0;
                }

                .nav-links {
                  display: none;
                  align-items: center;
                  gap: 18px;
                  font-size: 0.94rem;
                }

                .nav-links a:last-child {
                  padding: 10px 14px;
                  border: 1px solid rgba($ink_rgb, 0.14);
                  border-radius: 999px;
                  background: rgba(255, 255, 255, 0.48);
                  backdrop-filter: blur(10px);
                }

                .hero {
                  position: relative;
                  padding: 8px 0 36px;
                }

                .hero-grid {
                  display: grid;
                  gap: 30px;
                  align-items: center;
                }

                .hero-copy {
                  position: relative;
                  z-index: 1;
                }

                .eyebrow {
                  display: inline-flex;
                  align-items: center;
                  gap: 8px;
                  margin: 0 0 14px;
                  color: rgba($ink_rgb, 0.76);
                  text-transform: uppercase;
                  letter-spacing: 0.16em;
                  font-size: 0.78rem;
                  font-weight: 800;
                }

                .eyebrow::before {
                  content: "";
                  width: 34px;
                  height: 1px;
                  background: rgba($ink_rgb, 0.34);
                }

                .brand-name {
                  margin: 0;
                  font-family: "Cormorant Garamond", Georgia, serif;
                  font-size: clamp(3.2rem, 12vw, 7rem);
                  line-height: 0.92;
                  letter-spacing: -0.04em;
                }

                .slogan {
                  margin: 10px 0 0;
                  font-family: "Cormorant Garamond", Georgia, serif;
                  font-size: clamp(1.35rem, 4vw, 2.3rem);
                  line-height: 1.02;
                  letter-spacing: -0.02em;
                  max-width: 11ch;
                }

                .hero-body {
                  max-width: 34rem;
                  margin: 24px 0 0;
                  font-size: 1.02rem;
                  color: rgba($ink_rgb, 0.82);
                }

                .cta-row {
                  display: flex;
                  flex-wrap: wrap;
                  gap: 12px;
                  margin-top: 28px;
                }

                .button {
                  display: inline-flex;
                  align-items: center;
                  justify-content: center;
                  min-height: 48px;
                  padding: 0 18px;
                  border-radius: 999px;
                  border: 1px solid transparent;
                  font-weight: 700;
                  font-size: 0.96rem;
                  transition: transform 220ms ease, box-shadow 220ms ease, background 220ms ease;
                }

                .button:hover {
                  transform: translateY(-1px);
                }

                .button.primary {
                  background: var(--ink);
                  color: var(--bg);
                  box-shadow: 0 18px 30px rgba($ink_rgb, 0.16);
                }

                .button.secondary {
                  background: rgba(255, 255, 255, 0.52);
                  color: var(--ink);
                  border-color: rgba($ink_rgb, 0.12);
                  backdrop-filter: blur(12px);
                }

                .fact-row {
                  display: flex;
                  flex-wrap: wrap;
                  gap: 10px;
                  list-style: none;
                  padding: 0;
                  margin: 28px 0 0;
                }

                .fact-row li,
                .pill {
                  padding: 9px 12px;
                  border-radius: 999px;
                  background: rgba(255, 255, 255, 0.52);
                  border: 1px solid rgba($ink_rgb, 0.10);
                  font-size: 0.84rem;
                  color: rgba($ink_rgb, 0.74);
                  backdrop-filter: blur(12px);
                }

                .hero-art {
                  position: relative;
                  min-height: 360px;
                  display: grid;
                  place-items: center;
                }

                .hero-orb {
                  position: absolute;
                  width: 82%;
                  aspect-ratio: 1 / 1;
                  border-radius: 50%;
                  background:
                    radial-gradient(circle at 35% 35%, rgba(255, 255, 255, 0.92), transparent 42%),
                    linear-gradient(140deg, rgba($accent_rgb, 0.34), rgba($ink_rgb, 0.14));
                  filter: blur(0.3px);
                  opacity: 0.96;
                }

                .floating-card {
                  position: absolute;
                  width: min(72vw, 280px);
                  border-radius: 32px;
                  background: linear-gradient(180deg, rgba(255, 255, 255, 0.82), rgba(255, 249, 243, 0.62));
                  border: 1px solid rgba($ink_rgb, 0.10);
                  box-shadow: var(--shadow);
                  padding: 18px;
                  backdrop-filter: blur(18px);
                }

                .floating-card.primary-card {
                  transform: translateY(-4px);
                  z-index: 3;
                }

                .floating-card.tilt-left {
                  transform: translate(-26%, -12%) rotate(-9deg);
                  z-index: 2;
                }

                .floating-card.tilt-right {
                  transform: translate(24%, 14%) rotate(8deg);
                  z-index: 1;
                }

                main {
                  display: grid;
                  gap: 22px;
                }

                section {
                  position: relative;
                  padding: 30px 0;
                }

                .section-card {
                  background: linear-gradient(180deg, rgba(255, 255, 255, 0.48), rgba(255, 249, 243, 0.68));
                  border: 1px solid rgba($ink_rgb, 0.09);
                  border-radius: var(--radius-lg);
                  padding: 26px;
                  box-shadow: 0 14px 40px rgba($ink_rgb, 0.06);
                  backdrop-filter: blur(14px);
                }

                .section-head {
                  display: flex;
                  align-items: center;
                  justify-content: space-between;
                  gap: 18px;
                  margin-bottom: 18px;
                }

                .section-head p {
                  margin: 0;
                  text-transform: uppercase;
                  letter-spacing: 0.18em;
                  font-size: 0.78rem;
                  font-weight: 800;
                  color: rgba($ink_rgb, 0.62);
                }

                .section-head span {
                  width: 100%;
                  height: 1px;
                  background: linear-gradient(90deg, rgba($ink_rgb, 0.18), transparent);
                }

                .story-grid,
                .beans-grid,
                .store-grid,
                .footer-grid {
                  display: grid;
                  gap: 18px;
                }

                .story-copy h2,
                .beans-copy h2,
                .store-copy h2,
                .feed-copy h2 {
                  margin: 0 0 10px;
                  font-family: "Cormorant Garamond", Georgia, serif;
                  font-size: clamp(2.1rem, 4vw, 3.2rem);
                  line-height: 0.98;
                  letter-spacing: -0.03em;
                  max-width: 11ch;
                }

                .story-copy p,
                .beans-copy p,
                .store-copy p,
                .feed-copy p {
                  margin: 0;
                  color: rgba($ink_rgb, 0.8);
                  max-width: 38rem;
                }

                .story-aside,
                .store-panel,
                .goods-panel {
                  display: grid;
                  gap: 14px;
                  align-content: start;
                  padding: 18px;
                  border-radius: var(--radius-md);
                  background: rgba(255, 255, 255, 0.44);
                  border: 1px solid rgba($ink_rgb, 0.08);
                }

                .story-aside strong,
                .store-panel strong {
                  font-size: 0.78rem;
                  text-transform: uppercase;
                  letter-spacing: 0.16em;
                  color: rgba($ink_rgb, 0.6);
                }

                .story-aside p,
                .store-panel p {
                  margin: 0;
                }

                .pill-row {
                  display: flex;
                  flex-wrap: wrap;
                  gap: 10px;
                }

                .menu-intro {
                  max-width: 40rem;
                  margin: 0 0 20px;
                  color: rgba($ink_rgb, 0.8);
                }

                .menu-grid {
                  display: grid;
                  gap: 16px;
                }

                .menu-card {
                  display: grid;
                  gap: 18px;
                  padding: 18px;
                  border-radius: var(--radius-md);
                  background: rgba(255, 255, 255, 0.54);
                  border: 1px solid rgba($ink_rgb, 0.08);
                  box-shadow: 0 12px 26px rgba($ink_rgb, 0.05);
                }

                .card-visual {
                  padding: 18px;
                  border-radius: 18px;
                  background:
                    radial-gradient(circle at 30% 30%, rgba(255, 255, 255, 0.76), transparent 44%),
                    linear-gradient(180deg, rgba($accent_rgb, 0.14), rgba($ink_rgb, 0.05));
                }

                .card-copy {
                  display: grid;
                  gap: 8px;
                }

                .card-copy h3 {
                  margin: 0;
                  font-family: "Cormorant Garamond", Georgia, serif;
                  font-size: 2rem;
                  line-height: 0.98;
                  letter-spacing: -0.02em;
                }

                .card-copy p,
                .card-meta {
                  margin: 0;
                  color: rgba($ink_rgb, 0.75);
                }

                .card-meta {
                  font-size: 0.78rem;
                  text-transform: uppercase;
                  letter-spacing: 0.16em;
                  font-weight: 800;
                }

                .card-price {
                  justify-self: start;
                  padding: 10px 12px;
                  border-radius: 999px;
                  background: rgba($ink_rgb, 0.92);
                  color: var(--bg);
                  font-weight: 800;
                  font-size: 0.9rem;
                }

                .beans-grid {
                  gap: 18px;
                }

                .beans-copy ul {
                  list-style: none;
                  padding: 0;
                  margin: 18px 0 0;
                  display: grid;
                  gap: 10px;
                }

                .beans-copy li {
                  position: relative;
                  padding-left: 18px;
                  color: rgba($ink_rgb, 0.8);
                }

                .beans-copy li::before {
                  content: "";
                  position: absolute;
                  left: 0;
                  top: 0.6em;
                  width: 8px;
                  height: 8px;
                  border-radius: 50%;
                  background: rgba($accent_rgb, 0.9);
                }

                .goods-row {
                  display: flex;
                  justify-content: space-between;
                  gap: 12px;
                  align-items: flex-start;
                  padding: 14px 0;
                  border-top: 1px solid rgba($ink_rgb, 0.08);
                }

                .goods-row:first-of-type {
                  border-top: 0;
                  padding-top: 0;
                }

                .goods-row div {
                  display: grid;
                  gap: 4px;
                }

                .goods-row span,
                .goods-row em {
                  color: rgba($ink_rgb, 0.72);
                  font-style: normal;
                }

                .store-grid {
                  gap: 18px;
                }

                .store-panel a {
                  color: var(--accent);
                  font-weight: 800;
                }

                .feed-grid {
                  display: grid;
                  gap: 12px;
                  margin-top: 18px;
                }

                .feed-tile {
                  min-height: 140px;
                  display: flex;
                  align-items: flex-end;
                  padding: 16px;
                  border-radius: var(--radius-md);
                  border: 1px solid rgba($ink_rgb, 0.08);
                  background:
                    linear-gradient(160deg, rgba($accent_rgb, 0.22), rgba(255, 255, 255, 0.42)),
                    radial-gradient(circle at 20% 18%, rgba(255, 255, 255, 0.82), transparent 34%),
                    rgba(255, 249, 243, 0.64);
                  box-shadow: 0 10px 24px rgba($ink_rgb, 0.05);
                }

                .feed-tile span {
                  display: inline-flex;
                  padding: 8px 10px;
                  border-radius: 999px;
                  background: rgba(255, 255, 255, 0.62);
                  border: 1px solid rgba($ink_rgb, 0.08);
                  font-size: 0.82rem;
                  font-weight: 700;
                }

                footer {
                  padding: 16px 0 8px;
                }

                .footer-grid {
                  gap: 20px;
                  align-items: end;
                  border-top: 1px solid rgba($ink_rgb, 0.10);
                  padding-top: 18px;
                }

                .footer-brand strong {
                  display: block;
                  font-family: "Cormorant Garamond", Georgia, serif;
                  font-size: 2rem;
                  line-height: 0.96;
                  margin-bottom: 6px;
                }

                .footer-brand p,
                .footer-links a,
                .footer-note {
                  margin: 0;
                  color: rgba($ink_rgb, 0.72);
                }

                .footer-links {
                  display: flex;
                  flex-wrap: wrap;
                  gap: 12px 18px;
                }

                .footer-links a {
                  font-weight: 700;
                }

                .reveal {
                  opacity: 0;
                  transform: translateY(24px);
                  transition: opacity 700ms ease, transform 700ms ease;
                }

                .reveal.is-visible {
                  opacity: 1;
                  transform: translateY(0);
                }

                @media (min-width: 720px) {
                  .page-shell {
                    padding: 28px 28px 42px;
                  }

                  .menu-grid,
                  .feed-grid {
                    grid-template-columns: repeat(2, minmax(0, 1fr));
                  }

                  .footer-grid {
                    grid-template-columns: 1.4fr 1fr;
                  }
                }

                @media (min-width: 960px) {
                  .nav-links {
                    display: inline-flex;
                  }

                  .hero-grid {
                    grid-template-columns: minmax(0, 1.15fr) minmax(0, 0.85fr);
                    gap: 20px;
                    min-height: 82vh;
                  }

                  .story-grid,
                  .beans-grid,
                  .store-grid {
                    grid-template-columns: minmax(0, 1.2fr) minmax(320px, 0.8fr);
                    align-items: start;
                  }

                  .menu-grid {
                    grid-template-columns: repeat(2, minmax(0, 1fr));
                  }

                  .menu-card {
                    grid-template-columns: 160px 1fr auto;
                    align-items: center;
                  }

                  .feed-grid {
                    grid-template-columns: repeat(4, minmax(0, 1fr));
                  }

                  .hero-art {
                    min-height: 620px;
                  }

                  .floating-card {
                    width: min(24vw, 280px);
                  }
                }

                @media (prefers-reduced-motion: reduce) {
                  html {
                    scroll-behavior: auto;
                  }

                  .button,
                  .reveal {
                    transition: none;
                  }

                  .reveal {
                    opacity: 1;
                    transform: none;
                  }
                }
              </style>
            </head>
            <body>
              <div class="page-shell" id="top">
                <header class="hero">
                  <nav class="nav reveal">
                    <a class="brand-lockup" href="#top" aria-label="$brand_name home">
                      <strong>$brand_mark</strong>
                      <span>$brand_name</span>
                    </a>
                    <div class="nav-links">
                      <a href="#story">Story</a>
                      <a href="#menu">Menu</a>
                      <a href="#beans">Beans</a>
                      <a href="#visit">Visit</a>
                      <a href="$store_url" target="_blank" rel="noreferrer">Smart Store</a>
                    </div>
                  </nav>

                  <div class="hero-grid">
                    <div class="hero-copy reveal">
                      <p class="eyebrow">$hero_eyebrow</p>
                      <h1 class="brand-name">$brand_name</h1>
                      <p class="slogan">$slogan</p>
                      <p class="hero-body">$hero_body</p>
                      <div class="cta-row">
                        <a class="button primary" href="#menu">Explore the Menu</a>
                        <a class="button secondary" href="$store_url" target="_blank" rel="noreferrer">$beans_cta_label</a>
                      </div>
                      <ul class="fact-row">$fact_markup</ul>
                    </div>

                    <div class="hero-art reveal" aria-hidden="true">
                      <div class="hero-orb"></div>
                      <div class="floating-card tilt-left">$hero_asset_one</div>
                      <div class="floating-card primary-card">$hero_asset_two</div>
                      <div class="floating-card tilt-right">$hero_asset_three</div>
                    </div>
                  </div>
                </header>

                <main>
                  <section id="story">
                    <div class="section-card">
                      <div class="section-head">
                        <p>Brand Story</p>
                        <span></span>
                      </div>
                      <div class="story-grid">
                        <div class="story-copy reveal">
                          <h2>$story_title</h2>
                          <p>$story_body</p>
                        </div>
                        <aside class="story-aside reveal">
                          <strong>At A Glance</strong>
                          <p><b>Founded</b><br />$founded</p>
                          <p><b>Audience</b><br />$primary_target</p>
                          <div class="pill-row">$keyword_pills</div>
                        </aside>
                      </div>
                    </div>
                  </section>

                  <section id="menu">
                    <div class="section-card">
                      <div class="section-head">
                        <p>Menu</p>
                        <span></span>
                      </div>
                      <p class="menu-intro reveal">$menu_intro</p>
                      <div class="menu-grid">
                        $menu_cards
                      </div>
                    </div>
                  </section>

                  <section id="beans">
                    <div class="section-card">
                      <div class="section-head">
                        <p>Beans &amp; Goods</p>
                        <span></span>
                      </div>
                      <div class="beans-grid">
                        <div class="beans-copy reveal">
                          <h2>$beans_title</h2>
                          <p>$beans_body</p>
                          <ul>$beans_highlights</ul>
                          <div class="cta-row">
                            <a class="button primary" href="$store_url" target="_blank" rel="noreferrer">$beans_cta_label</a>
                            <a class="button secondary" href="#visit">Plan Your Visit</a>
                          </div>
                        </div>
                        <div class="goods-panel reveal">
                          $goods_rows
                        </div>
                      </div>
                    </div>
                  </section>

                  <section id="visit">
                    <div class="section-card">
                      <div class="section-head">
                        <p>Store Info</p>
                        <span></span>
                      </div>
                      <div class="store-grid">
                        <div class="store-copy reveal">
                          <h2>$store_title</h2>
                          <p>$store_body</p>
                        </div>
                        <aside class="store-panel reveal">
                          <strong>Directions</strong>
                          <p><b>Address</b><br />$location</p>
                          <p><b>Hours</b><br />$hours_label</p>
                          <p><b>Note</b><br />$visit_note</p>
                          <p><a href="$map_url" target="_blank" rel="noreferrer">Open map and directions</a></p>
                        </aside>
                      </div>
                    </div>
                  </section>

                  <section id="instagram">
                    <div class="section-card">
                      <div class="section-head">
                        <p>Instagram</p>
                        <span></span>
                      </div>
                      <div class="feed-copy reveal">
                        <h2>$instagram_title</h2>
                        <p>$instagram_body</p>
                      </div>
                      <div class="feed-grid">
                        $feed_tiles
                      </div>
                    </div>
                  </section>
                </main>

                <footer>
                  <div class="footer-grid">
                    <div class="footer-brand reveal">
                      <strong>$brand_name</strong>
                      <p>$footer_tagline</p>
                    </div>
                    <div class="reveal">
                      <div class="footer-links">
                        <a href="$instagram_url" target="_blank" rel="noreferrer">Instagram</a>
                        <a href="mailto:$email_address">$email_address</a>
                        <a href="$store_url" target="_blank" rel="noreferrer">Order Beans</a>
                        <a href="$map_url" target="_blank" rel="noreferrer">Directions</a>
                      </div>
                      <p class="footer-note">Single-scroll landing page for a warm, editorial coffee brand experience.</p>
                    </div>
                  </div>
                </footer>
              </div>

              <script>
                (function () {
                  if (window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
                    document.querySelectorAll(".reveal").forEach(function (node) {
                      node.classList.add("is-visible");
                    });
                    return;
                  }

                  var observer = new IntersectionObserver(function (entries) {
                    entries.forEach(function (entry) {
                      if (entry.isIntersecting) {
                        entry.target.classList.add("is-visible");
                        observer.unobserve(entry.target);
                      }
                    });
                  }, { threshold: 0.16, rootMargin: "0px 0px -8% 0px" });

                  document.querySelectorAll(".reveal").forEach(function (node) {
                    observer.observe(node);
                  });
                }());
              </script>
            </body>
            </html>
            """
        ).strip()
    )

    return template.safe_substitute(
        meta_title=escape(copy_pack["meta_title"], quote=True),
        meta_description=escape(copy_pack["meta_description"], quote=True),
        bg=colors["bg"],
        ink=colors["ink"],
        accent=colors["accent"],
        accent_rgb=accent_rgb,
        ink_rgb=ink_rgb,
        brand_name=escape(brief["brand_name"]),
        brand_mark=escape(mark),
        hero_eyebrow=escape(copy_pack["hero_eyebrow"]),
        slogan=escape(brief["slogan"]),
        hero_body=escape(copy_pack["hero_body"]),
        beans_cta_label=escape(copy_pack["beans_cta_label"]),
        fact_markup=fact_markup,
        hero_asset_one=hero_assets[0],
        hero_asset_two=hero_assets[1],
        hero_asset_three=hero_assets[2],
        story_title=escape(copy_pack["story_title"]),
        story_body=escape(copy_pack["story_body"]),
        founded=escape(brief["founded"]),
        primary_target=escape(brief["primary_target"] or brief["target_profile"] or "Coffee-focused regulars and curious visitors"),
        keyword_pills=render_keyword_pills(brief["keywords"] or ["Minimal", "Warmth", "Craftsmanship"]),
        menu_intro=escape(copy_pack["menu_intro"]),
        menu_cards=render_menu_cards(brief["signature_items"], copy_pack, assets),
        beans_title=escape(copy_pack["beans_title"]),
        beans_body=escape(copy_pack["beans_body"]),
        beans_highlights=render_highlights(copy_pack["beans_highlights"]),
        goods_rows=render_goods_list(brief["goods_items"]),
        store_title=escape(copy_pack["store_title"]),
        store_body=escape(copy_pack["store_body"]),
        location=escape(brief["location"]),
        hours_label=escape(copy_pack["hours_label"]),
        visit_note=escape(copy_pack["visit_note"]),
        map_url=map_url,
        store_url=store_url,
        instagram_title=escape(copy_pack["instagram_title"]),
        instagram_body=escape(copy_pack["instagram_body"]),
        feed_tiles=render_feed_tiles(copy_pack["instagram_labels"]),
        footer_tagline=escape(copy_pack["footer_tagline"]),
        instagram_url=instagram_url,
        email_address=escape(email_address),
    )


challenge = challenge_input if isinstance(challenge_input, dict) else {}
brief_markdown = compact_text("")
task_brief_value = challenge.get("task_brief")
if isinstance(task_brief_value, str) and task_brief_value.strip():
    brief_markdown = task_brief_value
else:
    brief_markdown = json.dumps(challenge, ensure_ascii=False, indent=2)

brief = parse_brief(brief_markdown)
assets = challenge.get("assets", {}) if isinstance(challenge.get("assets", {}), dict) else {}

config_extra = getattr(submission_config, "extra", {}) or {}
role_models = config_extra.get("role_models", {}) if isinstance(config_extra, dict) else {}
base_model = getattr(submission_config, "model", "openai/gpt-5.2") or "openai/gpt-5.2"
copy_model = role_models.get("copywriter", base_model)
review_model = role_models.get("reviewer", base_model)
temperature = getattr(submission_config, "temperature", 0.35)
max_tokens = getattr(submission_config, "max_tokens", 1600) or 1600
quality_guide = ""
if isinstance(rag_docs, dict):
    quality_guide = rag_docs.get("site-quality-rubric.md", "")

fallback_copy = build_fallback_copy(brief)
copy_pack = request_copy_pack(
    brief,
    fallback_copy,
    quality_guide,
    copy_model,
    review_model,
    temperature,
    max_tokens,
)
html_output = build_html(brief, copy_pack, assets)

result = {"output": html_output}

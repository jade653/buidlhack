import re
import json

# ── Unpack challenge inputs ───────────────────────────────────────────────────
assets       = challenge_input.get("assets", {})
brief        = challenge_input.get("task_brief", "")
design_guide = rag_docs.get("design_guide.md", "")

svg_espresso  = assets.get("espresso-cup", "")
svg_cold_brew = assets.get("cold-brew-tonic", "")
svg_latte     = assets.get("signature-latte", "")

# ── Model routing ─────────────────────────────────────────────────────────────
role_models  = submission_config.extra.get("role_models", {})
copy_model   = role_models.get("copywriter", submission_config.model)
design_model = role_models.get("designer",   submission_config.model)
review_model = role_models.get("reviewer",   submission_config.model)

# ─────────────────────────────────────────────────────────────────────────────
# STAGE 1 — Copy Writer
# Generates structured brand copy for every section from the raw brief.
# Using a focused model at moderate temperature for warm, on-brand language.
# ─────────────────────────────────────────────────────────────────────────────
COPY_USER = (
    "You are a brand copywriter. Using the brief below, write minimal, warm website copy.\n"
    "Tone: honest, craft-focused, understated. English. No marketing fluff.\n\n"
    "Return ONLY a valid JSON object with exactly these keys:\n"
    "  hero_headline, hero_subline,\n"
    "  brand_story,\n"
    "  menu_intro,\n"
    "  beans_headline, beans_body, beans_cta,\n"
    "  store_headline, store_hours, store_address, store_directions,\n"
    "  footer_tagline\n\n"
    "Constraints:\n"
    "- hero_headline: brand name only — 'Grain & Ground'\n"
    "- hero_subline: the slogan or a single evocative phrase (max 8 words)\n"
    "- brand_story: 3–4 sentences, specific to origin sourcing and Seongsu-dong\n"
    "- menu_intro: one sentence, max 12 words\n"
    "- beans_headline: 2–4 words\n"
    "- beans_body: 1–2 sentences about house-roasted beans and drip bags\n"
    "- beans_cta: 3–5 words for a button label\n"
    "- store_headline: 2–3 words\n"
    "- store_hours: exact hours as given\n"
    "- store_address: full address\n"
    "- store_directions: 1–2 sentences, evocative but practical\n"
    "- footer_tagline: the brand slogan\n\n"
    "BRAND BRIEF:\n" + brief
)

copy_raw = llm.chat(
    [
        {"role": "system", "content": agent_prompt},
        {"role": "user",   "content": COPY_USER},
    ],
    model=copy_model,
    temperature=0.45,
    max_tokens=900,
)["content"]

# Parse JSON with multiple fallback strategies
copy_data = {}
try:
    # Try stripping markdown fences first
    cleaned = re.sub(r"```(?:json)?", "", copy_raw).replace("```", "").strip()
    copy_data = json.loads(cleaned)
except Exception:
    try:
        m = re.search(r"\{[\s\S]*\}", copy_raw)
        copy_data = json.loads(m.group(0)) if m else {}
    except Exception:
        copy_data = {}

def get(key, default):
    return str(copy_data.get(key, default)).strip() or default

hero_headline    = get("hero_headline",    "Grain & Ground")
hero_subline     = get("hero_subline",     "Every cup has a story.")
brand_story      = get("brand_story",
    "Nestled in the back alleys of Seongsu-dong, we source green beans directly "
    "from origin and roast in small batches. Each cup is a conversation between "
    "a producer and a drinker — made possible by careful selection and honest craft.")
menu_intro       = get("menu_intro",       "Each drink begins with the bean.")
beans_headline   = get("beans_headline",   "Bring It Home")
beans_body       = get("beans_body",
    "House-roasted beans available in 100g and 200g, plus convenient drip bag sets. "
    "Sourced with intention. Roasted in small batches. Ready to ship.")
beans_cta        = get("beans_cta",        "Shop Beans & Goods")
store_headline   = get("store_headline",   "Find Us")
store_hours      = get("store_hours",      "Mon – Fri  9:00 – 21:00  /  Sat – Sun  10:00 – 22:00")
store_address    = get("store_address",    "Seongsu-dong, Seongdong-gu, Seoul")
store_directions = get("store_directions",
    "Tucked into a side street off Seongsu-ro. "
    "Look for the hand-painted sign above a low wooden door.")
footer_tagline   = get("footer_tagline",   "Every cup has a story.")

# ─────────────────────────────────────────────────────────────────────────────
# STAGE 2 — HTML Designer
# Builds the complete production website using the copy + design system + SVGs.
# Using the most capable model (opus) for high-quality layout and code.
# ─────────────────────────────────────────────────────────────────────────────
HTML_USER = (
    "Build a complete, production-ready single-page website for a specialty coffee café.\n"
    "Output ONLY raw HTML — start with <!DOCTYPE html>, end with </html>.\n"
    "No markdown fences. No prose before or after the HTML.\n\n"

    "=== DESIGN SYSTEM ===\n"
    + design_guide + "\n\n"

    "=== PAGE COPY ===\n"
    "hero_headline:    " + hero_headline    + "\n"
    "hero_subline:     " + hero_subline     + "\n"
    "brand_story:      " + brand_story      + "\n"
    "menu_intro:       " + menu_intro       + "\n"
    "beans_headline:   " + beans_headline   + "\n"
    "beans_body:       " + beans_body       + "\n"
    "beans_cta:        " + beans_cta        + "\n"
    "store_headline:   " + store_headline   + "\n"
    "store_hours:      " + store_hours      + "\n"
    "store_address:    " + store_address    + "\n"
    "store_directions: " + store_directions + "\n"
    "footer_tagline:   " + footer_tagline   + "\n\n"

    "=== MENU ITEMS (4 cards in a grid) ===\n"
    "1. Signature Hand Drip  |  Ethiopia Yirgacheffe  |  ₩7,500  |  espresso-cup SVG\n"
    "2. Cold Brew Tonic       |  House cold brew + tonic  |  ₩8,000  |  cold-brew-tonic SVG\n"
    "3. Café Latte            |  House blend, velvety foam  |  ₩6,500  |  signature-latte SVG\n"
    "4. Seasonal Drink        |  Rotates quarterly           |  approx. ₩8,500  |  use seasonal-icon CSS from design guide\n\n"

    "=== SVG ASSETS — embed verbatim, do not alter any attribute ===\n"
    "[espresso-cup]\n" + svg_espresso + "\n\n"
    "[cold-brew-tonic]\n" + svg_cold_brew + "\n\n"
    "[signature-latte]\n" + svg_latte + "\n\n"

    "=== TECHNICAL SPEC ===\n"
    "CSS :root variables (mandatory):\n"
    "  --clr-bg: #F5F0EB\n"
    "  --clr-dark: #3B2314\n"
    "  --clr-accent: #C07A5A\n"
    "  --ff-serif: 'Cormorant Garamond', Georgia, serif\n"
    "  --ff-sans: 'Inter', system-ui, sans-serif\n\n"
    "Google Fonts import (first line of <style>):\n"
    "  @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,600;1,400&family=Inter:wght@400;500&display=swap');\n\n"
    "Section order (with IDs):\n"
    "  1. <header> — sticky nav, brand name only\n"
    "  2. <section id='hero'> — 100vh, centered flex, large h1, subline, subtle scroll indicator\n"
    "  3. <section id='story'> — section-header + brand_story paragraph, centered, max-width 680px\n"
    "  4. <section id='menu'> — section-header + 4 menu cards in CSS Grid\n"
    "     Grid: grid-template-columns: repeat(auto-fill, minmax(240px, 1fr))\n"
    "  5. <section id='shop'> — dark bg (#3B2314), light text, beans info, CTA button\n"
    "     CTA href: 'https://smartstore.naver.com/grainandground'\n"
    "  6. <section id='visit'> — section-header, 2-col layout (hours+address left, directions right)\n"
    "     Map link href: 'https://maps.google.com/?q=Seongsu-dong+Seongdong-gu+Seoul'\n"
    "  7. <footer> — dark bg, brand name, footer_tagline, social icon links, copyright\n"
    "     Instagram: 'https://instagram.com/grainandground' (aria-label='Instagram')\n"
    "     Email: 'mailto:hello@grainandground.com' (aria-label='Email')\n\n"
    "Scroll animation:\n"
    "  Add class 'fade-in' to: every section, .section-header, every .menu-card, .shop-content, .visit-grid, footer\n"
    "  Use IntersectionObserver as in design guide (threshold: 0.1)\n\n"
    "Other:\n"
    "  html { scroll-behavior: smooth; }\n"
    "  * { box-sizing: border-box; margin: 0; padding: 0; }\n"
    "  Images/placeholders: none needed — SVGs only\n"
    "  No external JS dependencies\n"
    "  Include inline SVG icons (simple paths) for Instagram and email in footer\n"
    "  Hero: include a subtle animated scroll indicator (a small down-arrow that pulses)\n"
    "  Add focus-visible outline styles for accessibility\n"
    "  Meta tags: charset UTF-8, viewport, description 'Grain & Ground — Specialty Coffee, Seongsu-dong Seoul'\n"
)

html_raw = llm.chat(
    [
        {"role": "system", "content": agent_prompt},
        {"role": "user",   "content": HTML_USER},
    ],
    model=design_model,
    temperature=0.2,
    max_tokens=8000,
)["content"]

# Extract HTML document
html_m = re.search(r"(<!DOCTYPE html>[\s\S]*</html>)", html_raw, re.IGNORECASE)
draft_html = html_m.group(1) if html_m else html_raw.strip()

# ─────────────────────────────────────────────────────────────────────────────
# STAGE 3 — QA Reviewer
# Reads the draft, verifies every requirement, returns corrected HTML.
# Low temperature — this is correctness checking, not creative work.
# ─────────────────────────────────────────────────────────────────────────────
REVIEW_USER = (
    "You are a senior front-end QA engineer.\n"
    "Review the HTML below and return the complete, corrected version.\n"
    "Output ONLY raw HTML (<!DOCTYPE html> ... </html>). No markdown. No prose.\n\n"
    "QA Checklist — identify and fix every failing item:\n"
    "[ ] 1. All 3 custom SVGs are embedded verbatim in menu cards (espresso-cup, cold-brew-tonic, signature-latte)\n"
    "[ ] 2. CSS :root defines --clr-bg:#F5F0EB, --clr-dark:#3B2314, --clr-accent:#C07A5A, --ff-serif, --ff-sans\n"
    "[ ] 3. Google Fonts @import is the first rule inside <style>\n"
    "[ ] 4. All 7 structural elements present: nav, #hero, #story, #menu, #shop, #visit, footer\n"
    "[ ] 5. IntersectionObserver JS adds 'visible' to '.fade-in' elements\n"
    "[ ] 6. .fade-in/.fade-in.visible CSS rules are defined\n"
    "[ ] 7. Mobile-first: single column layout on <768px, no overflow-x\n"
    "[ ] 8. #shop section uses var(--clr-dark) as background, var(--clr-bg) as text color\n"
    "[ ] 9. Footer contains inline SVG icons for Instagram and email with aria-labels\n"
    "[ ] 10. Nav is sticky with backdrop-filter blur\n"
    "[ ] 11. Hero is 100vh with large Cormorant Garamond h1\n"
    "[ ] 12. Section headers use .label + .rule + h2 pattern\n"
    "[ ] 13. No unclosed tags, no invalid CSS, no JS errors\n"
    "[ ] 14. All 4 menu cards present (3 with brand SVGs, 1 seasonal placeholder)\n"
    "[ ] 15. Google Maps link present in #visit section\n\n"
    "HTML to review:\n\n"
    + draft_html
)

try:
    review_raw = llm.chat(
        [
            {"role": "system", "content": "You are a meticulous front-end QA engineer. Return ONLY complete, valid HTML. Never use markdown fences."},
            {"role": "user",   "content": REVIEW_USER},
        ],
        model=review_model,
        temperature=0.1,
        max_tokens=8000,
    )["content"]
    final_m = re.search(r"(<!DOCTYPE html>[\s\S]*</html>)", review_raw, re.IGNORECASE)
    final_html = final_m.group(1) if final_m else draft_html
except Exception:
    final_html = draft_html

# Strip any stray markdown fences that slipped through
final_html = re.sub(r"^```(?:html)?[\r\n]?", "", final_html.strip())
final_html = re.sub(r"[\r\n]?```$", "", final_html.strip())

result = {"output": final_html}

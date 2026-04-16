#!/usr/bin/env python3
"""
parse_task.py — task.md (client brief) → challenge_input.json

Usage:
    python parse_task.py                    # task.md → challenge_input.json
    python parse_task.py my_brief.md        # custom input
    python parse_task.py in.md out.json     # custom input + output

Handles:
    ## Section Header
    **Key:** Value (single line)
    **Key:**           ← followed by list items or prose on next lines
    - List item
    Standalone prose paragraphs
"""

import json
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Section body parser
# ---------------------------------------------------------------------------

def _parse_section_body(body: str) -> dict:
    """Parse one section's text into a flat dict."""
    result = {}
    lines = body.splitlines()
    i = 0

    while i < len(lines):
        line = lines[i].rstrip()

        # Skip horizontal rules and blank lines at top-level
        if re.match(r'^-{3,}$', line.strip()) or not line.strip():
            i += 1
            continue

        # Match **Key:** Value — colon is INSIDE the bold markers: **Key:** Value
        kv = re.match(r'^\*\*(.+?)[:：]\*\*\s*(.*)', line)
        if kv:
            key      = kv.group(1).strip()
            inline   = kv.group(2).strip()
            i += 1

            if inline:
                # Value on same line → plain string
                result[key] = inline
                continue

            # No inline value — collect following lines until blank or next key
            collected = []
            while i < len(lines):
                l = lines[i].rstrip()
                stripped = l.strip()

                # Stop conditions: blank line, next **key, horizontal rule
                if (not stripped
                        or re.match(r'^\*\*.+?[:：]\*\*', l)
                        or re.match(r'^-{3,}$', stripped)
                        or stripped.startswith('##')):
                    break
                collected.append(l)
                i += 1

            # List or prose? Handles both '- item' and '1. item' formats.
            list_items = []
            for l in collected:
                s = l.strip()
                if s.startswith('- '):
                    list_items.append(s[2:].strip())
                elif re.match(r'^\d+\.\s+', s):
                    list_items.append(re.sub(r'^\d+\.\s+', '', s))

            if list_items:
                result[key] = list_items
            elif collected:
                result[key] = ' '.join(l.strip() for l in collected if l.strip())
            continue

        i += 1

    return result


# ---------------------------------------------------------------------------
# Menu item parser
# ---------------------------------------------------------------------------

def _parse_menu_items(raw_list: list) -> list:
    """
    Convert raw list strings like
        '시그니처 핸드드립 (에티오피아 예가체프) — 7,500원'
    into {'name': ..., 'detail': ..., 'price': ...} dicts.
    """
    parsed = []
    for raw in raw_list:
        price_m = re.search(r'[—–]\s*(.+)$', raw)
        price   = price_m.group(1).strip() if price_m else ""
        name_part = raw[: price_m.start()].strip() if price_m else raw

        detail_m = re.search(r'\((.+?)\)', name_part)
        detail   = detail_m.group(1).strip() if detail_m else ""
        name     = re.sub(r'\s*\(.+?\)', '', name_part).strip()

        parsed.append({"name": name, "detail": detail, "price": price})
    return parsed


# ---------------------------------------------------------------------------
# Section → schema mapper
# ---------------------------------------------------------------------------

def _section(sections: dict, keyword: str) -> dict:
    """Find a section whose title contains `keyword` (case-insensitive)."""
    for title, data in sections.items():
        if keyword.lower() in title.lower():
            return data
    return {}


def _map_to_schema(sections: dict) -> dict:
    brand_s  = _section(sections, "브랜드")
    target_s = _section(sections, "타겟")
    menu_s   = _section(sections, "메뉴")
    design_s = _section(sections, "디자인")
    pages_s  = _section(sections, "페이지")
    req_s    = _section(sections, "특별")

    # ── brand ──────────────────────────────────────────────────────────────
    brand = {
        "name":        brand_s.get("브랜드명", ""),
        "slogan":      brand_s.get("슬로건", ""),
        "category":    brand_s.get("업종", ""),
        "operation":   brand_s.get("운영 형태", ""),
        "location":    brand_s.get("매장 위치", ""),
        "founded":     brand_s.get("설립 연도", ""),
        "description": brand_s.get("브랜드 소개", ""),
    }

    # ── target ─────────────────────────────────────────────────────────────
    target = {
        "age_range":       target_s.get("주요 타겟", ""),
        "characteristics": target_s.get("특징", ""),
    }

    # ── menu ───────────────────────────────────────────────────────────────
    menu_raw    = menu_s.get("대표 메뉴", [])
    goods_raw   = menu_s.get("원두 / 굿즈 판매", menu_s.get("굿즈", []))
    if isinstance(menu_raw, str):
        menu_raw = []
    if isinstance(goods_raw, str):
        goods_raw = []

    menu = {
        "items":    _parse_menu_items(menu_raw),
        "products": _parse_menu_items(goods_raw),
    }

    # ── design ─────────────────────────────────────────────────────────────
    keywords_raw = design_s.get("키워드", "")
    keywords = (
        [k.strip() for k in re.split(r'[,、]', keywords_raw)]
        if isinstance(keywords_raw, str) and keywords_raw
        else keywords_raw if isinstance(keywords_raw, list)
        else []
    )

    palette_raw = design_s.get("색상 팔레트", "")
    if isinstance(palette_raw, list):
        palette_raw = " ".join(palette_raw)
    colors = re.findall(r'#[0-9A-Fa-f]{6}', palette_raw)

    design = {
        "keywords":  keywords,
        "colors":    colors,
        "mood":      design_s.get("무드", ""),
        "reference": design_s.get("레퍼런스", ""),
    }

    # ── pages ──────────────────────────────────────────────────────────────
    req_secs = pages_s.get("필수 섹션 (순서대로)", pages_s.get("필수 섹션", []))
    opt_secs = pages_s.get("선택 섹션", [])
    if isinstance(req_secs, str):
        req_secs = [req_secs]
    if isinstance(opt_secs, str):
        opt_secs = [opt_secs]

    def _clean(s: str) -> str:
        """Strip numbering '1. ' and trailing annotations ' — ...' """
        s = re.sub(r'^\d+\.\s*', '', s)
        return s.split(' —')[0].strip()

    pages = {
        "type":     pages_s.get("페이지 형태", ""),
        "sections": [_clean(s) for s in req_secs],
        "optional": opt_secs,
    }

    # ── requirements ───────────────────────────────────────────────────────
    notes_raw = req_s.get("기타", [])
    if isinstance(notes_raw, str):
        notes_raw = [notes_raw]

    requirements = {
        "language":   req_s.get("언어", ""),
        "animation":  req_s.get("애니메이션", ""),
        "responsive": req_s.get("반응형", ""),
        "notes":      notes_raw,
    }

    return {
        "brand":        brand,
        "target":       target,
        "menu":         menu,
        "design":       design,
        "pages":        pages,
        "requirements": requirements,
    }


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def parse_task_md(md_text: str) -> dict:
    # Strip blockquote lines (the intro note in task.md)
    md_text = re.sub(r'^>.*$', '', md_text, flags=re.MULTILINE)

    # Split by ## section headers; result: [pre, title1, body1, title2, body2, ...]
    parts = re.split(r'^## (.+)$', md_text, flags=re.MULTILINE)

    sections: dict = {}
    idx = 1
    while idx < len(parts) - 1:
        title = parts[idx].strip()
        body  = parts[idx + 1]
        sections[title] = _parse_section_body(body)
        idx += 2

    return _map_to_schema(sections)


def main() -> None:
    args        = sys.argv[1:]
    input_path  = Path(args[0]) if args else Path("samples/task.md")
    output_path = Path(args[1]) if len(args) > 1 else Path("samples/challenge_input.json")

    if not input_path.exists():
        print(f"Error: {input_path} not found.", file=sys.stderr)
        sys.exit(1)

    md_text = input_path.read_text(encoding="utf-8")
    result  = parse_task_md(md_text)

    output_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"Parsed  : {input_path}")
    print(f"Output  : {output_path}")
    print(f"Brand   : {result['brand']['name']}")
    print(f"Menu    : {len(result['menu']['items'])} items")
    print(f"Sections: {result['pages']['sections']}")


if __name__ == "__main__":
    main()

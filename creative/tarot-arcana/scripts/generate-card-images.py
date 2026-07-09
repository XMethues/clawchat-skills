#!/usr/bin/env python3
"""Generate tarot card PNG images from deck.json data.

Usage:
  cd /opt/data/tarot-arcana-app
  uv run python3 scripts/generate-card-images.py

Output: 78 card face PNGs + 1 card back PNG in liveware/static/cards/
Each image: 240x336 px PNG with suit-based coloring.

Requires: Pillow (pip install Pillow)
"""

import json
import os

from PIL import Image, ImageDraw, ImageFont

DECK_JSON = "/opt/data/skills/creative/tarot-arcana/data/deck.json"
OUT_DIR = "/opt/data/skills/creative/tarot-arcana/liveware/static/cards"

W, H = 240, 336

# Suit colors
SUIT_COLORS = {
    "cups":     (91,  141, 203),  # blue
    "swords":   (201, 91,  91),   # red
    "pentacles":(91,  201, 107),  # green
    "wands":    (201, 168, 91),   # gold
}
MAJOR_COLOR = (123, 91, 201)  # purple
BACK_COLOR  = (42,  18,  72)  # dark purple

SUIT_SYMBOLS = {
    "cups":     "♕",
    "swords":   "♔",
    "pentacles":"♖",
    "wands":    "♗",
}
MAJOR_SYMBOL = "★"

RANK_LABELS = {
    1: "A", 11: "Page", 12: "Knight", 13: "Queen", 14: "King",
    2: "2", 3: "3", 4: "4", 5: "5", 6: "6", 7: "7", 8: "8", 9: "9", 10: "10",
}

ROMAN = {1:"I",2:"II",3:"III",4:"IV",5:"V",6:"VI",7:"VII",8:"VIII",9:"IX",
         10:"X",11:"XI",12:"XII",13:"XIII",14:"XIV",15:"XV",16:"XVI",
         17:"XVII",18:"XVIII",19:"XIX",20:"XX",21:"XXI"}

# Load card Zh data for Chinese names
CARDS_ZH_PATH = "/opt/data/tarot-arcana-app/src/data/cards.ts"
CARD_ZH = {}
if os.path.exists(CARDS_ZH_PATH):
    import re
    with open(CARDS_ZH_PATH) as f:
        ts = f.read()
    # Extract cardZh object
    m = re.search(r'export const cardZh\s*:\s*Record<string,\s*\{[^}]+\}>\s*=\s*\{([^}]+)\}', ts, re.DOTALL)
    if m:
        # Simple extraction of id: { name: "..." } pairs
        for match in re.finditer(r'"([^"]+)"\s*:\s*\{\s*name:\s*"([^"]+)"', ts):
            CARD_ZH[match.group(1)] = match.group(2)


def get_font(size: int):
    """Try to find a CJK-capable font, fall back to default."""
    paths = [
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]
    for p in paths:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def draw_rounded_rect(draw, xy, radius, fill):
    x1, y1, x2, y2 = xy
    draw.rounded_rectangle([x1, y1, x2, y2], radius=radius, fill=fill)


def generate_card(card: dict):
    card_id = card["id"]
    is_major = card["arcana"] == "major"
    suit = card.get("suit")
    number = card["number"]

    color = MAJOR_COLOR if is_major else SUIT_COLORS.get(suit, (80, 80, 80))

    # Light card background
    bg = (248, 244, 250) if is_major else (250, 250, 252)
    img = Image.new("RGB", (W, H), bg)
    draw = ImageDraw.Draw(img)

    # Border
    draw_rounded_rect(draw, (4, 4, W-4, H-4), 10, color)
    draw_rounded_rect(draw, (8, 8, W-8, H-8), 8, bg)

    # Suit symbol (large, centered)
    symbol = MAJOR_SYMBOL if is_major else SUIT_SYMBOLS.get(suit, "?")
    font_sym = get_font(80)
    bbox = draw.textbbox((0, 0), symbol, font=font_sym)
    sym_w = bbox[2] - bbox[0]
    sym_x = (W - sym_w) // 2
    draw.text((sym_x, 80), symbol, fill=color, font=font_sym)

    # Rank label (top)
    if is_major:
        rank_label = ROMAN.get(number, str(number))
    elif "rank" in card and card["rank"]:
        rank_label = RANK_LABELS.get(card["rank"], str(card["rank"]))
        if suit and rank_label.isdigit():
            rank_label = f"{rank_label}{SUIT_SYMBOLS.get(suit, '')}"
    else:
        rank_label = str(number)

    font_rank = get_font(22)
    bbox = draw.textbbox((0, 0), rank_label, font=font_rank)
    rw = bbox[2] - bbox[0]
    draw.text(((W - rw) // 2, 170), rank_label, fill=color, font=font_rank)

    # Card name (bottom)
    name = CARD_ZH.get(card_id) or card.get("name", card_id)
    font_name = get_font(16)
    # Word-wrap if needed
    words = name
    if draw.textbbox((0, 0), name, font=font_name)[2] > W - 24:
        # Split into two lines
        mid = len(name) // 2
        line1 = name[:mid]
        line2 = name[mid:]
        bbox1 = draw.textbbox((0, 0), line1, font=font_name)
        bbox2 = draw.textbbox((0, 0), line2, font=font_name)
        w1 = bbox1[2] - bbox1[0]
        w2 = bbox2[2] - bbox2[0]
        draw.text(((W - w1) // 2, 220), line1, fill=(60, 60, 70), font=font_name)
        draw.text(((W - w2) // 2, 244), line2, fill=(60, 60, 70), font=font_name)
    else:
        bbox = draw.textbbox((0, 0), name, font=font_name)
        nw = bbox[2] - bbox[0]
        draw.text(((W - nw) // 2, 230), name, fill=(60, 60, 70), font=font_name)

    out_path = os.path.join(OUT_DIR, f"{card_id}.png")
    img.save(out_path, "PNG")
    return out_path


def generate_card_back():
    img = Image.new("RGB", (W, H), BACK_COLOR)
    draw = ImageDraw.Draw(img)

    # Border
    draw_rounded_rect(draw, (4, 4, W-4, H-4), 10, (62, 28, 92))
    draw_rounded_rect(draw, (8, 8, W-8, H-8), 8, BACK_COLOR)

    # Dot pattern
    for y in range(20, H-20, 24):
        for x in range(20, W-20, 24):
            draw.ellipse([x-1, y-1, x+1, y+1], fill=(72, 38, 102))

    # Center diamond
    cx, cy = W // 2, H // 2
    diamond = [(cx, cy-40), (cx+30, cy), (cx, cy+40), (cx-30, cy)]
    draw.polygon(diamond, outline=(180, 140, 200), width=2)

    out_path = os.path.join(OUT_DIR, "CardBacks.png")
    img.save(out_path, "PNG")
    return out_path


def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    with open(DECK_JSON) as f:
        deck = json.load(f)

    count = 0
    for card in deck:
        path = generate_card(card)
        count += 1
        name = CARD_ZH.get(card["id"]) or card.get("name", card["id"])
        size = os.path.getsize(path)
        print(f"  [{count:2d}/78] {card['id']:20s} {name:10s} {size:>5}B")

    back = generate_card_back()
    print(f"  [  ] CardBacks.png ({os.path.getsize(back)}B)")
    print(f"\nDone. {count} cards + 1 back in {OUT_DIR}")


if __name__ == "__main__":
    main()

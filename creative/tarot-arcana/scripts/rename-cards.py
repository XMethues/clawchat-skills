#!/usr/bin/env python3
"""
Rename downloaded RWS card images to match the old HTML naming convention.

Old HTML convention:
  Major: {pad2(number)}-{nameNoSpaces}.jpg  (e.g. 01-TheMagician.jpg)
  Minor: {Suit}{pad2(number)}.jpg            (e.g. Wands01.jpg, Cups02.jpg)
  Back:  CardBacks.jpg

Usage:
  cd /opt/data/tarot-arcana-app
  uv run python3 /path/to/scripts/rename-cards.py
"""

import json
import os
from PIL import Image

SRC_DIR = "/opt/data/skills/creative/tarot-arcana/liveware/static/cards"
DECK_JSON = "/opt/data/skills/creative/tarot-arcana/data/deck.json"

with open(DECK_JSON) as f:
    deck = json.load(f)

SUIT_CAPITAL = {
    "wands": "Wands",
    "cups": "Cups",
    "swords": "Swords",
    "pentacles": "Pentacles",
}

# Convert CardBacks.png -> CardBacks.jpg
back_src = os.path.join(SRC_DIR, "CardBacks.png")
back_dst = os.path.join(SRC_DIR, "CardBacks.jpg")
if os.path.exists(back_src):
    img = Image.open(back_src).convert("RGB")
    img.save(back_dst, "JPEG", quality=92)
    print(f"  CardBacks.png -> CardBacks.jpg ({os.path.getsize(back_dst)} bytes)")

renamed = 0
for card in deck:
    cid = card["id"]
    name = card.get("name", "")
    number = card.get("number")
    is_major = card["arcana"] == "major"
    suit = card.get("suit", "")

    src = os.path.join(SRC_DIR, f"{cid}.png")
    if not os.path.exists(src):
        print(f"  SKIP {cid}: source not found")
        continue

    if is_major:
        name_no_space = name.replace(" ", "")
        dst_name = f"{str(number).zfill(2)}-{name_no_space}.jpg"
    else:
        suit_cap = SUIT_CAPITAL.get(suit, suit.capitalize())
        dst_name = f"{suit_cap}{str(number).zfill(2)}.jpg"

    dst = os.path.join(SRC_DIR, dst_name)
    img = Image.open(src).convert("RGB")
    img.save(dst, "JPEG", quality=92)
    print(f"  {cid:25s} -> {dst_name} ({os.path.getsize(dst)} bytes)")
    renamed += 1

print(f"\nDone: {renamed} cards + 1 back renamed")

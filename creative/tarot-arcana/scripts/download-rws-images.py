#!/usr/bin/env python3
"""Download RWS tarot card images from the public tarotcardapi.

Maps all 78 card IDs from deck.json to the API's image filenames and
downloads them as 240x336 PNGs. The API serves public-domain Rider-Waite-Smith
artwork.

Usage:
    cd /opt/data/tarot-arcana-app
    uv run python3 scripts/download-rws-images.py

Output: liveware/static/cards/<card-id>.png (78 files, ~90-200 KB each)

Name mapping detail:
  - Major arcana: thefool, themagician, thehighpriestess, ...
  - Minor arcana: aceofwands, twoofcups, pageofswords, ...
  - Exception: TheLovers.jpg (capital L, .jpg not .jpeg)
"""

import json
import os
import urllib.request

BASE_URL = "https://tarotcardapi.onrender.com/tarotdeck"
OUT_DIR = "/opt/data/skills/creative/tarot-arcana/liveware/static/cards"
DECK_JSON = "/opt/data/skills/creative/tarot-arcana/data/deck.json"

# Mapping from deck.json card names to API image filenames
NAME_TO_API = {
    # Major Arcana
    "The Fool": "thefool",
    "The Magician": "themagician",
    "The High Priestess": "thehighpriestess",
    "The Empress": "theempress",
    "The Emperor": "theemperor",
    "The Hierophant": "thehierophant",
    "The Lovers": "TheLovers",
    "The Chariot": "thechariot",
    "Fortitude": "thestrength",
    "The Hermit": "thehermit",
    "Wheel Of Fortune": "wheeloffortune",
    "Justice": "justice",
    "The Hanged Man": "thehangedman",
    "Death": "death",
    "Temperance": "temperance",
    "The Devil": "thedevil",
    "The Tower": "thetower",
    "The Star": "thestar",
    "The Moon": "themoon",
    "The Sun": "thesun",
    "The Last Judgment": "judgement",
    "The World": "theworld",
    # Wands
    "Ace of Wands": "aceofwands",
    "Two of Wands": "twoofwands",
    "Three of Wands": "threeofwands",
    "Four of Wands": "fourofwands",
    "Five of Wands": "fiveofwands",
    "Six of Wands": "sixofwands",
    "Seven of Wands": "sevenofwands",
    "Eight of Wands": "eightofwands",
    "Nine of Wands": "nineofwands",
    "Ten of Wands": "tenofwands",
    "Page of Wands": "pageofwands",
    "Knight of Wands": "knightofwands",
    "Queen of Wands": "queenofwands",
    "King of Wands": "kingofwands",
    # Cups
    "Ace of Cups": "aceofcups",
    "Two of Cups": "twoofcups",
    "Three of Cups": "threeofcups",
    "Four of Cups": "fourofcups",
    "Five of Cups": "fiveofcups",
    "Six of Cups": "sixofcups",
    "Seven of Cups": "sevenofcups",
    "Eight of Cups": "eightofcups",
    "Nine of Cups": "nineofcups",
    "Ten of Cups": "tenofcups",
    "Page of Cups": "pageofcups",
    "Knight of Cups": "knightofcups",
    "Queen of Cups": "queenofcups",
    "King of Cups": "kingofcups",
    # Swords
    "Ace of Swords": "aceofswords",
    "Two of Swords": "twoofswords",
    "Three of Swords": "threeofswords",
    "Four of Swords": "fourofswords",
    "Five of Swords": "fiveofswords",
    "Six of Swords": "sixofswords",
    "Seven of Swords": "sevenofswords",
    "Eight of Swords": "eightofswords",
    "Nine of Swords": "nineofswords",
    "Ten of Swords": "tenofswords",
    "Page of Swords": "pageofswords",
    "Knight of Swords": "knightofswords",
    "Queen of Swords": "queenofswords",
    "King of Swords": "kingofswords",
    # Pentacles
    "Ace of Pentacles": "aceofpentacles",
    "Two of Pentacles": "twoofpentacles",
    "Three of Pentacles": "threeofpentacles",
    "Four of Pentacles": "fourofpentacles",
    "Five of Pentacles": "fiveofpentacles",
    "Six of Pentacles": "sixofpentacles",
    "Seven of Pentacles": "sevenofpentacles",
    "Eight of Pentacles": "eightofpentacles",
    "Nine of Pentacles": "nineofpentacles",
    "Ten of Pentacles": "tenofpentacles",
    "Page of Pentacles": "pageofpentacles",
    "Knight of Pentacles": "knightofpentacles",
    "Queen of Pentacles": "queenofpentacles",
    "King of Pentacles": "kingofpentacles",
}


def download_and_convert(url, out_path):
    """Download JPEG and save as PNG, resized to 240x336."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
        from PIL import Image
        import io
        img = Image.open(io.BytesIO(data))
        img = img.resize((240, 336), Image.LANCZOS)
        img.save(out_path, "PNG")
        return os.path.getsize(out_path)
    except Exception as e:
        print(f"  FAILED: {e}")
        return 0


def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    with open(DECK_JSON) as f:
        deck = json.load(f)

    total = len(deck)
    success = 0

    for card in deck:
        cid = card["id"]
        name = card.get("name", "")

        if name not in NAME_TO_API:
            print(f"  SKIP {cid}: no mapping for '{name}'")
            continue

        slug = NAME_TO_API[name]
        ext = ".jpg" if slug == "TheLovers" else ".jpeg"
        url = f"{BASE_URL}/{slug}{ext}"
        out_path = os.path.join(OUT_DIR, f"{cid}.png")

        if os.path.exists(out_path) and os.path.getsize(out_path) > 1000:
            print(f"  EXISTS {cid}: {name} -> {os.path.getsize(out_path)} bytes")
            success += 1
            continue

        print(f"  DOWNLOAD {cid}: {name} -> {url}")
        size = download_and_convert(url, out_path)
        if size:
            print(f"    OK: {size} bytes -> {cid}.png")
            success += 1
        else:
            print(f"    FAILED: {cid}")

    print(f"\nDone: {success}/{total} cards downloaded")


if __name__ == "__main__":
    main()

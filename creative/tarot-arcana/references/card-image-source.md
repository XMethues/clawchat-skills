# Card Image Source: tarotcardapi

## Source

Card faces are downloaded from the public [tarotcardapi](https://github.com/krates98/tarotcardapi) at `https://tarotcardapi.onrender.com`.

The API serves public-domain Rider-Waite-Smith tarot card artwork (Pamela Colman Smith's illustrations, published in 1909, now in the public domain).

## API Endpoints

| Endpoint | Purpose |
|----------|---------|
| `GET /tarotdeck/<slug>.jpeg` | Card image (JPEG) |
| `GET /cards/` | Card metadata with image paths |

## API Image File Naming

All 78 cards use lowercase hyphenated names:
- `thefool.jpeg`, `themagician.jpeg`, ... (major arcana)
- `aceofwands.jpeg`, `twoofcups.jpeg`, `pageofswords.jpeg`, ... (minor arcana)
- Exception: `TheLovers.jpg` (capital L, `.jpg` not `.jpeg`)

## Mapping to deck.json IDs

The download script (`scripts/download-rws-images.py`) maps `deck.json` card names to API slugs via `NAME_TO_API`. Notable mappings:

| deck.json name | API slug | Reason |
|----------------|----------|--------|
| `Fortitude` | `thestrength` | RWS deck calls it "Strength" |
| `Wheel Of Fortune` | `wheeloffortune` | Lowercase, no "The" |
| `The Last Judgment` | `judgement` | RWS calls it "Judgement" |
| `The Lovers` | `TheLovers` | Only card with capital letter in API |

## Frontend Naming Convention (old HTML)

The frontend does NOT use the API's naming directly. Instead, it uses the convention from the original vanilla-HTML version of the app:

| Arcana | Convention | Examples |
|--------|-----------|----------|
| Major | `{pad2(number)}-{nameNoSpaces}.jpg` | `00-TheFool.jpg`, `01-TheMagician.jpg` |
| Minor | `{Suit}{pad2(number)}.jpg` | `Wands01.jpg`, `Cups02.jpg`, `Swords11.jpg` |
| Back | `CardBacks.jpg` | CardBacks.jpg |

Court card number mapping:
- Page = 11 (e.g. `Wands11.jpg`)
- Knight = 12 (e.g. `Cups12.jpg`)
- Queen = 13 (e.g. `Pentacles13.jpg`)
- King = 14 (e.g. `Swords14.jpg`)

Suit capitalization:
- `wands` → `Wands`
- `cups` → `Cups`
- `swords` → `Swords`
- `pentacles` → `Pentacles`

## Regenerating Images (original download sequence)

This was the original sequence for downloading from the tarotcardapi. It's preserved for reference but **superseded by user-provided image zips** (see SKILL.md "Replacing Card Images from a User Zip"):

```bash
cd /opt/data/tarot-arcana-app

# 1. Download real RWS images (PNG, keyed by deck.json id)
rm liveware/static/cards/*.png  # remove old generated images
uv run python3 scripts/download-rws-images.py

# 2. Generate card back (PNG) — only needed if no real back provided
uv run python3 scripts/generate-card-back.py

# 3. Create JPG copies with old-HTML naming convention
uv run python3 scripts/rename-cards.py

# 4. Build SolidJS app
npx vite build
```

## Replacing Images from User Zip

When the user provides a complete set of card images (78 faces + back) via zip:

1. Download and extract the zip
2. Rename files to match deck.json naming (see "Naming Convention Pitfalls" below)
3. Copy all JPG files to `liveware/static/cards/` (overwrite existing)
4. Clean up old PNG files
5. No build step needed — images are served as static files

## Naming Convention Pitfalls

The deck.json uses different names than standard RWS for two cards. When a user provides replacement images, these files may need renaming:

| deck.json name | Standard RWS name | File in zip | Rename to |
|----------------|-------------------|-------------|-----------|
| `Fortitude` | `Strength` | `08-Strength.jpg` | `08-Fortitude.jpg` |
| `The Last Judgment` | `Judgement` | `20-Judgement.jpg` | `20-TheLastJudgment.jpg` |

If you forget this step, the app will show broken images for cards 8 and 20 (the `cardImage()` function generates filenames from deck.json names).

## Current Image Dimensions

- All card images (faces + back): **300×527** pixels, JPEG, RGB mode
- CSS `aspect-ratio: 300 / 527` matches exactly
- Previous generation was 240×336 — the CSS was already prepared for 300/527 before the upgrade

If the API becomes unavailable, fall back to:
1. Wikimedia Commons major arcana JPGs (22 cards available at `https://upload.wikimedia.org/wikipedia/commons/`)
2. Generate placeholder images with Pillow (fallback approach)

## Cache Busting

After updating card images, the tunnel CDN may cache old versions. There are two cases:

### Hashed assets (JS/CSS via Vite)

Vite generates content-hashed filenames (`index-<hash>.js`). The CDN serves the old hash until a rebuild produces a new hash. This is handled automatically — just rebuild.

### Static images (card faces, card back)

Card images are served at fixed paths (`/cards/CardBacks.jpg`, `/cards/00-TheFool.jpg`). Replacing the file on disk does NOT change its URL — browsers and CDN keep serving the old cached version.

**Permanent fix — add a cache-busting query param to the source code:**

1. Update `cardBackImage()` in `src/App.tsx`:
   ```ts
   function cardBackImage(): string {
     return '/cards/CardBacks.jpg?v=2'
   }
   ```

2. Update the `imgBack` reference in `src/data/cards.ts`:
   ```ts
   imgBack: 'cards/CardBacks.jpg?v=2',
   ```

3. Rebuild: `npx vite build`

4. If the CDN still serves the old version for card face images, add `?v=N` to the `cardImage()` function similarly.

**Quick verification:**
```bash
curl -s -o /dev/null -w "%{size_download} bytes\n" "https://<app>.apps.clawling.io/cards/CardBacks.jpg"
```
Compare the size to the local file. If they match, the new version is served.

Users may still need to hard-refresh (Cmd/Ctrl+Shift+R) in their browser if the browser itself cached the old response before the CDN was updated.

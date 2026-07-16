# Ingesting image content from chat links

The XHS publish flow (`prepare --request`) expects local file paths for images. When the user shares slide content (cover, body slides) via a chat link rather than a local file, the agent must fetch the bytes locally before they can be uploaded. This reference covers the common failure modes and the working pattern.

## The failure mode

`vision_analyze` accepts a URL, but:

1. Many chat CDNs (`media.clawling.chat`, `cdn.discordapp.com`, etc.) require headers the agent's fetcher may not send, so the URL path returns 403 or times out.
2. Some platforms return `text/html` (a "this image has expired" stub) for cached / signed URLs.
3. `vision_analyze` on a bad URL fails silently in some wrappers and returns an empty description.

Telling the user "I can't see your image" without trying a workaround is a non-answer.

## Working pattern

```bash
mkdir -p /tmp/xhs-batch && cd /tmp/xhs-batch
curl -sSL --max-time 25 -o slide01.png "<url-from-user>"
# Verify it actually downloaded a PNG and not an HTML stub
ls -la slide01.png      # expect > 50 KB for a real slide
head -c 8 slide01.png | od -An -c   # expect PNG header "\211 P N G"
```

Then pass the **local path** to the vision tool, not the URL:

```
vision_analyze(image_url="/tmp/xhs-batch/slide01.png", question="...")
```

If a single attempt fails, retry the `curl` with `--retry 3 --retry-delay 2`. Some chat CDNs rate-limit aggressively; a single-shot `curl` may time out even when the URL is valid.

## Pitfalls

### Don't pass the chat URL directly to `vision_analyze`

The agent's vision endpoint and `curl` may use different network paths. `vision_analyze` on a URL that fails locally will not surface the failure clearly to the agent — it returns an empty or stub description, and the agent proceeds to publish based on fabricated content. Always `curl` first, verify the file size and header, then analyze the local copy.

### Don't trust file size alone

A 1 KB file with a PNG header is still a broken image. Spot-check the header bytes:

```bash
head -c 8 <file> | od -An -c | tr -d ' '
# Real PNG:  211 P N G \r \n 26 \n
# HTML stub: < ! D O C T Y
```

If the header check fails, the URL is dead — re-request or ask the user.

### Match the extension to the actual bytes, not the filename

`xhs-operator` only checks the extension (`.jpg`, `.jpeg`, `.png`, `.webp`) — it does NOT sniff magic bytes. Files saved from chat CDNs, screenshot pipelines, or tools that re-encode without re-extension will keep their old suffix. Real-world failure mode seen in production:

- File is named `slide.png` but the bytes start with `FF D8 FF E0` (JFIF/JPEG).
- `validateRequest` accepts it (extension matches).
- `setInputFiles` hands it to `<input type="file">`; the upload backend / decoder fails on the actual codec and the creator UI shows **上传失败**.
- Worker throws on the first `上传失败|重新上传` match → `failed`, `draftSaved: true`, empty slots.

**Fix**: rename to match the bytes; do not re-encode (no quality loss, no `imagemagick` needed):

```bash
for f in images/*.png; do
  head -c 3 "$f" | od -An -tx1 | tr -d ' \n' | grep -q '^ffd8ff' && mv "$f" "${f%.png}.jpg"
done
```

Verify by re-checking headers after the rename loop. `validateRequest` still passes (`jpg` is allowed) and the upload succeeds because the bytes are now genuinely JPEG. Renaming is reversible — original bytes are untouched; if the file really was PNG and you mis-detected, `mv` it back.

This is the most common silent `failed` cause after the auth/peer-dep basics are resolved. Check it **before** the first `prepare`, not after a failure.

### Don't fetch then forget the cleanup

If the run is aborted or the user pivots, `/tmp/xhs-batch` accumulates. Either wipe after a successful publish or scope fetches into a per-run subdir.

### Don't mix CDN order

When the user sends multiple images in one message, fetch them all before analyzing any. The order in which they arrive from the CDN may not match the order the user intended. Rename by the user's stated sequence (e.g., `01-cover.png`, `02-intro.png`), not by alphabetical sort of the URL slug.
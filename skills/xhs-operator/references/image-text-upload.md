# Image-and-text note upload workflow

Use this workflow to upload images, fill an image-and-text note, configure its settings, preview it, and then publish immediately or on a schedule after explicit confirmation.

## Collect content

Ask one question at a time when required information is missing.

1. Propose a title, body, ordinary topics, and conservative settings.
2. Ask whether to use the proposal. If rejected, require concrete replacement content.
3. Before running `prepare`, show the finalized content and settings.

Defaults: original statement off, remix off, body copying off, public visibility, scheduling off, no collection, and no location.

## Options

- Images: 1-18 existing JPG, JPEG, PNG, or WebP files in the supplied order. Never crop, convert, or compress them.
- Title: required, up to 20 characters.
- Body and ordinary topics: up to 1000 characters combined. Format topics as `#topic-one #topic-two`. Activity topics are not available.
- Original statement: on or off; default off.
- Remix: on or off; default off.
- Body copying: on or off; default off.
- Visibility: `公开可见`, `仅自己可见`, or `仅互关好友可见`; default `公开可见`. Recommend `仅自己可见` for tests.
- Scheduled publishing: off, or a Beijing time (`Asia/Shanghai`) in `YYYY-MM-DD HH:mm`; default off.
- Collection: none, an existing collection by exact name, or a new collection. Creating one requires separate confirmation, a name up to 20 characters, and an optional description up to 50 characters.
- Location: none, or one unique location. If candidates are ambiguous, show them and ask for the exact name and address.

## Pre-flight validation (do this before `prepare`)

`xhs-operator` validates the request with `lib.mjs:validateRequest` and **throws on the first violation**. If you skip the pre-check, the worker exits at `starting` and the user's time is wasted on a doomed run. Validate locally first:

```bash
node -e '
import("/opt/data/skills/xhs-operator/scripts/lib.mjs").then(m => {
  const v = m.validateRequest(JSON.parse(require("fs").readFileSync(process.argv[1],"utf8")));
  console.log("title code points:", [...v.title].length, "/20");
  console.log("body+topics code points:", [...v.content].length, "/1000");
  console.log("image count:", v.images.length, "/18");
  console.log("topics:", v.topics);
}).catch(e => { console.error("INVALID:", e.message); process.exit(1); });
' /absolute/path/request.json
```

Things this catches that are easy to get wrong:

- **Title length is counted in Unicode code points, not bytes or visible characters.** `AI 接管 Office ①:选中哪里,就改哪里` is 22 code points (each ASCII letter, space, `①`, `:`, `,` counts as 1) — over the 20 limit and will throw at validate. Trim or rewrite before running `prepare`.
- **Body + topics combined are capped at 1000 code points**, not separately. Topics are appended as `#t1 #t2 ...` after the body, so a long topic list eats into the body budget.
- **Image extensions are checked**: only `.jpg`, `.jpeg`, `.png`, `.webp`. Anything else throws. Don't pre-rename to `.tmp` or pass a path without an extension.
- **Verify image magic bytes match the extension before `prepare`.** `xhs-operator` does not sniff bytes — only the suffix. Files saved from chat CDNs, screenshot tools, or pipelines that re-encode without re-extension will keep their old name; downstream upload via `setInputFiles` then fails and the creator UI shows **上传失败**. See `cloud-media-fetch.md` for the byte-sniff + rename recipe, and "Diagnosing 上传失败" below for the inline one-liner.

If validation fails, edit the request JSON and re-validate. **Never** edit the request after `prepare` starts — the worker copies it into the run dir and ignores the source file.

## Prepare a preview

Create a UTF-8 request JSON in the current workspace. Use absolute image paths:

```json
{
  "images": ["/absolute/path/one.jpg"],
  "title": "不超过 20 个字符",
  "body": "正文",
  "topics": ["<topic one>", "<topic two>"],
  "settings": {
    "original": false,
    "allowRemix": false,
    "allowCopy": false,
    "visibility": "仅自己可见",
    "scheduledAt": null,
    "collection": null,
    "location": null
  }
}
```

Append `topics` to `body` with spaces between tags. `scheduledAt` is `null` or Beijing time in `YYYY-MM-DD HH:mm`.

For an existing collection, use `{ "name": "<exact name>" }`. To create one after separate confirmation, add `"create": true`, `"confirmed": true`, a name of at most 20 characters, and an optional description of up to 50 characters.

For a location, use `{ "name": "<exact name>" }`. If multiple candidates are returned, add the selected candidate's displayed address. Do not invent collection or location choices from examples.

Start preparation:

```bash
node ${HERMES_SKILL_DIR}/scripts/xhs-operator.mjs prepare --request /absolute/path/request.json
node ${HERMES_SKILL_DIR}/scripts/xhs-operator.mjs status --run <run-id>
```

When status becomes `awaiting_confirmation`, send `summary.json` and `preview.png` to the user. Use `[[as_document]]` when screenshot compression would make inspection difficult.

### `preview.png` only covers the current viewport, not the full publish page

`worker.mjs:screenshot()` is hardcoded to `fullPage: false`. The publish page is taller than a 1440×1000 viewport, so `preview.png` typically shows the **bottom half** — the content-settings panel (visibility, original-statement, scheduled, draft / publish buttons) — and clips off the **top** (title field, image grid, body editor, topics). The full `summary.json` is reliable for verifying title / body / topics / image count / settings, so the user does not strictly need to see the top half to confirm content.

If they ask for a complete top-of-page screenshot, the temptation is to spin up a second browser with the same `storageState` and `fullPage: true`-screenshot the publish page. **Do not do this.** Each fresh browser process is a new session from the creator side, and on this kind of account it triggers a `遇到问题` overlay, `net::ERR_CONNECTION_CLOSED` on most static assets, and (worse) raises risk-control state that may follow the real account on subsequent publishes from the legitimate worker.

If the user genuinely wants a complete top-of-page screenshot, the right answers (in order of safety):

1. Tell them the bottom-half `preview.png` plus `summary.json` together prove the form is correct.
2. Have them open the creator center themselves — the worker has saved a draft (or will on confirmation expiry), and the draft editor is the same UI rendered in their normal browser session.
3. If a top screenshot is required, extend `worker.mjs:screenshot()` to accept `fullPage: true` and use it in a *fresh* run, but never in parallel with the live one.

### Deliver `MEDIA:` paths inline in the reply, not just in thinking

When the skill tells you to "send the user `preview.png`" or the QR reference tells you to "deliver `qr.png`", that delivery has to land in the **assistant reply text** as a literal line of the form `MEDIA:/absolute/path`. Referencing the path in internal reasoning without emitting the line means the chat platform never gets the attachment, and the user sees "where is the image?" even though you wrote the path somewhere. If you cannot or will not emit `MEDIA:` for any reason (sanitization, transient platform bug), say so explicitly — "I am not sending the image; here is the path on disk" — rather than implying it was attached.

### Confirm token format

`state.json.confirmationPhrase` is `确认发布 <TOKEN>`. `TOKEN` is the 8-character uppercase hex value from `state.json.confirmationToken` (sha256 over runId + request, first 8 hex chars, uppercased). Both the phrase and the token are stored; pass the **bare token** (no `确认发布 ` prefix) to `confirm --token`. The phrase is for the human; the token is for the command.

## Confirm and publish

Publish only after the user replies with the exact `confirmationPhrase` from `state.json`. Extract its short task ID and run:

```bash
node ${HERMES_SKILL_DIR}/scripts/xhs-operator.mjs confirm --run <run-id> --token <task-id>
```

Any content or setting change requires a new request and new run. An old confirmation never applies.

The worker waits 15 minutes for confirmation. If confirmation expires, it attempts `暂存离开` and closes the browser.

### Why 15 minutes? (and why the agent cannot reach into the worker)

This is the most common user question at the `awaiting_confirmation` stage. Pre-empt it in your reply when you transition into awaiting_confirmation — the user is staring at a worker they cannot see and they will ask.

- **The 15-minute window is a deliberate design choice by the wrapper**, not a network constraint. It exists to prevent accidental publish clicks — the script author wanted a human-approval buffer before the script presses the irreversible "发布" button on Xiaohongshu.
- **The worker is a detached child process** (`spawn(..., { detached: true, stdio: "ignore" })`). Once it returns a `runId`, it lives in its own process tree with its own Playwright `page` in its own memory. The parent agent cannot drive its browser, click its buttons, take over its session, or send it signals that are not in its protocol.
- **The only communication channel is `control.json`** written into the run directory. `worker.mjs` only branches on `control.action === "publish"` and a matching token; any other action throws "确认令牌无效". There is no `action: "save_draft"` branch — the auto-save branch lives only inside the 15-minute expiry path.
- **Practical implications to surface to the user:**
  - "Can you click 暂存 now?" → No. The worker only attempts `暂存离开` after the 15-minute timer expires. Saving sooner means either waiting, or accepting that opening a fresh browser session raises account risk (see "preview.png only covers the current viewport" pitfall above).
  - "Can you operate the worker browser manually?" → No. It is a sealed process. Do not attempt to attach via signals, debugger ports, or shared storage state.
  - "Why does the creator draft box still look empty?" → Because the worker has not written to the creator draft box yet. Form contents live only in the worker's browser tab until either `confirm` runs (publish) or the 15-minute timer expires (auto-save). The creator center's "草稿箱" only shows notes that have been explicitly saved by the worker or by a manual click in the user's own session.

## Result handling

Poll status and interpret terminal states exactly:

- `published`: report success with the success screenshot.
- `confirmation_expired`: report whether `draftSaved` succeeded; require a new preview and confirmation.
- `failed`: publishing was not clicked; report `draftSaved` and diagnostics.
- `publish_unknown`: never click publish again and never save another draft. Ask the user to inspect the creator content list.
- `risk_verification_required`: stop all automation.

Do not claim success from a click alone.

## Failure at the image-upload step — what is in the creator draft

The most common `failed` state in practice is the worker throwing inside `uploadImages`. `worker.mjs:assertImagesUploaded` matches `上传失败|重新上传` in the page body and throws on the first occurrence. The terminal `state.json` shows `failed`, `draftSaved: true`, and an `errorScreenshot` of the creator page.

What the user sees in their creator center when this happens:

- **Images may be partially or fully present** depending on where the failure hit. If the failure was on the very first image, the editor is usually empty. If it was later (e.g., the 6th of 8), the first N images are still in the editor. The preview pane on the right may render the first uploaded image as the cover even though the editor slot is empty.
- **Title, body, and topics are NOT filled.** `worker.mjs` calls `fillTitle` / `fillBody` / `fillTopics` only after `uploadImages` returns successfully. A failed upload leaves the editor empty of text even though the worker wrote `draftSaved: true`.
- **A 草稿 (draft) row exists in the creator center.** This is independent of new runs — retrying `prepare` creates a *new* run and a *new* draft, leaving the old one behind. After two retries the creator has three drafts to clean up manually.

When reporting a `failed` upload-step state, tell the user all three things explicitly:

1. Whether any images made it into the editor (count visible in the editor's `1/18 … 8/18` slot counter, or in `error.png`).
2. That title/body/topics are NOT in this draft — they only land if upload succeeds.
3. That retrying `prepare` creates a fresh draft; the old one will need manual cleanup from the creator center, or a `cleanup --all --confirm` once the user confirms.

### Retry protocol for upload-step failures

- **Single retry is reasonable.** Image upload via `setInputFiles` to `ros-upload.xiaohongshu.com` is sensitive to transient 5xx and rate limits. A second `prepare` run often succeeds where the first failed.
- **Do not retry blindly more than once.** Two consecutive `failed` uploads with no diagnostic change (same `error` string in `state.json`) usually means the browser/CDN is rejecting this account/network combo and a third attempt will only add more stale drafts.
- **Do not lower the image count to "try with fewer images" without asking.** The user provided a specific set in a specific order; do not silently change the publish intent. Surface the failure and ask.
- **If the error string contains `net::ERR_FAILED`, `ERR_NETWORK_CHANGED`, or `ERR_CONNECTION_RESET`**, it is almost certainly network-side, not content-side. Confirm network reachability before retrying.
- **If the error contains `RISK_VERIFICATION_REQUIRED`**, do not retry. Surface to the user and stop.

### Diagnosing "上传失败" — extension vs magic bytes

If `state.json.error` is `图片上传请求失败: net::ERR_FAILED` or the user-side screenshot shows **上传失败** on the very first image, the most common root cause is the image bytes not matching the file extension. Quick diagnostic:

```bash
for f in images/*; do
  ext="${f##*.}"; head=$(head -c 3 "$f" | od -An -tx1 | tr -d ' \n')
  case "$head" in
    ffd8ff) real="jpg" ;;
    89504e) real="png" ;;
    52494646) real="webp" ;; # RIFF...WEBP, also has "WEBP" at offset 8
    *) real="?" ;;
  esac
  [ "$ext" != "$real" ] && echo "MISMATCH: $f ext=$ext bytes=$real"
done
```

Any `MISMATCH` line means rename to match the bytes (`mv` keeps the file unchanged; do not re-encode). Then re-run `prepare` with a fresh request JSON pointing at the renamed files. See `cloud-media-fetch.md` for the full pattern.
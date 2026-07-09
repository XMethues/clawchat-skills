---
name: tarot-arcana
display_name: Tarot Arcana
description: Tarot card drawing and interpretation — draws real cards via a local script, never fabricates results. Supports one-card and three-card spreads with structured psychological analysis.
category: creative
version: 0.22.3
metadata:
  hermes:
    tags: [Creative, Tarot, Reflection, Liveware]
    related_skills: [liveware-app]
---

# Tarot Arcana

Tarot Arcana has two layers. The primary layer is a standalone tarot-reader skill: the agent draws real cards via a bundled local script and interprets one-card or three-card spreads with grounded psychological analysis. The secondary layer is an optional liveware web app: it is an interface for collecting or displaying readings, but the interpretation still belongs to the agent using this skill.

## Design Model

1. **Core tarot-reader skill** — the source of truth for drawing cards, loading interpretation/spread references, keeping readings reflective, and producing the final reading. This layer must work independently in a normal chat without liveware.
2. **Liveware add-on** — an optional browser UI and delivery bridge. Liveware may collect the question/card data and display the result, but it must delegate interpretation back to a Hermes agent using `tarot-arcana`; it should not become a separate tarot-reading engine with its own rules.

When liveware calls the Hermes API Server, the API-server agent should load/use this skill and its references before writing the interpretation.

## When to Use

Use this skill when the user wants to:

- Draw tarot cards for a reflective reading
- Interpret a one-card or three-card spread
- Explore a situation through psychological, non-prophetic tarot framing
- Follow up on a reading produced by the liveware web app

Do not present tarot as proof, diagnosis, professional advice, or guaranteed prediction. For high-stakes or third-party questions, answer in a reflective way that focuses on the user's choices, feelings, preparation, and boundaries.

## Quick Reference

| Task | Command or file |
|------|-----------------|
| Draw one card | `node scripts/draw-tarot.mjs --spread one_card --question "<question>"` |
| Draw three cards | `node scripts/draw-tarot.mjs --spread three_card --question "<question>"` |
| Disable reversals | Add `--reversals false` |
|| Interpretation rules | `skill_view(name='tarot-arcana', file_path='references/interpretation-rules.md')` |
| Spread rules | `skill_view(name='tarot-arcana', file_path='references/spreads.md')` |
| Card image source | `skill_view(name='tarot-arcana', file_path='references/card-image-source.md')` |\n| Question templates | `skill_view(name='tarot-arcana', file_path='references/question-framework.md')` |
|| Question elicitation loop | Step 0 in Procedure below |
| Install liveware (first time) | `bash liveware/scripts/setup.sh` (from skill dir) |
| Activate liveware (daily) | `bash liveware/scripts/start.sh` (from skill dir) |
| Activate liveware (daily) | `bash liveware/scripts/start.sh` (from skill dir) |
| Generate card back PNG | `cd /opt/data/tarot-arcana-app && uv run python3 scripts/generate-card-back.py` |
| Download real RWS card images | `cd /opt/data/tarot-arcana-app && uv run python3 scripts/download-rws-images.py` |
| Rename cards to old-HTML convention | `cd /opt/data/tarot-arcana-app && uv run python3 scripts/rename-cards.py` |

### Local dependency

### Local dependency

Run the command examples from the `tarot-arcana` skill directory so relative `scripts/...` paths resolve correctly. The draw script requires `node` to be available in `PATH`, uses only Node.js built-ins, and does not require npm packages. If `node` is missing, tell the user Node.js is required before drawing cards.

## Procedure

### 0. Guide the user to formulate a good question (preferred: use liveware)

When someone asks for a tarot reading in conversation, **guide them through a structured question-formulation loop before drawing any cards**. The preferred flow leads them to the liveware web app with the question pre-filled.

**Why this step exists:** Most people don't know how to ask tarot. A vague question produces a vague reading. This step helps the user arrive at a question that has **specific context, a timeframe, and actionable meaning** — the three qualities of a good tarot question.

**The elicitation loop:**

Ask the user these questions one at a time (not all at once). Let them answer each before moving to the next:

1. **Theme** — "你想看哪个方面？感情、事业、还是别的？"
2. **Situation** — "目前情况到哪一步了？简单说说背景。"
3. **Core confusion** — "你真正纠结的是什么？卡在哪里？"
4. **Timeframe** — "想看多长时间的范围？一周、一个月、还是三个月？"
5. **Focus** — "你希望塔罗帮你看清什么？现状、阻碍、趋势、选择，还是行动建议？"

**After the question is clear:**

Generate the liveware URL with the question pre-filled and send it to the user. The URL format is:

```
https://<app-id>.apps.clawling.io/?question=<url-encoded-question>&lang=<zh|en>
```

For example:

```
https://app-ac73441de2f9f491.apps.clawling.io/?question=未来三个月，我和团队合作的关键阻碍在哪里？&lang=zh
```

Tell the user the web app is ready with their question pre-filled. They can open the link, select cards, and get a full interpretation.

**Fallback (liveware unavailable):** If the liveware web app is not running or unreachable, proceed with Step 1 and draw cards directly in chat using the local draw script. The question guidance loop still applies — formulate a clear question first.

**What to avoid in the loop:**
- Do not ask all five questions at once — the user will feel overwhelmed
- Do not pressure the user to share overly private details
- If the user seems unsure after a few rounds, offer a simple template: "关于【某件事】，我目前真正处在什么状态？"

### 1. Choose the reading mode

Match the spread to the user's request:

- **one_card** — use for a focused reminder, immediate theme, or simple reflective prompt.
- **three_card** — use for a fuller situation arc: current situation → obstacle → advice.

Ask a brief clarifying question only if the user's question is too vague to choose a spread or draw responsibly.

### 2. Load the reference files

Before interpreting, load these references:

1. `references/interpretation-rules.md` — the 10-step interpretation sequence, reading-depth rules, situation-reading rules, reflective questions, golden rules, and minimal safety/tone boundaries
2. `references/spreads.md` — spread types, position meanings, and when to use each

### 3. Draw real cards

Run the bundled script from the `tarot-arcana` skill directory with the selected spread and the user's question:

- For **one_card**:

  ```bash
  node scripts/draw-tarot.mjs --spread one_card --question "<question>"
  ```

- For **three_card**:

  ```bash
  node scripts/draw-tarot.mjs --spread three_card --question "<question>"
  ```

`--question` is required so the returned JSON carries the user's question for interpretation context, saved-reading archives, and liveware handoff continuity. It does not seed or steer the random card draw.

The script returns structured JSON with:

- `mode`
- `readingId`
- `spread`
- `question`
- `reversalsEnabled`
- `cards`
- `drawTimestamp`

Each card includes `position`, `positionName`, `positionDescription`, `cardId`, `name`, `arcana`, `suit`, `number`, `orientation`, `keywords`, `summary`, and `summaryModern`.

Never invent cards, positions, or orientations. Interpret only the script output.

### 4. Interpret in the required order

Apply the sequence from `references/interpretation-rules.md`:

1. **User's question** — identify what the user is actually asking and reframe if needed.
2. **Spread type** — one_card or three_card.
3. **Position meaning** — position takes priority over general card meaning.
4. **Card name** — identify each card and whether it is major or minor arcana.
5. **Orientation** — upright/reversed modifies the energy.
6. **Keywords** — use them as shorthand anchors.
7. **Summary** — apply the card meaning in context.
8. **Situation reading** — identify the larger pattern, relationship structure, choice, cost, or blind spot behind the stated question.
9. **Synthesis** — connect all cards into one coherent narrative.
10. **Actionable advice** — translate the final insight into grounded next steps and, for substantial readings, one to three reflective questions.

### 5. Apply spread rules

- **one_card**: position is `current_reminder`. Focus on one core theme and do not over-expand.
- **three_card**: positions are `current_situation` → `obstacle` → `advice`. Connect the cards into a single narrative arc. The advice card must become concrete guidance, and the final response should name the user's agency, choices, and costs rather than only predicting an outcome.

### 6. Keep the reading reflective and useful

Apply the minimal boundaries in `references/interpretation-rules.md` without over-restricting the experience:

- Answer the user's real concern whenever possible.
- Do not present tarot as proof, diagnosis, professional instruction, or guaranteed outcome.
- For high-stakes or third-party questions, focus on the user's feelings, options, boundaries, preparation, and next conversations.
- Avoid fear, shame, and manufactured urgency.

## Liveware Web App

The liveware web app is an optional interface, not the core tarot reader. This skill does not own liveware hosting, activation, app creation, tunnel binding, or ClawChat registration. It only defines the tarot-side behavior of the bundled code; implementation details live in `liveware/server.py`.

### Frontend i18n 设计

The liveware frontend supports Chinese and English via a three-layer system. Language is determined by priority: (1) URL query parameter `?lang=zh` or `?lang=en`, (2) `navigator.language` auto-detection (starts with `zh` → Chinese, everything else → English). Pure frontend — no server involvement. Translations are loaded from a centralized `i18n` object and applied through `data-i18n` attributes (static HTML) and `t('key')` calls (dynamic JS). Additionally, `?question=<text>` pre-fills the question input box on page load — orthogonal to the `lang` parameter, they can be combined independently.

For the full architecture (translation keys, function signatures, add-new-key workflow), see `skill_view(name='tarot-arcana', file_path='references/liveware-i18n.md')`.

### Frontend Question Guidance Copy Principles

The input area has three layers of question guidance. Each layer has a distinct role — do not overlap them:

| Layer | Role | Example (ZH) |
|-------|------|-------------|
| **Steps (ritual-steps)** | Tell the user WHAT to do at each stage — step 01 write question, step 02 choose spread, step 03 shuffle & pick | `写下一个有情境、有范围、有行动意义的问题。` |
| **Placeholder** | A real, relatable example question the user can model theirs after. Should feel like something a real person would actually ask. Use life scenarios (relationship, motivation, career). | `例如：和伴侣最近总为小事吵架，想看看接下来一个月问题到底出在哪。` |
| **Hint** | Explains the STRUCTURE of a good question (not another example). Complements the placeholder by teaching the user how to formulate their own. | `💡 好问题包含：具体情境 + 时间范围 + 你想看清什么。` |

**Principles when writing copy:**
- **No negative framing** — never say "避免" / "不要问" / "avoid". Tell the user what TO do, not what NOT to do.
- **Placeholder must be authentic** — use a scenario with emotional weight (relationship friction, life uncertainty), not abstract or generic. The placeholder example sets the tone for what kind of questions are welcome.
- **Hint teaches structure, not content** — don't put another example here. The hint's job is to help the user build their own question by understanding the three components.
- **Steps guide action** — step descriptions should be imperatives that tell the user what to do next. Step 02 should not repeat the tab descriptions; it should instruct the user to choose based on depth.
- **Tab descriptions explain when-to-use** — each spread tab's description should tell the user when they'd pick that option (quick check vs. deep dive), not just restate the position names.
- **Use consistent tarot terminology** — the third position is "未来" (future), not "下一步" (next step), matching standard tarot convention.

### 安装与激活脚本

为了方便安装和每日激活，提供了两个脚本：

> ⚠️ **分享注意事项**：这些脚本依赖 `liveware` CLI（需单独安装）和 `CLAWCHAT_TOKEN` 环境变量。如果你要分享这个技能，确保使用者已配置好这些依赖。

#### 首次安装 `liveware/scripts/setup.sh`

完整设置流程：登录 liveware → 创建 app → 注册到 ClawChat → 启动服务器 + 绑定隧道。

```bash
cd <skill-dir>
bash liveware/scripts/setup.sh
```

> 注意：注册到 ClawChat 的步骤需要在 Hermes 会话中用 `clawchat_register_app` 工具完成，脚本会打印对应的命令。

#### 每日激活 `liveware/scripts/start.sh`

当服务器和 app 已存在时，只需启动本地服务器并绑定隧道：

```bash
# 从技能目录运行（自动读取已保存的 app ID）
cd <skill-dir>
bash liveware/scripts/start.sh

# 或显式指定 app ID（可覆盖已保存的）
bash liveware/scripts/start.sh <app-id>
```

脚本会自动：
1. 从 `~/.clawling/tarot-app-id` 读取 app ID（或使用参数传入的）
2. 杀死占用端口的旧进程（如果有）
3. 用 `nohup` 启动 `liveware/server.py`（日志 → `/tmp/tarot-server.log`）
4. 等待服务器就绪
5. 绑定 liveware 隧道

> **注意**：因为 Hermes 的 `terminal()` 会在命令结束后杀掉子进程，所以脚本使用 `nohup` 保持服务器持续运行。如需手动停止：`kill $(ps aux | grep server.py | grep -v grep | awk '{print $2}')`
>
> 关于 liveware 激活的更多排查细节（token scope、隧道代理进程管理），参见 `clawchat` 技能中的 "Liveware App Activation" 章节。

### Activation Pitfall: Tunnel Must Be Explicitly Bound

When activating liveware, the app may already be registered and listed by `clawchat_list_apps()`, but **the tunnel binding is a separate step** — the app record exists on the server, but no local server is connected until you bind the tunnel.

✅ Correct activation sequence:
1. `clawchat_liveware_login()` — login
2. Start local server in background (e.g., `python3 server.py --port 5080`)
3. `liveware tunnel bind <appId> http://127.0.0.1:<port>` — bind tunnel
4. Verify public access: `curl https://<appId>.apps.clawling.io/`

❌ Mistake: assuming registration alone means the app is live.

### Pitfall: `$HOME` Mismatch When Running from Gateway Subprocess

`start.sh` reads the saved app ID from `$HOME/.clawling/tarot-app-id`. When triggered from a gateway hook subprocess (e.g., boot-md handler), the gateway's `$HOME` may differ from the interactive user's home directory. If the file doesn't exist at the expected path, `start.sh` exits with code 1 and **empty stderr** — the tunnel is never bound, and the public URL returns 502.

**Symptoms:**
- `clawchat_list_apps()` shows the app as registered and active
- `liveware backend list` shows an empty `TARGETURL` column
- `agent.log` shows `hooks.boot-md: start.sh exited 1:` with no error message
- Public URL returns 502

**Preferred fix:** Pass the app ID explicitly as an argument — this works regardless of `$HOME`:
```bash
bash liveware/scripts/start.sh <app-id>
```

**Fallback fix (if you can't control the argument):** Copy the app ID file to the gateway's `$HOME`:
```bash
mkdir -p "$(echo $HERMES_HOME)/.clawling"
cp ~/.clawling/tarot-app-id "$(echo $HERMES_HOME)/.clawling/tarot-app-id"
```

**Debugging tip:** The boot-md hook logs under `hooks.boot-md`, which is filtered out of `gateway.log` by the `_ComponentFilter` (only `gateway.*` and `hermes_plugins.*` pass through). Check `agent.log` instead for boot-md output.

For the full activation workflow, see `skill_view(name='liveware-app')`.

`liveware/server.py` is a Python HTTP server that:

- Serves the static frontend at `liveware/static/index.html`

### Pitfall — missing CORS headers on static files

Vite adds `crossorigin` to `<link rel="stylesheet">` in the built HTML. The browser sends a CORS request for the CSS file. If the server doesn't respond with `Access-Control-Allow-Origin`, **the stylesheet is silently not applied** — the page renders with default browser styling (beige/cream background, visible `sr-only` text, unstyled layout), even though the JS loads and runs correctly.

**Fix:** Override `end_headers()` in the handler class to add the CORS header to every response:

```python
def end_headers(self):
    self.send_header("Access-Control-Allow-Origin", "*")
    super().end_headers()
```

This must be done in the handler class itself (not just on API routes), because static files served by `super().do_GET()` → `send_head()` → `end_headers()` go through the same path.

**Verification:** Check the response headers with curl on the local port:
```bash
curl -sI http://127.0.0.1:5080/assets/index-*.css | grep -i access-control
# Expected: Access-Control-Allow-Origin: *
```

### Pitfall — CDN cache on tunnel URL with immutable cache headers

When the liveware tunnel/CDN (Cloudflare) serves static assets, it respects the `cache-control: public, max-age=2592000, immutable` header that Vite sets on hashed assets (30-day cache). If a previous deployment lacked CORS headers, the CDN caches the response **without** the CORS header and serves it for 30 days — even after the origin server is fixed.

**Symptoms:**
- Local curl to `127.0.0.1:<port>` shows `Access-Control-Allow-Origin: *`
- But curl to the tunnel URL (`https://<app-id>.apps.clawling.io/assets/...`) shows no CORS header
- `cf-cache-status: HIT` confirms the CDN is serving a cached copy

**Fix — force a new file hash:**

Change an actual CSS value (not just a comment — comments are stripped by LightningCSS minification) to produce different compiled output. Vite generates content hashes from the **compiled** output, so only changes that survive minification will produce a new hash:

```bash
# Before: no hash change
# Changing a comment → minifier strips it → same compiled output → same hash

# After: hash changes
# Changing --shadow: 0 24px 80px rgba(23, 5, 31, 0.30) to 0.31 → different compiled output
```

Rebuild, and the new CSS filename gets a different hash:
```bash
node node_modules/.bin/vite build
# Output shows new filenames: index-<newhash>.css, index-<newhash>.js
```

The new file is never cached (first request = MISS), so the CDN fetches it from the origin with CORS headers and caches the corrected version going forward.

**Long-term prevention:** To avoid needing hash changes, ensure the server has CORS headers before the first public deployment.

### Pitfall — TypeScript 6.0 strict build failures

The Vite template uses `tsc -b` (project build mode) before `vite build` in the `npm run build` script. TypeScript 6.0 is significantly stricter than earlier versions about:
- Empty array literals (`[]`) inferred as `never[]` instead of the expected typed array
- Unused variable declarations (`error TS6133`)
- Generic type mismatches on `Set<>` and `Map<>`

The `tsc -b` step will fail if any of these exist in the codebase, blocking the Vite build. To build without type-checking:

```bash
# Skip tsc, go straight to Vite:
node node_modules/.bin/vite build
```

The emitted JS is functionally identical regardless of type errors — the type checker only validates, it doesn't transform code. Use this workaround when iterating quickly. For production readiness, fix the type errors or update `tsconfig.json` to relax strict checks.

**Quick check after build:** Verify the new files exist and the HTML references them:
```bash
ls -la liveware/static/assets/
grep -o 'index-[^.]*\.\(css\|js\)' liveware/static/index.html
```
- Provides `POST /api/interpret` — submits card/question data to the Hermes API Server for interpretation
- Provides `GET /api/deck` — serves the skill's `data/deck.json` (78 cards with English names, keywords, summaryModern) for the frontend
- Sends submitted question/card data to the Hermes API Server with instructions to use the `tarot-arcana` skill for analysis
- Saves readings to `~/tarot-readings/` with an `index.json` history
- Returns the interpretation to the frontend without sending it to ClawChat automatically; the user sends it with the frontend button

### 🚫 Hard Rule: Never Clear the User's Input

> **The question input must NEVER be cleared by any interaction except the explicit "重新抽牌" button.**
>
> ⚠️ 这是整个项目中用户重复强调次数最多的一个 UX 规则。如果你收到中文反馈说"点击选牌后输入框被清空了"或"选牌后问题不见了"——优先排查这个规则是否被违反，而不是等待用户详细描述。具体排查步骤见下方 "Pitfall — choosePoolCard() accidentally clears input on card selection" 章节的 5 步 debug checklist。

This is the single most re-asserted UX requirement. Every code path that modifies reading state must be audited against this rule. Specifically:

| Action | Must preserve input? | Which function to call |
|--------|---------------------|----------------------|
| Card selection (`choosePoolCard`) | ✅ YES — never clear | Direct state update only |
| Spread tab switching (`setSpread`) | ✅ YES — never clear | `resetReadingState()` |
| New draw (oracle "重新抽牌 →") | ❌ Clears input | `resetReading()` |
| Reading generated (API success) | ✅ YES — never clear | State update only |
| Shuffle → choosing transition | ✅ YES — never clear | State update only |

**The one that bites:** A well-meaning refactor replaces `resetReadingState()` with `resetReading()` in `setSpread()` or `choosePoolCard()`, and suddenly the input clears on tab switch or card pick. There is no legitimate reason for card selection to call `resetReading()`.

### Pick Lock & Scroll Guidance

The frontend locks selection after all cards are picked to prevent re-selection. This is a deliberate UX guard:

- **After all cards are selected** in `choosePoolCard()`: `state.isPickingComplete = true`, the draw button and deck button are both disabled, and the deck hint text changes to `"选牌完成，向下查看解读 ↓"` (or English equivalent) with a pulsing accent-color animation via `.deck-hint.is-done`.
- **No automatic scroll on card selection** — `choosePoolCard()` no longer calls `scrollIntoView`. The user is already looking at the picker area; the spread grid appears just below it via `renderCards()` without any page scroll.
- **Minimal scroll to oracle panel** happens after the reading is generated (in `createReading()`'s success callback). Uses `block: 'nearest'` so it only scrolls if the reading text is not already visible, and with minimal offset rather than forcing it to the viewport top.
- **The `drawSpread()` function** checks `state.isPickingComplete` at the top and returns early if set, so the draw button and deck stack button are both inert.
- **`resetReadingState()`** — resets all reading state (cards, picker, buttons, reading text) but **preserves the question input**. Used internally by `setSpread()` so switching between one-card and three-card tabs does not clear the user's typed question.
- **`resetReading()`** — calls `resetReadingState()` then also clears the question input field. This is the full "start over" path. Called by the reset button (in the main actions bar) and the oracle panel reset button.
- **`setSpread()`** — calls `resetReadingState()` (not the full `resetReading()`), so switching spread tabs resets the cards but keeps the user's typed question.
- **`choosePoolCard()`** — when a user selects a card from the picker, must NOT clear the question input. The input survives card selection, reading generation, and the transition between shuffling → choosing → reading phases. The only way to clear the input is the explicit reset button (which calls `resetReading()`).

This prevents the user from accidentally triggering a re-shuffle after card selection, which would lose the current reading. The reset button is the intentional "start over" path.

#### Pitfall — `choosePoolCard()` accidentally clears input on card selection

If the user reports "the input box was cleared after I selected a card" (or "点击选牌后输入框被清空了"), debug in this order:

1. **Check `choosePoolCard()`** — does it call `resetReading()` (which clears input) anywhere? It should NOT. It should only update `drawn()`, `pickedIndexes`, and `phase()` — nothing that touches the question input.
2. **Check the JSX template** — does the question input element have a `value` binding that resets on state change? In SolidJS, `<input value={question()} />` will not reset on its own, but `<input value={someDerived()} />` might if the derived signal changes.
3. **Check `setSpread()`** — switching spread tabs calls `resetReadingState()` (preserves input). If someone changed it to call `resetReading()` (clears input), switching tabs would clear the box.
4. **Check the reset button handler** — does any button other than the explicit "start over" button call `resetReading()`?
5. **Check `createEffect` effects** — does any effect observe `drawn()` or `phase()` and inadvertently clear the question input as a side effect?

The root cause is almost always an unintended `resetReading()` call or a reactive binding that clears the input field when some other state changes. The fix is to ensure `resetReadingState()` (input-preserving) is used everywhere except the explicit reset button.

#### Reset during API request (AbortController)

**Pitfall: competing `scrollIntoView` calls cause jarring back-and-forth scrolling.** If two `scrollIntoView` calls fire in sequence (one scrolling to the card grid, one scrolling to the reading text), the page jumps down then immediately back up — the user perceives this as "jumping to the input box." Fix: remove the unnecessary scroll (the card grid is already visible below the picker), and for the remaining scroll use `{ block: 'nearest' }` so it only scrolls if the target is not already in view.

Both the reset button (`copyButton` in the oracle panel, or `resetButton` in the actions bar) and spread-tab switching (`setSpread()`) must remain clickable **even while `POST /api/interpret` is in flight**. Implementation:

1. In `createReading()`: do NOT disable `copyButton`; create an `AbortController` and pass its `signal` to `fetch()`.
2. In `resetReadingState()`: call `state.abortController.abort()` before any state cleanup.
3. In `resetReading()`: calls `resetReadingState()` (which handles abort) then clears the question input.
4. In the `.catch()` handler: check `err.name === 'AbortError'` and return silently — no error toast.

```js
// createReading()
if (state.abortController) state.abortController.abort();
const controller = new AbortController();
state.abortController = controller;

fetch('/api/interpret', { signal: controller.signal, ... })
  .catch(err => {
    if (err.name === 'AbortError') return;
    // normal error handling...
  });

// resetReadingState() — shared by resetReading() and setSpread()
if (state.abortController) {
  state.abortController.abort();
  state.abortController = null;
}
```

### Mobile Touch: Drag & Click Fixes

Mobile touch fixes cover two separate areas, both documented in `references/mobile-touch-fix.md`:

- **Drag fix** (horizontal card picker swipe): `touch-action: none` on all touch-path elements, touch event listeners as Pointer Events fallback, **replace `setPointerCapture` with document-level pointer listeners** (critical — `setPointerCapture` on the deck-picker parent blocks `click`/`dblclick` events on child card buttons on desktop Chrome).
- **Click fix** (card selection): native SolidJS `onClick` handler on each card button, with a `pointerMoved` flag to prevent drag-scroll from triggering accidental selection. No `addEventListener` via `ref` callback — that approach is unreliable in SolidJS `<For>` components when memo items are recreated on each evaluation (see the "Pitfall — `For` + `createMemo` identity" section for details).

### Card data architecture

Card data follows a dual-source architecture:

| Source | Location | Content | Language |
|--------|----------|---------|----------|
| `data/deck.json` | skill directory (copied to `public/` in Solid project, served as static `/deck.json`) | 78 cards with id, arcana, suit, number, name, upright/reversed keywords + summaryModern | English |
| `cardZh` | `src/data/cards.ts` in Solid project | Chinese UI data keyed by deck.json id: name, upright/shadow one-liner, symbol, hue, suit, rank | Chinese |

On page load, the frontend fetches `/deck.json` (from the server's static root), merges each card with its `cardZh` entry to produce the full UI card object. If the fetch fails, the draw button shows a loading message — the frontend doesn't have a fallback copy of the English data.

This means `data/deck.json` is the single source of truth for card identity (which 78 cards exist, their arcana/suit/number, and English interpretation data). The Solid source `cards.ts` only carries what deck.json cannot provide: Chinese names, Chinese upright/shadow one-liners, and display symbols/colors. Keeping them separate avoids maintaining two copies of the same card roster.

### Porting Pitfall: Backup Extract Loses Post-Backup Modifications

When porting from a vanilla HTML/JS app to SolidJS (or any framework), **never use a backup file taken before the user's modifications as the CSS/JS source.** The backup represents a snapshot in time — any edits made to the deployed version after the backup was taken will be missing.

**The specific pattern that bit us:** The original `index.html` went through several rounds of edits:
1. Initial light-theme version → backup taken (`/tmp/tarot_css.css`)
2. Dark theme applied (body `background: var(--bg)`, `:root` colors changed)
3. Copy changes (step1 negative phrasing removed, placeholder/hint rewritten)
4. CSS layout fixes (heading one-line, max-width adjusted)

When the SolidJS project was created, the CSS was extracted from step 1's backup (light theme, old copy) instead of the deployed live version. Result: all of steps 2–4's changes were silently lost.

**Prevention checklist when porting:**
- ✅ **Compare every changed string** between old and new after porting — grep for key phrases that were modified (e.g. `"会不会"`, `"avoid"`, `oklch(86%`)
- ✅ **Extract CSS from the deployed/live version**, not from a local backup file. If the deployed version is minified, use the browser dev tools or the unminified source if available.
- ✅ **Audit i18n keys one by one** — copy-heavy apps are the most likely to lose changes during porting
- ✅ **Verify visual theme tokens** — check `:root` color variables, body background, and surface colors match the deployed version
- ✅ **Run a visual diff** — compare the built app side-by-side with the original deployed version on at least one mobile and one desktop viewport

The fix when this happens: re-read the conversation history or session search for each specific change the user reported, then apply them one by one to the new source files. The `patch` tool with exact old→new string matching is the most reliable way to do this.

### Shuffle Logic, rAF + Timeout Fallback & Animation

The shuffle-to-choosing transition uses a `requestAnimationFrame` loop with a 760ms threshold check, plus a 1-second `setTimeout` fallback to guarantee the transition completes even if rAF stalls. During shuffling, two visual layers play simultaneously:

1. **Deck-stack fan-out** — 4 card backs spread outward via `.deck-stack.is-shuffling` CSS transforms (nth-child 1–4 rotate and translate).
2. **Shuffle orbit** — A `.deck-picker.is-shuffling-placeholder` with 6 card backs in a horizontal arc, each with staggered `shuffle-float` animation (1.15s infinite, bouncing up at 50%). The 6 cards are positioned via CSS custom properties (`--spin-x`, `--spin-y`, `--spin-rotate`, `--spin-delay`) from -128px to +140px on X axis.

The shuffle-orbit is rendered as a `<Show when={phase() === 'shuffling'}>` inside the deck-zone. Both the deck-stack fan-out and the shuffle-orbit are visible simultaneously during shuffling.

After the rAF loop completes (760ms elapsed), `phase('choosing')` triggers `is-selecting` on deck-zone: the deck-stack fades out (`opacity: 0`), the shuffle-orbit is replaced by the deck-picker with 78 card-back thumbnails in an arc layout.

**Timeout value:** 760ms — matches the original vanilla-HTML reference version. The rAF loop checks `Date.now() - start >= 760` each frame. A 1-second `setTimeout` fallback cancels the rAF and calls `tick()` directly as a safety net.

**Implementation pattern:**
```ts
const start = Date.now()
let rafId: number | null = null
function tick() {
  if (Date.now() - start >= 760) {
    // shuffle logic: Fisher-Yates, setDeckPool, setPhase('choosing')
  } else {
    rafId = requestAnimationFrame(tick)
  }
}
rafId = requestAnimationFrame(tick)
setTimeout(() => {
  if (rafId != null && Date.now() - start >= 760) {
    cancelAnimationFrame(rafId)
    tick()  // fallback: call directly
  }
}, 1000)
```

**Why rAF + setTimeout fallback:** `requestAnimationFrame` pauses when the tab is backgrounded or the device is under load. The 1-second `setTimeout` guarantees the transition always fires within ~1s regardless of tab visibility or CPU throttling. `cancelAnimationFrame(rafId)` in the fallback prevents double-execution.

**Pitfall — stale rAF state after manual fallback:** When the `setTimeout` fallback fires and calls `tick()`, `rafId` still holds a non-null value from the last rAF callback, so a subsequent fallback check at 1000ms will fire `tick()` again. This is harmless because `tick()` re-enters with `Date.now() - start >= 760` already true and re-shuffles the same pool — no crash, just a redundant shuffle. To prevent even that, reset `rafId = null` after the fallback fires.

**Debugging tip — browser console logs with prefix:** When the app appears "stuck" after the shuffle animation, the first step is to check the browser console for errors. Add a `console.log('[tarot]', ...)` prefix to all debug logs so they're easy to filter. Common checks:

1. Open DevTools Console → filter `[tarot]` or look for red `TypeError` entries
2. Check if `setPhase('choosing')` fires (logged after the timeout) — if it does, the error is after that
3. Check for `t(...)` calls in `setReadingHtml()` — this is where function-valued i18n keys cause `TypeError: Q(...) is not a function`
4. Verify the timeout value matches the reference HTML (760ms) — too long (>1200ms) causes perceived stuckness even without errors

**Error handling:** The rAF tick function is wrapped in a try-catch. On any error (shuffle failure, state corruption), the phase resets to `'idle'` and shuffling is set to `false`, so the app never gets permanently stuck:

```ts
function tick() {
  const elapsed = Date.now() - start
  if (elapsed >= 760) {
    try {
      const pool = shuffle(tarotCards()).map(c => ({ ... }))
      setDeckPool(pool)
      setPickedIndexes(new Set())
      setDrawn([])
      setRevealed(new Set())
      setPhase('choosing')
      setShuffling(false)
      setReadingHtml(...)
    } catch (err) {
      console.error('[tarot] Shuffle error:', err)
      setPhase('idle')
      setShuffling(false)
      showToast('Shuffle error, please try again')
    }
  } else {
    rafId = requestAnimationFrame(tick)
  }
}
rafId = requestAnimationFrame(tick)
setTimeout(() => {
  if (rafId != null && Date.now() - start >= 760) {
    cancelAnimationFrame(rafId)
    tick()
  }
}, 1000)
```

### Pitfall — stale timeout value: If the timeout is too long (≥1200ms), users perceive the app as "stuck" because the card backs spread out but nothing happens. Always cross-reference the timeout against the old HTML version's `drawTimer` value (760ms in the original). If you change the timeout, also update the CSS animation durations that should complete before the transition fires.

### Pitfall — `t('key')(arg)` vs `t('key', arg)` call pattern

The `t()` i18n function signature accepts `...args` and handles function-valued translations internally:

```ts
// i18n.ts — t() calls the function internally and returns a string
export function t<K extends I18nKey>(key: K, ...args: ...): string {
  const val = i18n[LANG][key];
  if (typeof val === 'function') return val(...args);  // calls with ...args
  return String(val);
}
```

This means `t('reading_pick_body', spread())` returns a **string** directly. Writing `t('reading_pick_body')(spread())` calls `t(...)` first (returns a string), then tries to call the string as a function → **`TypeError: Q(...) is not a function`**.

**Symptoms of the wrong pattern:** The shuffle timeout fires, all state updates succeed (`setPhase('choosing')`, `setDeckPool(pool)`, etc.), but `setReadingHtml(...)` throws inside the try block. The catch block resets `phase('idle')` and `shuffling(false)`, so the user sees the shuffle animation but immediately returns to the idle state — appearing as "stuck." The error is visible in the browser console but silent to the user.

**Affected call sites (all must use `t('key', arg)` not `t('key')(arg)`):**
- `setReadingHtml` calls with parameterized i18n keys
- `aria-label` attributes on picker cards and spread cards
- `ritual_pick`, `ritual_revealed`, `ritual_all_revealed` in the sr-only live region

**How to audit:** Search for `t('.*')\(` in the source — this pattern matches `t('foo')(bar)` but not `t('foo', bar)`:

```bash
grep -n "t('" src/App.tsx | grep -E '\)\(|\),'
```

**How it went undetected:** The TypeScript `t()` return type is `string` (because it always returns a string), so `t('key')(arg)` doesn't produce a type error — `string(...)` is valid TypeScript syntax (calling a string as a function is a runtime error, not a compile-time error). The i18n values are typed as `string | function` via `I18nKey` lookup, but the `t()` return type narrows to `string`.

**Prevention:** When changing the `t()` function signature to accept `...args` (so it handles function-valued translations internally), audit ALL call sites that previously used `t('key')(arg)` and update them to `t('key', arg)`. The safest approach: after the signature change, search the entire codebase for `t('.*')\(` and fix every match.

**Visual flow during shuffle:**
1. User clicks deck-stack or draw button → `handleDraw()` called
2. `setShuffling(true)` → `is-shuffling` CSS class on deck-stack (4 card backs fan out)
3. `setPhase('shuffling')` → `is-busy` CSS class on deck-zone
4. rAF loop runs for ~760ms (shuffle animation plays):
   - Deck shuffled (Fisher-Yates) when `Date.now() - start >= 760`
   - `deckPool` populated with shuffled cards + random reversal (25% chance)
   - `phase` set to `'choosing'` → `is-selecting` CSS class on deck-zone, deck-stack fades out
   - `shuffling` set to `false` → `is-shuffling` class removed
5. `Show` component renders deck-picker with 78 card-back thumbnails in an arc layout

### Pitfall — `For` + `createMemo` identity: unnecessary DOM recreation

When `pickerCards()` is a `createMemo` that returns `.map()` output (new object literals), **every evaluation creates a completely new set of objects**. SolidJS's `For` component uses `===` identity comparison by default — since every item is a new reference on every memo evaluation, the `For` destroys ALL existing DOM nodes and creates new ones.

**Symptoms:**
- The picker arc scroll position resets to 0 after each card selection
- Event listeners attached via `ref` callback + `addEventListener` are silently lost after the first selection (cards become unclickable)
- The `ref` callback fires during reconciliation, but listeners from the previous lifecycle are gone
- If the memo re-evaluates during animation (e.g., after `pickedIndexes` changes), the arc visibly stutters

**Recommended fix — use native `onClick` instead of `ref` + `addEventListener`:**

The most reliable approach is to **avoid `ref` callback + `addEventListener` entirely** in SolidJS `<For>` components when items are memo-driven. Use SolidJS's native `onClick` handler:

```tsx
<For each={pickerCards()}>
  {(item) => (
    <button
      onClick={() => handlePickerClick(item.index)}
      disabled={item.chosen}
    >
```

This is lifecycle-safe: SolidJS manages event delegation through its own system, not through manual DOM listener attachment. The handler always fires regardless of how many times the `<For>` recycles its DOM nodes.

**Double-click pattern (deck picker selection):** The deck picker requires double-click/tap to select a card, implemented with a `Date.now()` threshold check:

```ts
let lastPickerClick = 0
let lastPickerIndex = -1
function handlePickerDoubleClick(poolIndex: number) {
  if (pointerMoved) return  // was a drag, not a click
  const now = Date.now()
  if (poolIndex === lastPickerIndex && now - lastPickerClick < 400) {
    // Double-click detected — select the card
    lastPickerClick = 0
    lastPickerIndex = -1
    choosePoolCard(poolIndex)
  } else {
    // First click — record it and wait
    lastPickerClick = now
    lastPickerIndex = poolIndex
  }
}
```

Then use it in the template:
```tsx
<button
  onClick={() => handlePickerDoubleClick(item.index)}
  disabled={item.chosen}
>
```

Key details:
- The 400ms threshold works for both desktop (click) and mobile (touch)
- `pointerMoved` check prevents drag-scroll from being misidentified as a click
- Same-card-index check (`poolIndex === lastPickerIndex`) prevents cross-card double-tap
- `lastPickerClick = 0` after a successful double-tap prevents triple-click from triggering a second selection

**Drag-scroll guard:** When the picker supports horizontal drag-scroll, native `onClick` can fire after a drag ends (if the pointer moved but the browser still emits a click). Guard against this with a `pointerMoved` flag:

```ts
let pointerMoved = false

function onPickerPointerDown(e: PointerEvent) {
  pointerMoved = false
  // ... track scroll start
  document.addEventListener('pointermove', () => {
    if (/* moved > 5px */) pointerMoved = true
  })
  document.addEventListener('pointerup', cleanup)
}

function handlePickerClick(poolIndex: number) {
  if (pointerMoved) return  // was a drag, not a click
  choosePoolCard(poolIndex)
}
```

The browser's built-in click-gesture detection (no click event if pointer moved significantly between down/up) covers most cases; the `pointerMoved` flag is an additional safety layer.

**Why `ref` + `addEventListener` fails:**

1. `pickerCards()` memo returns `.map()` output → all items are new object references
2. SolidJS `<For>` uses referential identity → sees all-new items → destroys old DOM → creates new DOM
3. The `ref` callback fires on the new DOM, calling `addEventListener`
4. But there's a timing window between DOM creation and event system attachment where clicks can be swallowed
5. On subsequent memo evaluations (after each card pick), the cycle repeats — listeners from the previous cycle are discarded with the old DOM nodes

This is fundamentally a SolidJS lifecycle issue: `ref` callbacks are for DOM access, not event binding. Event binding belongs in JSX props (`onClick`, `onKeyDown`, etc.) so SolidJS can manage them through its event delegation system.

### Same class of bug: spread grid `positions` memo not tracking `drawn()`

The same `For` + `createMemo` identity pattern affects the **spread grid** — the 1–3 card slots below the picker. The spread grid renders like this:

```tsx
<For each={positions()}>
  {(pos, index) => {
    const draw = drawn()[index()]
    ...
  }}
</For>
```

Where `positions` is:
```ts
const positions = createMemo(() => spreads[spread()])
```

**The bug:** `positions` only depends on `spread()`. When the user selects a card (updating `drawn()`), the `positions()` memo does NOT recompute. The `For` component sees the same array reference (same items), so it does not re-render its children — even though `drawn()` is read inside the callback.

**Why this is the same class of bug as pickerCards:** In both cases, a `createMemo` that returns a stable array (from a static data structure) does not track a secondary signal that the template reads reactively. The `For` component's internal reconciliation is driven by the `each` array's reference identity; it does not re-execute the mapping function for items it considers "already existing."

**Fix — `spreadSlots` memo with combined dependencies:**

Create a new memo that explicitly depends on both `positions()` and `drawn()` (plus `revealed()` for completeness):

```ts
const spreadSlots = createMemo(() => {
  const pos = positions()
  const draws = drawn()
  return pos.map((p, i) => ({
    pos: p,
    draw: draws[i] || null,
    isRevealed: draws[i] ? revealed().has(i) : false,
  }))
})
```

Then iterate over `spreadSlots()` in the `For`:

```tsx
<For each={spreadSlots()}>
  {(slot) => {
    const { pos, draw, isRevealed } = slot
    ...
  }}
</For>
```

Now when `drawn()` or `revealed()` changes, `spreadSlots` creates new item objects → `For` detects new references → re-renders the affected card slots.

**Why this works:** `spreadSlots` returns a new array with new object references on every evaluation. SolidJS's `For` uses `===` identity — new references = new items = re-render. The `pos.map()` call creates fresh objects each time, which is the correct behavior here because the array is small (1–3 items) and the re-render cost is negligible.

**Alternative (doesn't work):** Adding `drawn()` as a dependency to `positions` but still returning `spreads[spread()]` (same array reference) — `For` won't detect the change because the array reference hasn't changed. You MUST create a new array (via `.slice()`, `.map()`, or spread) for `For` to re-render.

**Alternative fix — use `by` prop for stable keying:**

If you must keep `ref` + `addEventListener` (e.g., for touch gesture detection), use SolidJS's `by` prop to preserve DOM identity:

```tsx
<For each={pickerCards()} by={(a, b) => a.index === b.index}>
```

This tells `<For>` to reuse DOM nodes when only the item data changed. The `ref` callback re-runs for new items only; existing items keep their listeners and DOM state (scroll position, focus, etc.).

`by` is available in SolidJS 1.5+. The project uses `solid-js` via the Vite template — verify the version if upgrading from an older template.

**Alternative fix — stable identity on memo items:**

Instead of using `by`, make the memo return items with stable object references. This is more complex (requires externalized state or an immutable data structure), so the `by` prop approach is preferred.

### SolidJS Build Pipeline

Since v0.21.0, the liveware frontend is a **SolidJS + Vite + TypeScript** project rather than a single inline HTML file. The source code lives at a separate location:

```
/opt/data/tarot-arcana-app/
├── src/
│   ├── index.tsx              ← SolidJS mount point
│   ├── App.tsx                ← Main component (state, JSX, all logic)
│   ├── index.css              ← All styles (dark theme, card layout, etc.)
│   └── data/
│       ├── cards.ts           ← 78-card Chinese data (cardZh)
│       └── i18n.ts            ← Chinese/English translation + spreads
├── public/
│   ├── favicon.svg / icons.svg
│   └── deck.json              ← Auto-copied to build output
├── vite.config.ts             ← outDir: skill's liveware/static/
└── index.html
```

**Build command:**
```bash
cd /opt/data/tarot-arcana-app && node node_modules/.bin/vite build
```

**Build output** goes to `liveware/static/`:
| File | Size | Notes |
|------|------|-------|
| `index.html` | 0.4 KB | SolidJS mount point |
| `assets/index-*.js` | ~96 KB | SolidJS + marked library + all logic |
| `assets/index-*.css` | ~22 KB | Minified CSS |
| `deck.json` | 79 KB | Card data (from `public/`) |

**Pitfall: `emptyOutDir: true`** — If set, the entire `static/` directory is cleared on each build. Card PNGs in `static/cards/` (generated by the Python script) would be deleted. **Fix:** Set `emptyOutDir: false` in `vite.config.ts` — PNG files survive rebuilds. The `public/` folder continues to work normally and its contents are merged into the build output.

**Pitfall: `tsc -b` failures with TypeScript 6.0** — The `npm run build` script runs `tsc -b && vite build`. TypeScript 6.0 is stricter about empty arrays, unused variables, and generic types. If type errors block the build, run Vite directly: `node node_modules/.bin/vite build`. The emitted JS is identical.

**Pitfall: CDN caches the old CSS hash for 30 days** — Vite sets `cache-control: immutable` on hashed assets. If the CDN cached a version without CORS headers (or with stale content), the only way to force a new cache entry is to change a real CSS value (not just a comment — comments are stripped by the minifier) so Vite generates a different content hash. See the "Pitfall — CDN cache on tunnel URL" section above for the full procedure.

**Why SolidJS?** Replaced vanilla JS (60 KB of inline DOM manipulation with `innerHTML`) with SolidJS reactive JSX. Benefits: declarative rendering (no manual `innerHTML`), fine-grained reactivity (no full re-renders), proper component lifecycle (`createEffect`, `onCleanup`), TypeScript type safety. The final JS bundle is ~96 KB including SolidJS runtime + marked library — slightly larger than the vanilla file but with a cleaner architecture and proper markdown rendering.

### CSS Source — Owner's Reference HTML

The liveware frontend CSS must match the owner's reference `index.html` file exactly. This is the authoritative visual design source — do not redesign or restyle independently. Key CSS properties that must match:

- **Layout**: 2-column hero grid (`minmax(720px, 1fr) minmax(460px, 560px)`), intro + control-panel in column 1, oracle-panel sticky in column 2 spanning both rows
- **Colors**: oklch token set with `--paper`/`--paper-deep` surface colors, `--accent` (purple) and `--cup-gold` (gold) accents
- **Body**: dark radial gradient background with grid pattern overlay (`body::before`) and SVG noise overlay (`body::after`, mix-blend-mode overlay)
- **Cards**: `border-radius: 4px` (card backs) / `6px` (face) / `16px` (picker cards), `object-fit: contain` for card images
- **Buttons**: primary button uses gold gradient (`linear-gradient(135deg, var(--cup-gold), oklch(66% 0.13 72))`)
- **Deck zone**: `overflow: visible` (not `hidden`), with concentric circle and diamond `::before`/`::after` pseudo-elements
- **Responsive**: breakpoints at 1180px (hero goes to single column `grid-template-columns: 1fr`, oracle-panel drops to full width with `position: static`), 820px (mobile single-column with narrower width), 480px (compact padding/border-radius). The 1180px breakpoint is critical — at any width below 1180px the layout must be single-column (not a reduced 2-column layout), or the right column (oracle-panel) overflows.

**Container is `.hero`, not `.app`:** The outermost layout wrapper is `<section class="hero">`, NOT `<div class="app">`. There is no `.app` element in the HTML template (it uses `<>` Fragment → `<section class="hero">`). Any CSS targeting `.app` is dead code — it will never apply. Always use `.hero` for outer container width/margin rules.

**Mobile padding values (user preference, verified via screenshot):** The `.hero` container must not be flush against screen edges on small viewports. Specific values:
- **820px breakpoint:** `.hero { width: min(100% - 48px, 680px); }` — 24px horizontal breathing room on each side
- **480px breakpoint:** `.hero { width: min(100% - 40px, 460px); }` — 20px on each side
- **Card internal padding at 480px:** `.intro, .control-panel, .oracle-panel { padding: 22px; }` — increased from 18px after user reported content still too close to edges

Total effective padding from screen edge to card content at 480px: ~42px (20px from `.hero` + 22px from card). The user confirmed this as comfortable via screenshot.

**Pitfall — CSS targeting `.app` when the root is `.hero`:** Before adding or changing layout CSS, always verify the actual HTML structure. The template uses `<> <section class="hero"> ... </section> </>`, so `.hero` is the real outer container. If you write `.app { width: ... }` rules, they silently do nothing and the user will report "没有padding" (no padding). Check the TSX/JSX root element first.

**Pitfall — trusting a backup over the deployed version:** When porting CSS from the old HTML to a new framework (e.g., vanilla JS → SolidJS), extract CSS from the deployed/live version of the reference HTML, not from a stale local backup. The user may have edited the deployed HTML directly (changed colors, copy, layout) after the backup was taken. Use `curl` to fetch the live HTML if available, or re-read the conversation for edits the user applied.

**Pitfall — responsive breakpoint mismatch:** The 1180px breakpoint must set `.hero { grid-template-columns: 1fr; }` (single column), not a reduced 2-column like `1fr 1.35fr`. If the hero stays 2-column below 1180px, the control-panel (left) and oracle-panel (right) become too narrow and the layout breaks. The exact responsive CSS at 1180px from the reference HTML:
```css
@media (max-width: 1180px) {
  .hero { grid-template-columns: 1fr; }
  .intro { grid-column: auto; grid-template-columns: 1fr; gap: 18px; min-height: auto; }
  .ritual-steps { grid-template-columns: repeat(3, minmax(0, 1fr)); }
  .control-panel { grid-column: auto; min-height: auto; }
  .oracle-panel { grid-column: auto; grid-row: auto; position: static; min-height: 380px; max-height: none; }
}
```
Note: Vite's LightningCSS transforms `@media (max-width: 1180px)` to the modern range syntax `@media (width<=1180px)` in the output — both are equivalent and supported in modern browsers.

**Pitfall — CSS extraction misses user edits:** After porting, compare every changed string between old and new. Grep for key phrases that were modified (e.g. `"会不会"`, `"avoid"`, `oklch(86%`). Audit i18n keys one by one. Verify visual theme tokens (`:root` color variables, body background, surface colors) against the deployed version. Run a visual diff on at least one mobile and one desktop viewport.

### Card Image Source

Card face images and the card back come from the user's source set (78 JPG files at 300×527, provided via zip). The images are served directly from `liveware/static/cards/` as static files — no JS rebuild needed when only the images change.

The original download script at `scripts/download-rws-images.py` was used for the initial fetch from the public tarotcardapi, and the card back generator at `scripts/generate-card-back.py` was a fallback. These scripts remain in the repo but are superseded when the user provides their own image set.

#### Replacing Card Images from a User Zip

When the user provides a zip containing card images:

1. Download the zip and extract:
   ```bash
   curl -L -o /tmp/cards.zip "<url>" && python3 -c "import zipfile; zipfile.ZipFile('/tmp/cards.zip').extractall('/tmp/cards-out')"
   ```

2. **Rename files to match deck.json naming** — the deck.json uses `Fortitude` (not `Strength`) and `The Last Judgment` (not `Judgement`). The user's zip may use the alternate RWS names:
   ```bash
   mv /tmp/cards-out/<dir>/08-Strength.jpg /tmp/cards-out/<dir>/08-Fortitude.jpg
   mv /tmp/cards-out/<dir>/20-Judgement.jpg /tmp/cards-out/<dir>/20-TheLastJudgment.jpg
   ```

3. Copy all JPG files to the cards directory, overwriting existing:
   ```bash
   cp /tmp/cards-out/<dir>/*.jpg /opt/data/skills/creative/tarot-arcana/liveware/static/cards/
   ```

4. Clean up old PNG files (leftover from previous generation scripts):
   ```bash
   rm -f /opt/data/skills/creative/tarot-arcana/liveware/static/cards/*.png
   ```

5. Verify:
   ```bash
   ls /opt/data/skills/creative/tarot-arcana/liveware/static/cards/*.jpg | wc -l  # should be 79 (78 faces + 1 back)
   python3 -c "from PIL import Image; img = Image.open('.../CardBacks.jpg'); print(img.size)"  # should be 300×527
   ```

**No build step needed** — the images are served as static files. The server picks them up immediately. Users may need to hard-refresh (Cmd/Ctrl+Shift+R) to see new images if the CDN has cached old ones.

#### Image Dimensions

- Card faces and back: 300×527 pixels (CSS uses `aspect-ratio: 300 / 527` which matches exactly)
- Format: JPEG, RGB mode
- Previous generation: 240×336 (from the tarotcardapi download). The CSS was already set to 300/527 before the upgrade, so no layout changes were needed.

**Name mapping detail:** The API uses lowercase hyphenated names (e.g. `thefool.jpeg`, `aceofwands.jpeg`) except `TheLovers.jpg` which has a capital `L`. The download script handles this edge case in the `NAME_TO_API` dict.

### File Naming Convention

Card images follow the naming convention from the original vanilla-HTML version of the app (the authoritative reference the owner provides). This convention is what the frontend `cardImage()` function uses to construct image URLs:

- **Major arcana:** `{pad2(number)}-{nameNoSpaces}.jpg` — e.g. `00-TheFool.jpg`, `01-TheMagician.jpg`, `21-TheWorld.jpg`
- **Minor arcana:** `{Suit}{pad2(number)}.jpg` — e.g. `Wands01.jpg` (Ace), `Cups02.jpg` (Two), `Swords11.jpg` (Page=11), `Pentacles12.jpg` (Knight=12), `Pentacles13.jpg` (Queen=13), `Pentacles14.jpg` (King=14)
- **Card back:** `CardBacks.jpg`

After downloading the real RWS images as PNGs, run the rename script to create JPG copies with the old-HTML naming convention:

```bash
cd /opt/data/tarot-arcana-app
uv run python3 scripts/rename-cards.py
```

The rename script converts PNGs to JPEG (quality=92) and also converts `CardBacks.png` → `CardBacks.jpg`.

The frontend constructs image paths using the old-HTML convention:
```ts
// App.tsx — matches the old HTML naming convention exactly
const SUIT_CAP: Record<string, string> = { wands: 'Wands', cups: 'Cups', swords: 'Swords', pentacles: 'Pentacles' }
function cardImage(card: { arcana: string; number: number; name?: string; suit: string | null }): string {
  const isMajor = card.arcana === 'major'
  if (isMajor) {
    const name = (card.name || '').replace(/\s+/g, '')
    return `/cards/${String(card.number).padStart(2, '0')}-${name}.jpg`
  }
  const suit = SUIT_CAP[card.suit || ''] || 'Wands'
  return `/cards/${suit}${String(card.number).padStart(2, '0')}.jpg`
}
function cardBackImage(): string { return '/cards/CardBacks.jpg?v=2' }
```

**Cache-busting static images:** When the card back (or any static image in `static/cards/`) is updated but the filename doesn't change, browsers serve the cached version even after hard-refresh. Append `?v=N` (increment N each update) to the image URL in `cardBackImage()` (and both `cardImage()` and `cardZh.imgBack` in `cards.ts` if face images change) to force re-fetch. The JS bundle rebuild (new hash) ensures the new `?v=N` value reaches the browser.

**Why JPG not PNG for delivery:** The original HTML references `.jpg` files. The downloaded images are converted to JPG to match. The card back is also served as JPG even though it was generated as PNG. This matters for the Python HTTP server's Content-Type header — `.jpg` → `image/jpeg` is correct for JPEG data.

**Pitfall — CDN cache:** After updating card images, the tunnel CDN may still serve old versions. Use cache-busting query params (`?v=N`) to verify. The user may need to hard-refresh (Cmd/Ctrl+Shift+R) to see new images in the browser.

### Full Setup Sequence

```bash
cd /opt/data/tarot-arcana-app
# 1. Download real RWS images (PNG, named by deck.json id)
uv run python3 scripts/download-rws-images.py
# 2. Generate card back (PNG) — OR replace with user-provided images (see "Replacing Card Images from a User Zip")
uv run python3 scripts/generate-card-back.py
# 3. Create JPG copies with old-HTML naming convention
uv run python3 scripts/rename-cards.py
# 4. Build SolidJS app
npx vite build
# 5. Clean up stale JS/CSS assets
rm -f ../skills/creative/tarot-arcana/liveware/static/assets/index-*.js
# Re-run build (assets are regenerated)
npx vite build
# 6. Restart server
# Kill old python3 server, start new one
```

**Why PNG not SVG data URI:** The user explicitly requested real image files over inline SVG. PNG images also work better with `<img>` tag loading, browser caching, and the 3D flip animation (no data URI size inflation in JS).

**Rendering layers:**
- **Deck picker** (horizontal scrollable card selection): each card button shows the PNG card back as a thumbnail
- **Spread cards** (the 3D flip cards): the back face shows the PNG card back, the front face shows the PNG card face
- **Reversed cards**: the front image gets `transform: rotate(180deg)` via `.is-reversed` class; the `.face.front` wrapper also rotates via `transform: rotateY(180deg) rotate(180deg)` to keep the 3D flip animation correct
- **Selected/disabled picker cards**: get `opacity: .34; filter: saturate(.65)`

#### Empty slot behavior (spread positions)

The spread position slots (过去/现在/未来) **keep text placeholders** — they show a waiting message before shuffling and during card selection. This is deliberate: the spread positions are not filled until the user completes their selection, and text placeholders make the flow clearer than showing a card back that might be mistaken for an already-drawn card.

- **`renderEmptySlots()`** (before shuffle): shows `empty_title_wait` / `empty_body_wait` i18n text
- **`renderCards()`** (during selection, unfilled positions): shows `empty_title_select` / `empty_select` or `empty_title_wait` / `empty_body_wait` text depending on state

#### Default deck stack (pre-shuffle)

Before shuffling, the deck stack (`.deck-stack` button in `.deck-zone`) shows four card-back PNG thumbnails stacked slightly, fanned via `nth-child` transforms. After shuffling, `.deck-zone.is-selecting .deck-stack` becomes `opacity: 0; pointer-events: none` and the deck picker (`.deck-picker`) takes over with individual card back thumbnails.

The card back PNG has a dark purple background with a traditional RWS-style pattern: concentric circles, an 8-pointed compass star, corner diamond ornaments, and a subtle dot grid in the outer areas. Loaded as a regular `<img>` with `loading=\\\"lazy\\\"` for deferred loading.

### Interpretation Text Rendering (wrapMdAsHtml via `marked`)

The interpretation text returned from `POST /api/interpret` comes as markdown. The frontend uses the **`marked`** library (installed via npm) to render it to HTML before injecting into the oracle panel. The custom hand-rolled `wrapMdAsHtml` parser was replaced after the user questioned it — `marked` handles all edge cases (nested lists, indented items, code blocks, inline formatting) correctly.

```ts
import { marked } from 'marked'

// Custom renderer shifts heading levels by +2 (### → h5)
const _mdRenderer = new marked.Renderer()
_mdRenderer.heading = ({ text, depth }: { text: string; depth: number }) => {
  const h = Math.min(depth + 2, 6)
  return `<h${h}>${text}</h${h}>`
}
marked.setOptions({ renderer: _mdRenderer })

function wrapMdAsHtml(md: string, _question: string): string {
  return marked.parse(md, { async: false }) as string
}
```

**Key details:**
- The `marked` library handles: headings, ordered/unordered lists (including nested/indented), code blocks (fenced), inline formatting (`**bold**`, `*italic*`, `` `code` ``), and HTML entity escaping natively
- The only customization is heading level shifting (+2) to match the original design where `###` produces `<h5>`
- The oracle panel uses `innerHTML` to inject the result — safe because the markdown comes from the trusted server endpoint
- Bundle size impact: JS increased from ~56 KB to ~96 KB (gzip: 21→34 KB) due to the `marked` library inclusion

**If the user reports "the interpretation shows raw `**text**` instead of bold text":**
1. Verify `marked.parse()` is being called before `innerHTML` assignment
2. Check that the oracle panel uses `innerHTML` (not `textContent`)

**Pitfall — ordered list renders as all "1." with indented levels (numbered list numbering lost) — RESOLVED**

This was a bug in the custom `wrapMdAsHtml` parser. **Switching to the `marked` library resolved both causes permanently.** `marked` handles indented list items, nested lists, proper `<ol>`/`</ol>` closing tags, and auto-numbering natively. No custom regex or closing-tag logic to maintain.

### Intro Heading Layout

The page title `<h1>` has two `<span class="title-line">` elements ("Tarot" / "Arcana"). These default to `display: block` (stacked). To show them on one line:

```css
.intro h1 .title-line { display: inline; margin-inline-end: .15em; }
```

**Pitfall: `max-width` truncation.** The `<h1>` has `max-width: 6.6ch` — enough for one word when stacked, but "Tarot Arcana" (~12 chars) overflows when on one line. The second word gets clipped visually. Fix: increase to `13ch` (or more). The symptom is "Arcana 没有完整显示" — the second word appears cut off.

**Pitfall: mobile font-size overflow (CSS clamp too large).** On mobile breakpoints (≤820px, ≤480px), the `h1` font-size is set with `clamp(54px, 18vw, 82px)` / `clamp(46px, 18vw, 64px)`. "Tarot Arcana" is ~12 characters wide. At 18vw on a 375px phone (~67px), the title is ~480px wide — far wider than the viewport.

**Diagnostic priority (this was wrong twice — learn from it):** When the user reports "标题太宽了" or "超出了 card 的宽度" or "最顶部的大字TarotArcana在手机上太宽了":
1. ✅ FIRST check the `h1` font-size `clamp()` values on mobile breakpoints — `18vw` is almost certainly the culprit
2. ❌ Do NOT add `overflow-x: hidden` to `.app` — that suppresses the symptom (clips the overflow) instead of fixing the cause (oversized text)
3. ❌ Do NOT change `position: relative` on `.deck-zone` — the deck-zone positioning has nothing to do with the title width; changing it can break the deck picker layout
4. ✅ The correct fix is to reduce the font-size clamp on mobile breakpoints:

```css
@media (max-width: 820px) {
  .intro h1 { font-size: clamp(36px, 12vw, 54px); }
}
@media (max-width: 480px) {
  .intro h1 { font-size: clamp(32px, 12vw, 46px); }
}
```

At `12vw` (~45px on 375px), "Tarot Arcana" fits comfortably within viewport width.

**Diagnosis:** When the user reports the title is "too wide" or "超出 card 的宽度" — check the font-size clamp values on mobile breakpoints first. If they use `18vw`, that's almost certainly the culprit. The title will look oversized on any phone ≤414px wide.

**Pitfall: adjacent `margin-inline-end`.** Without spacing between the two inline spans, "TarotArcana" reads as a single word. Add `margin-inline-end: .15em` (or `gap` if using flex) for a natural word separation.

### File Size & Mobile Performance

The liveware frontend is built by Vite, which produces separate CSS (~22 KB) and JS (~96 KB) files. Total payload ~118 KB (gzip: ~40 KB). No manual minification is needed — Vite handles this automatically with Rollup in production mode.

The deck.json (79 KB) is fetched as a separate HTTP request and is cached by the browser after the first load.

### Card-Slot Centering — Flexbox vs. Grid

The card-slot (the dashed-border container around each position label + card) must center the card both horizontally and vertically on all window sizes. There are two approaches:

#### Approach A: Flexbox (recommended for centering)

```css
.card-slot {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 14px;
}
```

`align-items: center` centers the card horizontally; `justify-content: center` centers the card group vertically within the slot. This is the preferred approach when the card must stay centered regardless of window width.

#### Approach B: Grid (alternative)

```css
.card-slot {
  display: grid;
  grid-template-rows: auto minmax(0, auto);
}
```

The grid approach does **not** center the card vertically — content sits at the top of the slot. On wide windows the card may appear off-center. If you use grid, add `place-items: center` to force centering.

**Pitfall:** A grid with `grid-template-rows: auto minmax(0, auto)` and no centering will leave the card at the top of the slot. The user will report "卡片没有出现在边框的正中间" (card not centered in border) on wide windows. Fix: switch to flexbox or add `place-items: center`.

### CSS Card Sizing — Aspect Ratio vs. Min-Height

All card images are 300×527 pixels (aspect ratio ~0.569). There are **two valid approaches** to sizing them in the spread, with tradeoffs:

#### Approach A: Aspect-Ratio (proportional)

Use when the card height should follow the image's natural proportions. The card gets taller as the slot gets wider (e.g., ~510px tall for a 292px-wide slot in single-card mode).

```css
.tarot-card {
  width: 100%;
  aspect-ratio: 300 / 527;   /* image-native ratio */
}

.card-slot {
  display: grid;
  grid-template-rows: auto minmax(0, auto);  /* not auto 1fr */
}
```

Key rules:
- `aspect-ratio` goes on `.tarot-card` (the flip container), not on the `<img>` — keeps flip animation boundaries correct
- `.card-inner` uses `height: 100%` with `min-height: 0` (no forced minimum)
- `.empty-slot` keeps text placeholders (not card back images) — see "Empty slot behavior" section
- Mobile breakpoints must also override: `.tarot-card, .card-inner, .empty-slot { min-height: 0; }`

#### Approach B: Min-Height (compact)

Use when the user prefers compact cards that don't grow tall in single-card mode. Cards stay at a fixed minimum height; the image is fitted inside via `object-fit`.

```css
.tarot-card {
  width: 100%;
  min-height: 310px;          /* fixed compact height */
}

.card-slot {
  display: grid;
  grid-template-rows: auto 1fr;   /* card fills slot */
}
```

#### `object-fit` tradeoff (with PNG images)

Card faces are 240×336 PNG images (aspect ratio ~0.714). The tradeoff when sizing cards with `object-fit`:

| Value | Effect | When to use |
|-------|--------|-------------|
| `cover` | Image fills entire card, may crop edges | With matching aspect-ratio — reversed rotation is clearly visible |
| `contain` | Full image visible with dark letterboxing | With min-height approach; prevents cropping but **reversed rotation becomes less obvious** |

**Recommendation:** Prefer Approach A (aspect-ratio) with `object-fit: cover` for a polished look where card proportions are true to the physical deck. Fall back to Approach B (min-height + contain) if the user reports cards as "too large" or "enlarged" in single-card mode.

#### Reversed card indicator

Reversed cards are shown by rotating the image 180° — no badge or label needed. The rotation is applied via two CSS rules:

```css
/* rotate the image inside the card */
.card-face-img.is-reversed {
  transform: rotate(180deg);
}
/* rotate the entire front face so the 3D flip animation stays correct */
.face.front.is-reversed {
  transform: rotateY(180deg) rotate(180deg);
}
```

With 240×336 PNG images, the 180° rotation is clearly visible. If switching to images with a different aspect ratio or `object-fit: contain`, the rotation may become less visually obvious — use `object-fit: cover` instead or switch to aspect-ratio sizing. Do NOT add a badge or label — the user prefers the card to simply be visually upside down.
### Liveware reading flow

1. The user draws or submits cards through the web UI.
2. The liveware server sends the card data to the Hermes API Server and asks the agent to use `tarot-arcana` for interpretation.
3. The agent analyzes the submitted cards using this skill's interpretation and spread references.
4. The reading is saved under `~/tarot-readings/`.
5. The HTTP response returns the interpretation to the frontend without ClawChat delivery.
6. If the user clicks the **Send to ClawChat** button, the frontend calls the delivery endpoint; the server keeps the existing delivery prompt unchanged and sends the visible reading to ClawChat.

> **Prompt architecture:** The prompt sent to the API server in step 2 has a specific structure — task description, required skills, user question, submitted cards, and output requirements. See `skill_view(name='tarot-arcana', file_path='references/liveware-server-prompt.md')` for the full prompt structure, output format requirements, and the lessons learned about what to include vs. exclude in the output requirements section.

### Post-reading follow-up & agent querying

When the user follows up in conversation about a web reading, use the saved files under `~/tarot-readings/` for context. Prefer `latest.json`; otherwise read `index.json` and then the referenced markdown file.

`index.json` is an array of all readings, newest first. Each entry includes `question`, `timestamp`, `spread` (card count), and `cards` (name + orientation + position). No frontend history UI exists — the agent queries readings directly via file tools.

**Query patterns the agent can use (no frontend changes needed):**

| Goal | How |
|------|-----|
| List recent readings with questions | `python3 -c "import json; rs=json.load(open(os.path.expanduser('~/tarot-readings/index.json'))); ..."` iterate entries, print timestamp + question + card names |
| Search by question keyword | `search_files(pattern='吵架', path='~/tarot-readings')` — searches `.md` files for keyword |
| Search by card name | `grep -rl '死神' ~/tarot-readings/*.md` or `search_files` for card name |
| Read full interpretation | `read_file(path='~/tarot-readings/20260708-0839-*.md')` — use the filename from index |
| Get latest reading | `read_file(path='~/tarot-readings/latest.json')` — always the most recent |

The agent should answer directly from these files when asked "帮我查一下之前关于 X 的解读" or "我上次抽到 Y 的时候问了什么".

## Verification

For a normal reading:

- The draw command succeeds and returns valid JSON.
- `cards.length` matches the selected spread: 1 for `one_card`, 3 for `three_card`.
- Cards are not duplicated in one draw.
- Every interpreted card appears in the draw output with the correct position and orientation.
- The interpretation follows the reference sequence and includes actionable advice.
- The tone stays reflective, useful, and non-fear-based.

For liveware:

- `POST /api/interpret` prompts the Hermes API Server agent to use `tarot-arcana` for analysis.
- `POST /api/interpret` returns a response to the frontend without sending to ClawChat.
- A reading file and `index.json` entry are written under `~/tarot-readings/`.
- The **Send to ClawChat** button calls the delivery endpoint only after the user clicks it.
- Follow-up conversation can recover the latest reading from `latest.json` or the indexed markdown file.

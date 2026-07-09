# Mobile Touch Fix: Drag-Based Card Picker on Mobile Browsers

> **Note (2025-07-08):** The app uses double-click via a `Date.now()` threshold check in SolidJS native `onClick` (400ms window, same card index). The drag-scroll guard uses a `pointerMoved` flag. See the "Pitfall — `For` + `createMemo` identity" section in the main SKILL.md for the current approach. This reference is preserved as a historical record of the mobile debugging path.

## Problem

The deck picker's horizontal drag (swipe to browse cards) worked on desktop but not on mobile. On desktop, `pointerdown` → `pointermove` → `pointerup` events handled the drag; on mobile, touching and dragging produced no movement.

## Root Cause

Two issues:

1. **`touch-action: pan-y`** — the deck zone and deck-picker CSS had `touch-action: pan-y` (only vertical touch allowed). On mobile, this tells the browser to intercept horizontal touch gestures — the browser consumes the gesture for its own scroll handling, and pointer events for horizontal movement either don't fire or are suppressed.

2. **No touch event fallback** — some mobile browsers (especially iOS Safari) don't dispatch `pointermove` events reliably when `touch-action: none` is set on a parent with `overflow: hidden`. The pointer events API is supported but its behavior across mobile browsers is inconsistent.

## Fix

Three changes were required:

### 1. `touch-action: pan-y` → `touch-action: none`

All elements in the touch path need explicit `touch-action: none`:

```css
.deck-zone.is-selecting {
  touch-action: none;
}

.deck-zone.is-selecting .deck-picker {
  touch-action: none;
}

.deck-zone.is-selecting .deck-picker-card {
  touch-action: none;
}

/* Base styles (always active) */
.deck-picker {
  touch-action: none;
}

.deck-picker-card {
  touch-action: none;
}
```

`touch-action: none` tells the browser to pass all touch events to JavaScript without any default handling — no native scroll, no tap delay, no double-tap zoom.

### 2. Replace `setPointerCapture` with document-level listeners

**⚠️ Critical: `setPointerCapture` on a parent element prevents `click` events on child elements on desktop Chrome.**

When the deck-picker captures the pointer (via `setPointerCapture(e.pointerId)` in `onPointerDown`), all subsequent `click` and `dblclick` events are dispatched to the capturing element (the deck-picker), NOT to the child card button. The card's `bindCardTap` handlers never fire — the user sees cards but can't select them.

**Do NOT use `setPointerCapture` at all.** Instead, register `pointermove`/`pointerup` on `document` inside `onPointerDown`:

```typescript
function onPickerPointerDown(e: PointerEvent) {
  if (!pickerRef) return
  startScrollLeft = pickerRef.scrollLeft
  startX = e.clientX
  isDragging = true
  pickerRef.classList.add('is-dragging')
  // Track move/up on document — avoids pointer capture blocking card click events
  document.addEventListener('pointermove', onDocPointerMove)
  document.addEventListener('pointerup', onDocPointerUp)
}
function onDocPointerMove(e: PointerEvent) {
  if (!isDragging || !pickerRef) return
  const delta = e.clientX - startX
  const maxScroll = Math.max(0, pickerRef.scrollWidth - pickerRef.clientWidth)
  pickerRef.scrollLeft = Math.max(0, Math.min(maxScroll, startScrollLeft - delta))
}
function onDocPointerUp() {
  if (!pickerRef) return
  isDragging = false
  pickerRef.classList.remove('is-dragging')
  document.removeEventListener('pointermove', onDocPointerMove)
  document.removeEventListener('pointerup', onDocPointerUp)
}
```

Why this works:
- `setPointerCapture` is never called, so `click`/`dblclick` events always reach the card button target
- Document-level listeners track the pointer even if it leaves the deck-picker element (no lost drag state)
- `onPointerMove` and `onPointerUp` on the deck-picker template become no-ops (or delegates) — the real logic lives in the document listeners
- Works identically on desktop and mobile

**Do NOT try to "fix" by releasing capture in `onPointerUp`** — the damage is done at `pointerdown` time. The browser's internal event routing has already committed to the capturing element by the time `click` fires.

```javascript
// ❌ BAD — capture is set at pointerdown, releasing in pointerup is too late
el.setPointerCapture(e.pointerId)  // click target is now the capturing element

// ❌ BAD — even releasePointerCapture in pointerup doesn't help
// because the click event's target was already determined at pointerdown

// ✅ GOOD — never call setPointerCapture, use document listeners instead
document.addEventListener('pointermove', onMove)
document.addEventListener('pointerup', onUp)
```

**Legacy note:** Previous versions of this reference suggested just removing `setPointerCapture` and relying on `activePointerId` tracking. That works on mobile but on desktop, the deck-picker's `onPointerMove`/`onPointerUp` handlers stop receiving events when the pointer leaves the element — document-level listeners are required for reliable behavior on all platforms.

### 3. Add touch event listeners as fallback

Pointer events + touch-action:none still don't work reliably on all mobile browsers. Add native touch event listeners that share the same drag logic:

```javascript
// Touch Events (fallback for mobile browsers)
dragSurface.addEventListener('touchstart', event => {
  const touch = event.touches[0];
  if (!touch) return;
  activePointerId = 0;
  onPointerDown(touch.clientX);
}, { passive: true });

dragSurface.addEventListener('touchmove', event => {
  const touch = event.touches[0];
  if (!touch) return;
  event.preventDefault();
  onPointerMove(touch.clientX);
}, { passive: false });

dragSurface.addEventListener('touchend', () => endDrag(), { passive: true });
dragSurface.addEventListener('touchcancel', () => endDrag(), { passive: true });
```

Key points:
- `touchstart` is `passive: true` (no `preventDefault()` needed on start)
- `touchmove` is `passive: false` so `event.preventDefault()` works
- Both pointer and touch events call the same `onPointerDown`/`onPointerMove`/`endDrag` functions
- The `activePointerId` check prevents the two event systems from conflicting (pointer events set `activePointerId` to a real pointerId, touch events set it to `0`)

### The shared core logic

```javascript
function onPointerDown(x) {
  if (!state.isChoosing || !state.deckPool.length) return;
  isPointerDown = true;
  isDragging = false;
  moved = false;
  startX = x;
  startScrollLeft = deckPicker.scrollLeft;
}

function onPointerMove(x) {
  if (!isPointerDown) return;
  const delta = x - startX;
  if (Math.abs(delta) <= dragThreshold && !isDragging) return;
  if (!isDragging) {
    isDragging = true;
    deckZone.classList.add('is-dragging');
    deckPicker.classList.add('is-dragging');
  }
  moved = true;
  suppressClick = true;
  const maxScroll = Math.max(0, deckPicker.scrollWidth - deckPicker.clientWidth);
  deckPicker.scrollLeft = Math.max(0, Math.min(maxScroll, startScrollLeft - delta));
}

function endDrag() {
  if (!isPointerDown) return;
  isPointerDown = false;
  deckZone.classList.remove('is-dragging');
  deckPicker.classList.remove('is-dragging');
  isDragging = false;
  activePointerId = null;
  if (moved) window.setTimeout(() => { suppressClick = false; }, 90);
  else suppressClick = false;
}
```

## Why This Works

| Technique | Purpose |
|-----------|---------|
| `touch-action: none` on all involved elements | Prevents browser from intercepting touch for native scroll/zoom |
| Shared drag logic | One set of state variables, two event sources |
| Touch event fallback | Covers browsers where Pointer Events API is unreliable |
| No `setPointerCapture` | Avoids mobile-specific capture bugs |
| `suppressClick` after drag | Prevents the click event that fires after a swipe from triggering card selection |

## Verification

1. Open the app on a real mobile device or mobile emulator (Chrome DevTools device mode).
2. Tap "洗牌并抽牌" to reveal the card picker.
3. Touch a card and drag horizontally — cards should scroll smoothly.
4. Double-tap a card to select it.
5. On iOS, verify that long-press does NOT show the context menu.

---

# Mobile Touch Fix: Double-Tap Card Selection on Mobile

## Problem

After the drag fix was applied, double-tapping a card to select it still had issues on mobile:
- The tap was sometimes not recognized (missed double-tap detection)
- The interaction felt sluggish (300ms click delay on mobile)
- On some mobile browsers, the `click` event fired in addition to touch events, causing duplicate selection attempts

## Root Cause

Three issues:

1. **300ms tap delay** — mobile browsers introduce a ~300ms delay on `click` events while waiting to see if the tap is actually a double-tap gesture. When detection relied on counting `click` events, the delay made the interaction feel sluggish.

2. **Click suppression vs touch detection** — the drag fix used `suppressClick` to prevent drag-triggered clicks from selecting cards. But on mobile, taps that were NOT drags still relied on the `click` event, which was delayed and sometimes suppressed by the drag guard.

3. **Touch event not explicitly prevented from generating a click** — on mobile, a `touchend` fires first, then ~300ms later a `click` fires. Without explicit handling, both events can trigger the same selection logic.

## Fix

### 1. Rewrite `bindDoubleTap` with native touch events

Replace click-based double-tap detection with touch-based detection:

```javascript
function bindDoubleTap(button, handler) {
  let touchHandled = false;
  let lastTap = 0;

  button.addEventListener('touchstart', () => {
    touchHandled = false;
  }, { passive: true });

  button.addEventListener('touchmove', (e) => {
    const touch = e.touches[0];
    if (!touch) return;
    // Check if the finger moved more than 10px — treat as swipe, not tap
    const rect = button.getBoundingClientRect();
    const dx = touch.clientX - (rect.left + rect.width / 2);
    const dy = touch.clientY - (rect.top + rect.height / 2);
    if (Math.sqrt(dx * dx + dy * dy) > 10) {
      touchHandled = true;
    }
  }, { passive: true });

  button.addEventListener('touchend', (e) => {
    if (touchHandled) return;
    e.preventDefault(); // Prevent the click event from also firing
    touchHandled = true;

    const now = Date.now();
    if (now - lastTap < 360) {
      // Double-tap detected
      handler(e);
    }
    lastTap = now;
  }, { passive: false });
}
```

### 2. Add `touch-action: manipulation` at the app level

```css
.app {
  touch-action: manipulation;
}
```

`touch-action: manipulation` removes the 300ms tap delay on mobile while preserving vertical scrolling and pinch-zoom. This is a broader CSS fix than per-element `touch-action: none` (used for the drag gesture).

### 3. Use `touchHandled` flag to isolate touch and click

The `touchHandled` flag is set to `true` in `touchend` and blocks the subsequent `click` event from doing anything. This prevents duplicate selection:

```javascript
button.addEventListener('click', (e) => {
  if (touchHandled) {
    touchHandled = false;
    return;
  }
  // Desktop click path — only fires when touch events didn't handle it
  ...
});
```

### 4. Add movement detection to distinguish swipe from tap

On `touchmove`, if the finger moves more than 10px from the initial touch point, `touchHandled` is set to `true`. This prevents a swipe gesture from being interpreted as a tap.

### 5. Reduce backdrop-filter GPU cost on mobile

Heavy `backdrop-filter` values (e.g., 18px) consume significant GPU resources on mobile. Reducing to 6px on screens narrower than 820px improves scroll and animation smoothness:

```css
@media (max-width: 820px) {
  .panel,
  .oracle-panel {
    backdrop-filter: blur(6px);
    -webkit-backdrop-filter: blur(6px);
  }
}
```

## Why This Works

| Technique | Purpose |
|-----------|---------|
| Touch-based double-tap detection | Eliminates 300ms click delay — detects taps in real time |
| `touch-action: manipulation` | Removes tap delay globally while preserving scroll |
| `touchHandled` flag | Prevents duplicate touch+click event processing |
| Movement threshold (10px) | Distinguishes intentional tap from swipe gesture |
| `e.preventDefault()` on touchend | Suppresses the synthetic click event after touch |
| Reduced backdrop-filter | Lower GPU compositing cost on mobile hardware |

## Verification

1. Open the app on a real mobile device or mobile emulator.
2. Tap "洗牌并抽牌" to reveal the card picker.
3. Double-tap a card — the card should be selected immediately (no 300ms delay).
4. Swipe horizontally through the picker — cards should scroll without triggering selection.
5. Tap a single card once — should NOT select (double-tap is required).
6. Verify on both iOS Safari and Android Chrome.
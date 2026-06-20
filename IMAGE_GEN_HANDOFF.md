# Handoff — generate a crisp "Catalytic Silence" lab UI mockup (whipgen-mcp)

**Audience:** the next agent, with no prior conversation context.
**Goal:** produce **one sharp, fully-rendered 16:9 concept mockup** of the web9
"Catalytic Silence" lab UI and deliver it **inline as a rendered image** to the
user. A previous attempt produced a blurry, half-rendered capture; this doc
explains exactly why and how to get a clean result on the first real try.

---

## 0. TL;DR — do this

1. Load whipgen tools via `ToolSearch` (prefix may change — see §6), then call
   **`whipgen_help`** with no args (required first call; suppresses the reminder banner).
2. `whipgen_route` (goal: "generate a UI mockup image") + `whipgen_health` to see live state.
   **Ignore route's asim recommendation** — asim image-gen is UI-broken (see §3).
3. **`whipgen_warmup` providers `["gemini"]`, mode `"capability"`** — clears Gemini's
   cold start so the next sync call fits under the 60s transport cap.
4. Generate on **Gemini/Imagen** with a **fresh `name`** (or `force:true`),
   **`returnBytes:true`**, and the anti-blur prompt in §5. This returns the PNG as
   an **MCP image content block** that renders to the user cross-host.
5. Eyeball it. If sharp → done. If still soft → see §7 escalation.

Cost ≈ **$0.04** per Gemini image. Don't loop generations without checking output.

---

## 1. What "done" looks like

A high-fidelity, **legible**, sharp 16:9 image of a dark scientific-instrument web
app titled "CATALYTIC SILENCE": left Roman-numeral stage rail (I–XIII), a center
3D hydrothermal-vent apparatus, a circular SEM micrograph panel, a right-hand
parameter/regime control stack with a small chart, a top view-toggle
(LAB / SPLIT / LIVE-SEM), a bottom provenance strip, and a tiny amoeba guide.
Rendered **inline in chat**, not just saved to disk.

## 2. Current state / artifacts

- A **poisoned** asset exists: name **`web9_ideal_lab_ui`**, file
  `F:\whipgen-mcp\whipgen-out\web9_ideal_lab_ui.png` (1.37 MB). It is the
  blurry mid-render capture. **Do NOT reuse this name** without `force:true` —
  generate is cached by `name` and will hand back the bad bytes.
- It was produced via `whipgen_generate_image` (ChatGPT) with `failover:true` +
  `returnBytes:true`. It rendered, but quality is unacceptable.

## 3. Root-cause diagnosis (read this — it's the whole game)

- **The blur = progressive-render captured mid-reveal.** ChatGPT reveals images
  with a "blur-up" animation; the daemon's browser automation grabbed the frame
  before it sharpened. Composition is correct, focus isn't. This is a
  provider/automation timing flake, **not** a prompt problem.
  → **Fix:** use **Gemini/Imagen**, which returns a *finished image file* (no
  progressive chat-canvas reveal), so there's no half-rendered frame to capture.
- **Cache is keyed by `name`.** The bad frame is cached under `web9_ideal_lab_ui`.
  → **Fix:** use a **new name** (e.g. `web9_lab_ui_v2`) or `force:true`.
- **asim image-gen is broken** at the UI layer: jobs fail with
  `"Generate action button not found."` even though `whipgen_health`/`whipgen_route`
  report asim *available* (they read health, not runtime UI state).
  → **Do not use asim for images.** `whipgen_route` will still *recommend* it — ignore that.
- **60s MCP transport cap.** A synchronous generate that includes cold-start
  warmup + a large `returnBytes` payload exceeds 60s and the **transport** times
  out — even though the **daemon job completes** (it ran in ~27s). `failover:true`
  forces the sync path, compounding this.
  → **Fix:** warm Gemini first (§0.3) so the real call is fast; keep payload to
  one image. A proven-fast path is a **cache hit** (same name, `force:false`,
  `returnBytes:true`) which returns instantly — but only after a *good* asset
  exists under that name.
- **Cross-host retrieval.** Daemon runs on **Windows host `ToxicAvenger`**
  (`F:\…` paths); the agent runs in a **Linux container**, so `savedTo` paths are
  unreachable. You must pull bytes back as an **MCP image content block**:
  - `whipgen_generate_image` / `whipgen_gemini_generate_image` with
    **`returnBytes:true`** → image block inline (≈50 KB–2 MB). ✅
  - `whipgen_get_asset` with **`includeImage:true`** → optimized image block. ✅
    (but see index caveat below)
  - **NOT** `whipgen_job_status.result.base64` for big images — that's a ~6 MB
    base64 **string in JSON** → blows the tool-result token cap and won't render. ❌
  - **NOT** a `savedTo` path — unreachable from Linux. ❌
- **Index vs outDir mismatch.** `whipgen_get_asset`/`whipgen_search_assets` read a
  **persistent index**; the `returnBytes` auto-save writes the PNG + sidecar to
  **outDir** but does **not** register it in that index. So `get_asset` by name
  **404s** for auto-saved files, while `whipgen_list` (reads outDir) shows them.
  → Prefer the **`returnBytes` inline path** for delivery; don't rely on
  `get_asset` unless the asset is actually indexed.

## 4. Execution plan (precise)

> Tool names below omit the MCP prefix. Discover the real prefix via ToolSearch (§6).

1. `whipgen_help` (no args).
2. `whipgen_route` { goal: "generate a high-res UI mockup image, 16:9 dark lab app" }
   and `whipgen_health` — confirm `gemini-image` is present (likely `dormant:true`)
   and `chatgpt-image` available. Note asim caveat.
3. `whipgen_warmup` { providers: ["gemini"], mode: "capability" } — wait for `ok`.
4. `whipgen_help` { topic: "whipgen_gemini_generate_image" } — confirm its
   `returnBytes` / `saveTo` / `async` / aspect-ratio params (Imagen uses aspect
   ratios; pass the nearest 16:9, e.g. width 1792 × height 1024 or the tool's
   `aspectRatio:"16:9"`).
5. **Generate (primary path):** `whipgen_gemini_generate_image` {
   `name: "web9_lab_ui_v2"`, `prompt: <§5>`, `returnBytes: true`,
   `saveTo: "F:\\whipgen-mcp\\whipgen-out\\web9_lab_ui_v2.png"` (optional backup;
   must be under `allowedWriteRoots` = `F:\whipgen-mcp`), 16:9 sizing }.
   - If the Gemini tool's `returnBytes` only works with `saveTo` set, set both.
6. **Verify** the rendered block is sharp + legible. If yes → deliver, done.
7. **Fallback if Gemini sync still times out at 60s:** call with `async:true` +
   `saveTo`, poll `whipgen_job_status` (interval ~1s, give up at
   `max_duration_ms` 240000). On `done`, you still need a renderable block — if
   `get_asset includeImage` 404s (unindexed), re-issue a **cache-hit**
   `whipgen_gemini_generate_image` with the **same name** + `force:false` +
   `returnBytes:true` (instant, returns the bytes inline). This "cache-hit
   returnBytes" trick is proven to render cross-host.

## 5. The prompt (anti-blur, refined — paste verbatim)

```
A sharp, fully-rendered, high-fidelity UI design mockup — a flat 2D product
screenshot (not a photo) of a dark, elegant scientific-instrument web app titled
"CATALYTIC SILENCE", an origin-of-life cellular-automata laboratory. 16:9 desktop
layout. Crisp vector-clean edges, pixel-sharp legible typography, fully in focus.
NO photographic blur, NO bokeh, NO depth-of-field, NO motion blur, NO film grain.

Style: museum vitrine meets precision lab instrument. Near-black obsidian
background, luminous teal-cyan accents, warm bone-white text, thin hairline rules,
generous negative space, high-contrast didone serif display headings with neat
monospaced numeric readouts.

Layout, left to right:
- Far-left vertical rail: Roman-numeral stage index I to XIII; "VII RNA WORLD"
  highlighted in glowing teal.
- Center-left hero panel: a clean 3D-rendered lab apparatus on a dark plinth —
  borosilicate glassware and a hydrothermal-vent mineral chimney, crisp studio
  rim lighting, sharp detail (rendered, not photographed).
- Center-right: a circular scanning-electron-micrograph panel of greyscale
  reaction-diffusion microstructure, with a small caption tag "SEM RENDER —
  synthetic, not live feed".
- Far-right control panel: a vertical stack of labelled parameter sliders each
  with a numeric value + units, a "REGIME" preset dropdown pinned at top, a
  "SWEEP: 24 seeds" control, and below it a small line chart with a shaded error band.
- Top bar: a segmented toggle "LAB / SPLIT / LIVE-SEM" and a green status chip "VIABLE".
- Thin bottom strip: a run-manifest provenance readout (seed, commit hash, timestamp).
- A tiny translucent glowing amoeba guide creature in the lower-left corner.

Sharp, clean, cinematic but legible. No watermark.
```

## 6. Connection / environment facts

- **The whipgen MCP connection is provisioned by the remote web environment**, not
  by any repo file. The only on-disk reference is a *stale permissions allowlist*
  in `.claude/settings.local.json` pointing at the old uuid prefix
  `mcp__7912963c-66a7-4bc5-908d-244ffe2ad265__*`. There is no `.mcp.json` /
  `mcpServers` block to edit.
- **The tool prefix can change across reconnects.** Observed: original
  `mcp__7912963c-66a7-4bc5-908d-244ffe2ad265__*` → a broken half-handshake server
  named `whip` (instructions loaded, **zero tools** — `mcp__whip__…` calls returned
  "No such tool available") → back to the original uuid prefix. **Always discover
  via `ToolSearch`** (e.g. `select:mcp__<prefix>__whipgen_help,…` or keyword
  `"whipgen route gemini status"`) before calling. If `ToolSearch` returns nothing
  and a direct call says "No such tool available", the server is disconnected or
  half-open — only a reconnect/fresh session fixes it; nothing in-session does.
- **Daemon facts** (from `whipgen_status`):
  - host `ToxicAvenger`, platform `win32`, outDir `F:\whipgen-mcp\whipgen-out`,
    port 9223, CDP debugUrl `http://127.0.0.1:9222`.
  - `allowedWriteRoots`: `F:\whipgen-mcp`
  - `allowedReadRoots`: `C:\Users\guru8`, `C:\code`, `F:\whipgen-mcp\whipgen-out`
  - image cost/img: asim $0.02, chatgpt $0.04, gemini $0.04.
  - asim pilots: video `343003`, image `254047` (image one is the broken UI).

## 7. Escalation if Gemini also comes back soft

- Confirm it's not a cache hit on a bad name (use a brand-new `name`).
- Try a different size / explicit `aspectRatio:"16:9"`.
- Inspect `whipgen_job_status.result` for a `variants[]` with a higher-res entry.
- If multiple providers blur identically, the daemon's **capture timing** is the
  culprit (provider-independent) — report it to the user with the failing jobIds
  rather than burning more credits; it's a daemon-side fix
  (wait-for-render-settle before screenshot), not promptable.

## 8. Do-not list

- Don't use **asim** for images (UI broken) — and don't trust route's asim pick.
- Don't reuse name **`web9_ideal_lab_ui`** without `force:true` (poisoned cache).
- Don't retrieve large images via `job_status.result.base64` (token-cap blowup).
- Don't set `failover:true` unless you accept forced-sync + the asim middle hop.
- Don't restart the daemon as a probe (drops in-flight jobs); use `whipgen_status`.
- Don't `whipgen_list` with `includeMeta:true` and dump it raw — it's ~84 KB; it
  will exceed the tool-result cap. Filter/grep the saved output instead.

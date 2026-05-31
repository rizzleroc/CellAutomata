# PRD — VibeVoice TTS/ASR as a whipgen-mcp Service

| | |
|---|---|
| **Status** | Draft v0.1 — for review |
| **Author** | cellauto social/content tooling |
| **Date** | 2026-05-30 |
| **Owners** | whipgen-mcp maintainer · local GPU host owner |
| **Target host** | Local workstation, **NVIDIA RTX 5090** (Blackwell, ~32 GB VRAM) |
| **Related** | `marketing/social/voiceover/` (scripts + muxer), `marketing/social/build_reels.py` |

---

## 1. Summary

Add **[microsoft/VibeVoice](https://github.com/microsoft/VibeVoice)** — Microsoft's
open-source, long-form, multi-speaker **TTS** (and, in a later phase, **ASR**)
model family — to **whipgen-mcp** as a first-class provider, served from a
persistent inference process on a local **RTX 5090**. The MCP gains a new
`voice-gen` tool family (`whipgen_vibevoice_*`) that follows whipgen's existing
conventions (async job model, per-provider queue, `whipgen_job_status` polling,
`saveTo` write-root rules, session isolation, `whipgen_health`/`whipgen_status`
wiring, `whipgen_help` drill-down docs, structured error codes).

This is the missing modality: whipgen today covers image, video, 3D, LLM chat,
vision, and structured artifacts — **but has no speech synthesis**. The
immediate driver is the cellauto reel program: 30 vertical reels that each need
a ~10–13 s narration. Today that pipeline is blocked because the build
environment has no GPU and blocks HuggingFace; a 5090-hosted VibeVoice service
removes the blocker for every whipgen consumer.

---

## 2. Motivation & problem statement

- **Capability gap.** whipgen orchestrates ChatGPT/Claude/Kimi/Gemini/Imagen/
  Veo/ASIM/Tripo but offers **no TTS**. Voiceover, narration, podcast audio, and
  audio-overview workflows must currently leave the MCP (e.g. NotebookLM
  overview, which is uncontrollable per-clip).
- **Concrete need.** `marketing/social/voiceover/scripts.json` holds 30
  finished narration scripts. `add_voiceover.py` already muxes WAVs into reels.
  The only missing link is a controllable, high-quality, **self-hostable** TTS
  that can run where HuggingFace weights are reachable.
- **Environment reality.** CI / sandbox build hosts (where reels are assembled)
  have **no GPU** and a network policy that **blocks huggingface.co** (and
  hf-mirror / ModelScope). VibeVoice weights only ship via HF. A persistent
  **local 5090 service** is the natural place to run the model once and serve
  synthesis over the network to any whipgen consumer.
- **Quality bar.** VibeVoice is a frontier open model: long-form (up to ~90 min),
  up to 4 distinct speakers, expressive prosody, voice-prompt cloning — far above
  espeak-class fallbacks.

---

## 3. Goals / Non-goals

### Goals
- G1 — A new whipgen provider **`vibevoice`** and `voice-gen` family with at
  least `whipgen_vibevoice_tts`, `whipgen_vibevoice_voices`, and health wiring.
- G2 — Synthesize single- and multi-speaker scripts to WAV/MP3, async, with
  `jobId` + `whipgen_job_status` polling identical to other slow tools.
- G3 — Run as a **persistent GPU service** on the 5090 (model resident in VRAM),
  proxied by the whipgen daemon over HTTP — mirroring the existing `touch-app`
  proxy pattern (`whipgen_touch_*` + `touch-proxy-unreachable`).
- G4 — First-party use case proven: generate all 30 reel WAVs from
  `scripts.json`, mux via `add_voiceover.py`, produce `reels_voiced/`.
- G5 — Honour VibeVoice's responsible-AI protections (audible AI disclaimer +
  watermark) and a first-party-scripts-only authorization posture.

### Non-goals (this PRD)
- N1 — Real-time/streaming conversational TTS (`Realtime-0.5B`) — phase 3.
- N2 — ASR/transcription (`VibeVoice-ASR`) — phase 3 (useful for auto-captions).
- N3 — Multi-GPU / multi-host autoscaling. Single 5090, single process.
- N4 — A general voice-cloning product surface for arbitrary third-party voices
  (consent-gated; see §10).

---

## 4. Background

### 4.1 VibeVoice model family
- **VibeVoice-TTS** — long-form, multi-speaker. **`microsoft/VibeVoice-1.5B`**
  (64K context, ~90 min, up to 4 speakers). **`VibeVoice-Large`** (32K, ~45 min;
  availability varies — confirm current model-card status/license).
- **VibeVoice-Realtime-0.5B** — streaming, low-latency, `--device cpu|cuda|mps`.
- **VibeVoice-ASR** — long-form speech-to-text (Who/When/What), now available
  via HF Transformers.
- **Architecture** — continuous acoustic+semantic tokenizers at **7.5 Hz**, an
  LLM backbone for context/dialogue, and a **next-token diffusion** head for
  acoustic detail. Code deps: `torch`, `transformers>=4.51.3,<5`.
- **Inputs** — transcript form, `Speaker 1: … / Speaker 2: …`; a per-speaker
  voice preset (`.pt`) or a short reference clip for cloning. `cfg_scale`
  (~1.3–1.5) trades fidelity vs. adherence.
- **Responsible AI** — Microsoft ships an **audible "AI-generated" disclaimer**
  and an **imperceptible watermark**; the project was briefly withdrawn over
  misuse concerns. These protections **must be preserved**, not stripped.

### 4.2 RTX 5090 considerations (Blackwell, sm_120)
- Requires a **CUDA 12.8-class PyTorch** build (`cu128`; torch ≥ 2.7 stable, or
  nightly) for `sm_120`. Pin this in the service env — it is the #1 setup risk.
- **VRAM:** `1.5B` in bf16 is a few GB and fits comfortably in 32 GB; `Large`
  needs more — both can plausibly stay resident. Optional FlashAttention-2.
- Weights downloaded **once** on the local box (HF reachable there) into a
  persistent `HF_HOME` cache.

### 4.3 whipgen-mcp conventions the new tools MUST follow
(from `whipgen_help`):
- **Naming:** `whipgen_<verb>` / `whipgen_<provider>_<verb>`; group under a
  `family` (new: `voice-gen`). Each tool gets a `whipgen_help` topic with full
  schema + examples + `common_errors` + `chains_well_with`.
- **Async:** anything > ~10 s returns `{ jobId, queued: true }`; poll
  `whipgen_job_status` (terminal: `queued|running|done|error|cancelled`; results
  retained ~1 h). Long synth (multi-minute) is async-first.
- **Queues:** per-provider. Single GPU ⇒ `vibevoice` queue **concurrency 1**
  (optionally micro-batched); does not block other providers.
- **Save paths:** `saveTo` must be inside `WHIPGEN_ALLOWED_WRITE_ROOTS` else
  `save_to_outside_allowed_roots`; otherwise return base64 audio.
- **Session isolation:** tag jobs with `sessionId`; `whipgen_job_status` only
  returns the caller's jobs; foreign cancels → `cross_session_access`.
- **Preflight/health:** `whipgen_health` adds a `vibevoice-tts` provider entry;
  `whipgen_status` reports queue depth; `whipgen_warmup` can preload the model;
  `whipgen_connect`-style reattach for the service socket.
- **Proxy precedent:** the **touch-app** integration (`whipgen_touch_generate`
  → Next.js backend, `whipgen_touch_health`, error `touch-proxy-unreachable`) is
  the blueprint: an out-of-process backend reached over HTTP, with a health
  probe and a dedicated "unreachable" error.

---

## 5. Proposed architecture

```
 MCP consumer (Claude/agent)
        │  whipgen_vibevoice_tts {script, speakers, model, saveTo, async}
        ▼
 whipgen-mcp daemon
   • VibeVoiceDriver  (new) — enqueues on the `vibevoice` queue (concurrency 1)
   • tags job w/ sessionId, returns {jobId, queued}
        │  HTTP (localhost or Tailscale/SSH tunnel)
        ▼
 vibevoice-svc  (new, on the RTX 5090)
   • FastAPI/uvicorn, models resident in VRAM (1.5B [+ Large])
   • POST /tts, GET /voices, POST /voices/register, GET /health, POST /asr
   • inserts audible disclaimer + watermark; writes WAV/MP3
        │
        ▼  audio (path under an allowed write-root, or base64)
 add_voiceover.py  (existing) → marketing/social/reels_voiced/
```

### 5.1 `vibevoice-svc` (the GPU service)
- **Process:** Python + FastAPI/uvicorn, single worker, model(s) preloaded at
  startup; runs under **systemd** (`Restart=always`), bound to `127.0.0.1:8077`.
- **Endpoints**
  - `POST /tts` → body `{ script, speakers[], model, cfg_scale, ref_audio?,
    format("wav"|"mp3"), sample_rate }`; returns
    `{ audio_b64 | path, sample_rate, duration_s, watermarked: true,
    disclaimer: true }`.
  - `GET  /voices` → built-in presets + registered clones.
  - `POST /voices/register` (multipart ref clip + name, **consent flag**) →
    `{ voice_id }`.
  - `GET  /health` → `{ ok, gpu, driver_cuda, vram_total, vram_free,
    models_loaded[], queue_depth }`.
  - `POST /asr` (phase 3) → `{ segments:[{speaker,start,end,text}] }`.
- **Concurrency:** internal single-flight (GPU-bound) + bounded request queue;
  optional micro-batch of short clips.
- **Config (env):** `VIBEVOICE_MODELS`, `HF_HOME`, `PORT`, `MAX_CHARS`,
  `WRITE_ROOT`, `ALLOW_VOICE_CLONE`.
- **Networking:** same host as daemon ⇒ localhost. Remote daemon ⇒ Tailscale or
  SSH tunnel; never expose the port publicly unauthenticated.

### 5.2 whipgen daemon integration
- New **`VibeVoiceDriver`** registered as provider `vibevoice`, with:
  health canary (`GET /health`), connect/reattach, a `vibevoice` queue
  (concurrency 1), `warmup` (preload), and job tagging/ownership.
- Wire into `whipgen_health`, `whipgen_status`, `whipgen_warmup`,
  `whipgen_connect`.
- Add `whipgen_help` topics for the family and each tool.

---

## 6. New MCP tools (specs)

> Schemas follow the whipgen tool-doc shape (`name/family/stability/input/
> output/async/side_effects/safety/common_errors/chains_well_with`).

### 6.1 `whipgen_vibevoice_tts`  *(family: voice-gen, stability: beta)*
Long-form, single- or multi-speaker synthesis.

```jsonc
input: {
  "script":    "string  // 'Speaker 1: ...\\nSpeaker 2: ...' or plain text",
  "speakers":  "string[]?  // preset names or registered voice_ids, in order",
  "model":     "enum('1.5b','large') = '1.5b'",
  "cfg_scale": "number = 1.4",
  "format":    "enum('wav','mp3') = 'wav'",
  "sampleRate":"number = 24000",
  "name":      "string?  // cache key (dedupe like other generate-* tools)",
  "saveTo":    "string?  // absolute path inside WHIPGEN_ALLOWED_WRITE_ROOTS",
  "async":     "boolean = true"
}
output: {
  "ok": true,
  "savedTo": "string?",        // when saveTo set
  "audioBase64": "string?",    // else inline
  "sampleRate": 24000,
  "durationS": 11.4,
  "watermarked": true
}
async:  { supported: true, poll_with: "whipgen_job_status", poll_interval_ms: 2000,
          typical_duration_ms: 8000, max_duration_ms: 300000 }
side_effects: "writes-disk"
safety: "free-to-call"
preflight_with: "whipgen_vibevoice_health"
best_for: ["reel/video narration","podcast/dialogue","audiobook-style long-form"]
common_errors: [
  {code:"vibevoice-unreachable", remedy:"start vibevoice-svc on the GPU host; check tunnel; whipgen_connect"},
  {code:"vibevoice-oom",         remedy:"use model '1.5b' or shorten script; lower batch"},
  {code:"model-not-loaded",      remedy:"whipgen_warmup vibevoice, or wait for service warmup"},
  {code:"save_to_outside_allowed_roots", remedy:"omit saveTo or use an allowed root"}
]
chains_well_with: ["whipgen_vibevoice_voices","whipgen_vibevoice_health"]
```

### 6.2 `whipgen_vibevoice_voices`  *(voice-gen, stable, probe-safe)*
List built-in presets + registered clones; optionally register a reference clip.
```jsonc
input:  { "register": { "name":"string","refAudioPath":"string","consent":true }? }
output: { "voices": [ { "id":"Wayne","kind":"preset" }, ... ] }
side_effects: "none | mutates-session(on register)"
```

### 6.3 `whipgen_vibevoice_health`  *(voice-gen, stable, probe-safe)*
```jsonc
output: { "ok":true,"gpu":"RTX 5090","vramFreeGB":29.1,
          "modelsLoaded":["1.5b"],"queueDepth":0 }
```
(Also surfaced as a provider row in `whipgen_health`.)

### 6.4 Phase-3 (deferred)
- `whipgen_vibevoice_stream` — streaming `Realtime-0.5B` (low-latency chunks).
- `whipgen_vibevoice_asr` — transcription → can auto-generate **burned-in
  captions/subtitles** for reels (high-value for TikTok retention).

---

## 7. First-party workflow (acceptance demo)

```bash
# one whipgen call per reel (async), polled to done, saved under an allowed root
for r in scripts.json:
    jobId = whipgen_vibevoice_tts(name=f"reel_{i:02d}",
              script="Speaker 1: "+r.script, speakers=["Wayne"],
              model="1.5b", saveTo=".../voiceover/wav/reel_{i:02d}.wav")
    poll whipgen_job_status(jobId) -> done
# then, anywhere (no GPU/HF needed):
python3 marketing/social/voiceover/add_voiceover.py   # -> reels_voiced/
```

Reuses the committed `scripts.json` + `add_voiceover.py` unchanged.

---

## 8. Performance targets (RTX 5090) — to be measured in M0
- **Throughput:** ≥ realtime by a wide margin for `1.5B`; target the full 30-reel
  batch (~5 min of audio) in **≤ 2 min** wall.
- **Latency (single ~12 s clip):** target **≤ 4 s** p50 once warm.
- **VRAM:** `1.5B` resident < ~8 GB; headroom for `Large` co-resident.
- **Reliability:** service warm-start < 30 s; `Restart=always`.

---

## 9. Testing & acceptance criteria
- A1 — `whipgen_vibevoice_health` green; `vibevoice` row in `whipgen_health`.
- A2 — `whipgen_vibevoice_tts` (async) returns a `jobId`, reaches `done`, writes
  a valid WAV; `whipgen_job_status` honours session isolation.
- A3 — All 30 `scripts.json` entries synthesize and pass `add_voiceover.py`
  (durations/ducking correct), producing 30 `reels_voiced/` MP4s.
- A4 — `saveTo` outside roots → `save_to_outside_allowed_roots`; service down →
  `vibevoice-unreachable`; oversized script → graceful `vibevoice-oom`.
- A5 — Output retains the audible AI disclaimer + watermark.
- A6 — `whipgen_help topic="whipgen_vibevoice_tts"` returns the documented schema.

---

## 10. Security, safety & responsible AI
- **Preserve protections:** keep Microsoft's audible "AI-generated" disclaimer
  and watermark in all output; do not add a strip/disable flag.
- **Authorization posture:** first-party scripts only (our own marketing copy).
- **Voice cloning gated:** `/voices/register` requires an explicit `consent`
  flag and is off by default (`ALLOW_VOICE_CLONE=0`); **no cloning of real
  individuals without documented consent**; no political/impersonation use.
- **Network:** bind localhost; remote access only via authenticated tunnel; never
  expose the GPU service publicly unauthenticated.
- **Logging/rate limits:** log prompts + caller `sessionId`; per-session caps.

---

## 11. Milestones
- **M0 — Spike (local).** Run VibeVoice 1.5B on the 5090 via the repo CLI;
  confirm `cu128` torch, measure RTF/VRAM, synth 3 reel scripts by hand.
- **M1 — Service.** `vibevoice-svc` (FastAPI) + systemd + `/tts` `/voices`
  `/health`; disclaimer+watermark verified.
- **M2 — MCP integration.** `VibeVoiceDriver` + `whipgen_vibevoice_tts/voices/
  health`; wire `whipgen_health/status/warmup/connect`; `whipgen_help` docs;
  error codes. → satisfies G1–G4.
- **M3 — Extensions.** voice cloning (consent-gated), streaming, ASR captions.
- **M4 — E2E in pipeline.** scripts.json → 30 WAVs → `reels_voiced/` as a
  one-command path; document in `marketing/social/voiceover/README.md`.

---

## 12. Risks & mitigations
| Risk | Mitigation |
|---|---|
| Blackwell/`sm_120` torch build issues | Pin `cu128`/torch ≥ 2.7 (or nightly); document exact wheels in M0 |
| `Large` weights gated/disabled on HF | Default to `1.5B`; treat `Large` as optional; confirm model-card license |
| GPU host ≠ daemon host | Tailscale/SSH tunnel; `vibevoice-unreachable` + `whipgen_connect` recovery |
| VRAM pressure with multiple models | Lazy-load; default single `1.5B`; cap concurrency 1 |
| Misuse of cloning | Consent gate off by default; preserve watermark/disclaimer; usage logs |
| Long scripts → OOM/timeout | `MAX_CHARS`, chunk + stitch, async with generous `max_duration_ms` |
| Service crash mid-job | systemd `Restart=always`; interrupted-job ticket like existing whipgen retries |

---

## 13. Open questions
1. Does the whipgen daemon run on the **same** box as the 5090, or remote
   (tunnel needed)?
2. Current license/availability of `VibeVoice-Large` — ship it, or `1.5B`-only v1?
3. Preferred audio contract: inline base64 vs. always `saveTo` an allowed root
   (large WAVs argue for `saveTo`)?
4. Is ASR-driven **auto-caption** burn-in wanted in v1 (big TikTok win) or M3?
5. Output format/loudness defaults (WAV 24 kHz mono vs. 48 kHz; pre-normalize in
   service or leave to `add_voiceover.py`'s `loudnorm`)?

---

## Appendix A — example `whipgen_vibevoice_tts` call
```json
{
  "tool": "whipgen_vibevoice_tts",
  "input": {
    "name": "reel_00",
    "script": "Speaker 1: What you're watching is cell division, with no biology at all...",
    "speakers": ["Wayne"],
    "model": "1.5b",
    "cfg_scale": 1.4,
    "saveTo": "/abs/allowed-root/voiceover/wav/reel_00.wav",
    "async": true
  }
}
```
## Appendix B — `vibevoice-svc` `/health` (example)
```json
{ "ok": true, "gpu": "NVIDIA GeForce RTX 5090", "driver_cuda": "12.8",
  "vram_total": 32607, "vram_free": 29840, "models_loaded": ["1.5b"],
  "queue_depth": 0 }
```

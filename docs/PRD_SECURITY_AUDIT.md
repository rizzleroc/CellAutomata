# CellAutomata — Security Audit PRD & Remediation Tracker

**Repo:** `rizzleroc/CellAutomata`
**Audit date:** 2026-06-03
**Reviewed commit:** `b260496` (`b2604966dc8fe23d450558ca5fa608afb9c8565d`)
**Branch:** `claude/stoic-goodall-CQG4O`
**Auditor:** Security team — automated **16-subagent** white-box review (17 non-overlapping scopes) + lead triage
**Method:** read-only static analysis; data-flow tracing from every input (file, CLI arg, env var, URL, network) to sensitive sinks; CVE verification via web; call-path reachability confirmation. No code was modified during the audit.
**Tracking epic:** [#44](https://github.com/rizzleroc/CellAutomata/issues/44)

> This document is the canonical, fully-documented record of the audit. Each finding has a stable ID (`SEC-###`), a CWE, a confidence rating, concrete `file:line` evidence, a realistic attack scenario, and a concrete remediation. Critical/High findings are filed as individual GitHub issues for PM management; Medium/Low/Info are tracked in the epic checklist and detailed here.

---

## 0. Executive summary

A 16-agent white-box review covered 100% of the repository — the installable Python package (Tk desktop app + CLI), all four browser clients (`web`, `web2`, `web3`, `web6`), the docs/Pages site, the Railway container, the CI/CD workflows, the dependency set, and the full git history.

### Severity tally

| Severity | Count | IDs |
|---|---|---|
| 🔴 Critical | 1 | SEC-001 |
| 🟠 High | 8 | SEC-002 … SEC-009 |
| 🟡 Medium | 6 | SEC-010 … SEC-015 |
| 🟢 Low | 6 | SEC-016 … SEC-021 |
| ⚪ Info / Governance | 4 | SEC-022 … SEC-025 |
| **Total** | **25** | |

### Headline risks

1. **SEC-001 (Critical) — Pickle RCE via snapshot files.** `Engine.load()` runs `pickle.loads()` on a base64 blob embedded in any `.json` save file. Snapshots are an explicit *save → share → load* feature, reachable from GUI *File ▸ Open*, `--load`, and `cellauto gui --load`. A crafted snapshot = arbitrary code execution on the victim. **This is a release-blocker.**
2. **The snapshot loader trusts its input.** SEC-001, SEC-002 (memory DoS from dimensions/arrays), SEC-003 (VM organism-state OOB), and SEC-012 (no schema/validation/authenticity) all stem from the same root cause: loaded snapshots are treated as trusted data. Fixing the trust boundary resolves four findings at once.
3. **Untrusted-input file/image surfaces.** SEC-004 (arbitrary file write via `--out`/`--save`) and SEC-005 (untrusted image decode via `CELLAUTO_SPRITE_DIR`/`set_sprite_dir`, including decompression bombs) expand the local attack surface, the latter compounded by SEC-007 (Pillow CVE range).
4. **Supply-chain & web hardening.** three.js is pulled from a third-party CDN with no SRI/CSP (SEC-010/011); dependencies are unpinned with no lockfile/hashes and an incomplete CI scan (SEC-007/009/014/015).

### What's clean (verified, not assumed)

- **Secrets:** no credentials, tokens, `.env`, or private keys in the working tree or across **96 commits** of history. `TRIPO_API_KEY` is a documentation reference with no value (SEC-025).
- **Stage XIII VM core:** the digital-organism interpreter has no host-escape surface — no `eval`/`exec`/`getattr`-on-genome, integer-dispatched opcodes, one instruction per organism per step, genome capped. The bugs (SEC-003) are in *loading* untrusted state, not the interpreter.
- **Web client XSS:** web1/web2/web3 have no exploitable DOM XSS — URL-hash params are coerced via `Number()`/whitelist checks and written with `textContent`.

---

## 1. Scope & methodology

### Release surface (what's actually exposed)

| Surface | Where | Reach | Notes |
|---|---|---|---|
| Static docs site | GitHub Pages (auto-deploy from `docs/` on push to `main`) → `web6/` | Public | Canonical lab; loads three.js from CDN |
| Static docs site | Railway container (`Dockerfile` → `python -m http.server` serving `docs/`) | Public | No security headers; runs as root |
| Python package | source / `pip install -e .` (no PyPI release found) | Whoever runs it | Tk GUI + CLI; the RCE/DoS surface |
| Dev tools | `tools/*.py` (excluded from the wheel) | Developers/CI | Lower-trust, dev-machine context |

Version note: `pyproject.toml` declares `4.1.1` while CHANGELOG/commits describe "v5 / Stage XIII" (SEC-024).

### The 17 audit scopes

| # | Scope | Result (C/H/M/L/I) |
|---|---|---|
| 1 | web6 core (`index.html`,`main.js`,`scene.js`,`styles.css`) | 0/0/2/2/1 |
| 2 | web6 apparatus (`apparatus/*.js`) | 0/0/1/0/1 |
| 3 | web6 experiment rules + `atlas.json` | 0/0/1/2/1 |
| 4 | web2 client | 0/0/1/2/2 |
| 5 | web3 client | 0/0/1/1/2 |
| 6 | web (1.0) client | 0/0/1/2/2 |
| 7 | Cross-web headers / CSP / SRI | consolidated → SEC-010/011/018 |
| 8 | engine + persistence (`engine.py`,`grid`,`field`,`channel`) | 1/1/2/1/1 |
| 9 | CLI + app shell (`__main__.py`,`app.py`) | 1/1/2/1/0 |
| 10 | export + image I/O (`export`,`hires`,`sprites`) | 0/2/3/1/1 |
| 11 | renderers + asset loading (`renderer*`,`mascot`,…) | 0/1/2/1/1 |
| 12 | rules + abiogenesis VM (`rules/**`,`life_vm`) | 0/2/3/3/1 |
| 13 | tools scripts (`tools/*.py`) | 0/0/2/3/1 |
| 14 | dependencies & supply chain | 1*/2/3/1/1 |
| 15 | CI/CD GitHub Actions | consolidated → SEC-009/015 |
| 16 | container + secrets sweep | consolidated → SEC-013/020/025 |
| 17 | docs / governance / release posture | consolidated → SEC-022/024 |

\* The dependency scope rated the Pillow `ImageMath.eval` CVE Critical by CVSS; this PRD rates the consolidated dependency finding **High** because that specific code path is not reachable in this codebase (see SEC-007). Per-scope counts overlap; the deduplicated register below is authoritative.

---

## 2. Findings register

| ID | Sev | Title | CWE | Primary location | Issue |
|---|---|---|---|---|---|
| SEC-001 | 🔴 Crit | Pickle RCE in `Engine.load()` | 502 | `engine.py:121` | [#35](https://github.com/rizzleroc/CellAutomata/issues/35) |
| SEC-002 | 🟠 High | Memory-DoS from unvalidated snapshot dims/arrays | 789 | `engine.py:111-118` | [#36](https://github.com/rizzleroc/CellAutomata/issues/36) |
| SEC-003 | 🟠 High | Stage XIII VM organism-state OOB on load | 129 | `stage_life.py:594-629` | [#37](https://github.com/rizzleroc/CellAutomata/issues/37) |
| SEC-004 | 🟠 High | Arbitrary file write via `--out`/`--save` | 22 | `__main__.py:103,123` | [#38](https://github.com/rizzleroc/CellAutomata/issues/38) |
| SEC-005 | 🟠 High | Untrusted image decode via sprite-dir overrides | 434 | `sprites.py:61-65,438` | [#39](https://github.com/rizzleroc/CellAutomata/issues/39) |
| SEC-006 | 🟠 High | Predictable temp-file TOCTOU/symlink write | 377 | `app.py:2565-2575` | [#40](https://github.com/rizzleroc/CellAutomata/issues/40) |
| SEC-007 | 🟠 High | Pillow `>=10.0` admits known CVEs | 1104 | `requirements.txt:1` | [#41](https://github.com/rizzleroc/CellAutomata/issues/41) |
| SEC-008 | 🟠 High | Uncontrolled resource consumption | 400 | `__main__.py:137,157`; `app.py:2304` | [#42](https://github.com/rizzleroc/CellAutomata/issues/42) |
| SEC-009 | 🟠 High | CI `pip-audit` coverage gap | 1104 | `ci.yml:66` | [#43](https://github.com/rizzleroc/CellAutomata/issues/43) |
| SEC-010 | 🟡 Med | three.js CDN without SRI; no CSP | 829 | `web6/index.html:7-13` | #44 |
| SEC-011 | 🟡 Med | No CSP / security headers on web surfaces | 693 | all `index.html`; `Dockerfile` | #44 |
| SEC-012 | 🟡 Med | Incomplete snapshot validation & integrity | 20 | `engine.py:104-118` | #44 |
| SEC-013 | 🟡 Med | Container: http.server as root, unpinned base | 250 | `Dockerfile` | #44 |
| SEC-014 | 🟡 Med | No lockfile/hash pinning; unbounded build backend | 494 | `pyproject.toml:2` | #44 |
| SEC-015 | 🟡 Med | CI: unpinned Actions; no least-privilege token | 1357 | `.github/workflows/*` | #44 |
| SEC-016 | 🟢 Low | CSV formula-injection (latent) | 1236 | `app.py:2186` | #44 |
| SEC-017 | 🟢 Low | Absolute path disclosure in logs/toasts | 209 | `export.py:61` | #44 |
| SEC-018 | 🟢 Low | Google Fonts without SRI (integrity+privacy) | 829 | `web*/index.html` | #44 |
| SEC-019 | 🟢 Low | Latent client-side DOM sinks | 79 | `web6/main.js:292` et al. | #44 |
| SEC-020 | 🟢 Low | Developer path/identity disclosure in tools | 312 | `tools/render_aaa_visuals.py` | #44 |
| SEC-021 | 🟢 Low | Dev-tool script robustness | 73 | `tools/*.py` | #44 |
| SEC-022 | ⚪ Info | No `SECURITY.md`/disclosure policy/threat model | — | repo root | #44 |
| SEC-023 | ⚪ Info | web2/web3 smoke tests excluded from CI gate | 1059 | `pages.yml` | #44 |
| SEC-024 | ⚪ Info | Package version inconsistency | — | `pyproject.toml` | #44 |
| SEC-025 | ⚪ Info | Baseline positives (secrets/VM/XSS clean) | — | — | #44 |

---

## 3. Findings detail

### 🔴 SEC-001 — Arbitrary code execution via `pickle.loads` in `Engine.load()`
- **CWE:** 502 → 94 · **Confidence:** High · **Issue:** #35
- **Location:** `cellauto/engine.py:121` (blob produced at `:90`).
- **Reachable via:** `app.py:2125` (GUI *File ▸ Open*), `__main__.py:55` (`--load`), `__main__.py:81` (`gui --load`).
- **Description:** After `json.loads()` of a snapshot file, if `rng_state` is present the loader runs `pickle.loads(base64.b64decode(data["rng_state"]))` with no integrity/type checks. Pickle executes arbitrary code on deserialization.
- **Attack scenario:** Attacker crafts a snapshot whose `rng_state` is a malicious pickle (`__reduce__` → `os.system`), shares it as a "cool simulation"; victim opens it → RCE with their privileges. No prompt, no sandbox. Also triggers in any pipeline that runs `--load` on a dropped file.
- **Evidence:**
  ```python
  rng_state = pickle.loads(base64.b64decode(data["rng_state"].encode("ascii")))  # engine.py:121
  ```
- **Remediation:** Replace pickle with JSON-native RNG state: persist `random.getstate()` (a `(int, tuple[int,...], float|None)`), restore via `rng.setstate((s[0], tuple(s[1]), s[2]))` after validating shape/types; reject malformed `rng_state`. Never `pickle.loads` file input.

### 🟠 SEC-002 — Memory-exhaustion DoS from unvalidated snapshot dimensions & arrays
- **CWE:** 789 / 400 / 1284 · **Confidence:** High (measured +241 MB for a 1500² grid; scales quadratically) · **Issue:** #36
- **Location:** `engine.py:111-118`; every rule `deserialize_state` (`stage1_grayscott.py:223`, `stage_life.py:595`, `field.py:75`, +10).
- **Description / impact:** `width`/`height` flow straight into the constructor's grid allocation before validation; rule deserializers build numpy arrays from JSON with no size cap and no cross-check against declared dimensions. A tiny file declaring huge dimensions or arrays forces OOM on open; negative/zero/non-int dims raise uncaught exceptions.
- **Remediation:** Validate `width`/`height` (int, `>0`, `<=MAX_DIM`, `width*height<=MAX_CELLS`) before construction and in `__post_init__`; in each `deserialize_state` require shapes to match validated dims and cap element count.

### 🟠 SEC-003 — Stage XIII VM organism-state out-of-bounds / corruption on load
- **CWE:** 129 / 787 / 20 · **Confidence:** High (reproduced via `abiogenesis-pipeline-extended`, stage 12) · **Issue:** #37
- **Location:** `rules/abiogenesis/stage_life.py:594-629` → `life_vm.py:254-349`; spatial write `stage_life.py:621`.
- **Description / impact:** Organism fields (`head`,`regs`,`x`,`y`,`ip`,`genome`,…) are deserialized with no validation. `head=999`/OOB `x,y` → `IndexError` first step (crash). **Negative** values silently index from the end → state corruption / broken determinism. The VM *core* is sandboxed; the flaw is unvalidated loaded state.
- **Remediation:** Clamp/validate every organism field against grid + register bounds in `deserialize_state`; reject failures; mask `head % N_REGISTERS` at use sites.

### 🟠 SEC-004 — Arbitrary file write / path traversal via `--out` / `--save`
- **CWE:** 22 / 73 · **Confidence:** High · **Issue:** #38
- **Location:** `__main__.py:103,123`; `engine.py:98`; `export.py:51`; `hires.py:107,138`. Dev variant `tools/shot.py:85`.
- **Description / impact:** Output paths are unsanitized; `mkdir(parents=True, exist_ok=True)` + write yields an arbitrary-file-write primitive (`../../etc/cron.d/x`, `~/.ssh/authorized_keys`) for any wrapper invoking the CLI with influenced args.
- **Remediation:** `Path(arg).resolve()` confined to an allowed export root; suffix allowlist; same guard across all writers and `engine.save`.

### 🟠 SEC-005 — Untrusted image decode via `CELLAUTO_SPRITE_DIR` / `set_sprite_dir` / `load_sprite`
- **CWE:** 426 / 434 / 400 / 22 · **Confidence:** High · **Issue:** #39
- **Location:** `sprites.py:61-65,438`; `renderer_sem.py:629-633,656,660`.
- **Description / impact:** Sprite root is overridable via env var, an ungated public global, and an unchecked `name` join — all feeding `Image.open().load()` with no `MAX_IMAGE_PIXELS` and swallowed errors. Decompression bombs → OOM; malformed images → Pillow/libtiff/FreeType decoder CVEs (SEC-007); `name="../.."` traversal. Runs every frame.
- **Remediation:** Confine override paths to an allowed base; magic-byte + suffix allowlist; set `Image.MAX_IMAGE_PIXELS`; gate `set_sprite_dir` to tests; canonicalize the sprite path.

### 🟠 SEC-006 — Predictable temp-file TOCTOU / symlink write
- **CWE:** 377 / 59 · **Confidence:** High · **Issue:** #40
- **Location:** `app.py:2565-2575`.
- **Description / impact:** Writes to a fixed `…/cellauto_raf_network.png` in the shared temp dir then reads it back; `Image.save` follows symlinks. On a shared host, a pre-planted symlink redirects the write to a victim file (clobber / potential escalation); the write→read gap is a TOCTOU window.
- **Remediation:** `NamedTemporaryFile`/`mkstemp` with an unguessable private fd; unlink after use.

### 🟠 SEC-007 — Pillow `>=10.0` floor admits known high-severity CVEs
- **CWE:** 1104 / 1395 · **Confidence:** High (CVE ranges web-verified) · **Issue:** #41
- **Location:** `requirements.txt:1`, `pyproject.toml:24`.
- **Description / impact:** The floor permits CVE-2023-50447 (9.0 `ImageMath.eval` ACE; *not reachable* — `ImageMath` unused), CVE-2024-28219 (cms overflow), CVE-2023-4863/5129 (libwebp), CVE-2026-25990 (PSD OOB), CVE-2026-40192 (FITS bomb). The decoder/bomb CVEs **are** reachable via SEC-005.
- **Remediation:** Pin `Pillow>=12.2.0,<13` in both manifests; bump/upper-bound numpy; add hash-pinned lockfile (SEC-014).

### 🟠 SEC-008 — Uncontrolled resource consumption (CLI / GIF / render_size / params)
- **CWE:** 400 / 789 · **Confidence:** High · **Issue:** #42
- **Location:** `__main__.py:137,157,163-165`; `app.py:2304-2306`; `renderer_sem.py:936-950`; `rules/params.py`.
- **Description / impact:** Unbounded `--grid/--steps/--canvas`, an uncapped GIF frame buffer, unbounded `render_size`, and unvalidated `rule_config` (incl. NaN/inf) enable trivial OOM/CPU-hang DoS and simulation poisoning.
- **Remediation:** Range-validate all numeric args; cap `_gif_frames` and auto-stop; clamp `render_size`/`out_size`; reject NaN/inf and clamp params to declared ranges (ties SEC-012).

### 🟠 SEC-009 — CI vulnerability-scanning gap (`pip-audit` scope)
- **CWE:** 1104 · **Confidence:** High · **Issue:** #43
- **Location:** `.github/workflows/ci.yml:66` vs install `:31`.
- **Description / impact:** Only `requirements.txt`'s two deps are audited; dev tools, the build backend, and all transitive deps are unscanned → false "no known vulns" assurance.
- **Remediation:** Audit the installed venv (`pip-audit` with no `-r`, or `-r <(pip freeze)`); add Dependabot + SBOM.

### 🟡 SEC-010 — three.js from jsdelivr CDN without SRI; no CSP
- **CWE:** 829 / 353 · **Confidence:** High · **Tracked:** #44
- **Location:** `docs/web6/index.html:7-13` (importmap), consumed by `main.js:7`, `scene.js:11-17`.
- **Description / impact:** `three@0.162.0` (and the `three/addons/` prefix → arbitrary submodules) load from a third party with no integrity. CDN/DNS/TLS compromise → arbitrary JS in the site origin with full DOM access. Version is pinned and has no known CVE — this is an *integrity/delivery* risk. Importmaps cannot carry SRI, so the fix is structural.
- **Remediation:** Self-host the pinned `three.module.js` + addons under `docs/web6/` and point the importmap at relative paths; add a CSP `script-src`.

### 🟡 SEC-011 — No Content-Security-Policy / security headers on web surfaces
- **CWE:** 693 · **Confidence:** High · **Tracked:** #44
- **Location:** all `docs/**/index.html` (no CSP meta); `Dockerfile` (`http.server` sends none); no `_headers` file.
- **Description / impact:** No CSP, `X-Content-Type-Options`, `Referrer-Policy`, or clickjacking protection — defense-in-depth gap that would otherwise contain SEC-010/019. GitHub Pages can't set headers (use `<meta>` CSP); Railway `http.server` can't either (needs a real server).
- **Remediation:** Add `<meta http-equiv="Content-Security-Policy">` to each page; serve Railway via nginx/caddy with full security headers; consider self-hosting fonts (SEC-018).

### 🟡 SEC-012 — Incomplete snapshot input validation & integrity
- **CWE:** 20 / 501 / 345 / 129 / 1339 · **Confidence:** High · **Tracked:** #44
- **Location:** `engine.py:104-118`; `pipeline.py:472-482`; `stage2_raf.py:218-245`; `params.py`.
- **Description / impact:** Beyond dims (SEC-002), the loader assumes a fixed schema (missing/typed keys → uncaught `KeyError`/`TypeError`), spreads `rule_config` into constructors, never checks `current_stage` (negative wraps to a different stage), trusts RAF reaction indices, accepts NaN/inf params, and verifies no authenticity/integrity of shared files.
- **Remediation:** Validate the envelope (dict, `version`, typed/ranged fields); allow-list `rule_config` keys; bounds-check `current_stage` and reaction indices; reject NaN/inf; treat imported snapshots as untrusted by default.

### 🟡 SEC-013 — Container hardening (http.server as root, unpinned base image)
- **CWE:** 250 / 829 / 16 · **Confidence:** High · **Tracked:** #44
- **Location:** `Dockerfile`.
- **Description / impact:** Production serving uses stdlib `http.server` (no security headers, directory listing, single-threaded DoS) as **root** (no `USER`), on a tag-pinned (not digest-pinned) base image.
- **Remediation:** Switch to nginx/caddy with headers; add a non-root `USER`; pin the base image by digest; keep `.dockerignore` minimal (already excludes `.git`/source — good).

### 🟡 SEC-014 — No lockfile/hash pinning; unbounded build backend; no Dependabot/SBOM
- **CWE:** 494 / 1104 · **Confidence:** High · **Tracked:** #44
- **Location:** `requirements.txt`, `pyproject.toml:2` (`setuptools>=68`, unbounded `wheel`), `.github/` (no `dependabot.yml`).
- **Remediation:** Generate a hash-pinned lock (`pip-compile --generate-hashes` / `uv lock`), install with `--require-hashes` in CI/Docker; bound the build backend; add Dependabot (pip + github-actions) + an SBOM step.

### 🟡 SEC-015 — CI supply-chain hygiene (unpinned Actions; no least-privilege token)
- **CWE:** 1357 / 272 · **Confidence:** High · **Tracked:** #44
- **Location:** `.github/workflows/ci.yml`, `pages.yml`.
- **Description / impact:** Third-party Actions are pinned to mutable tags (`actions/checkout@v4`, `setup-node@v6`, …) not commit SHAs; `ci.yml` sets no top-level `permissions:` (broad default `GITHUB_TOKEN`); `pages.yml` runs an unpinned `npm install three@…`. Triggers are `pull_request` (not `pull_request_target`), which correctly limits injection severity.
- **Remediation:** SHA-pin all Actions; add a minimal top-level `permissions: { contents: read }`; pin/lock the npm install; optionally add `harden-runner` + CodeQL.

### 🟢 SEC-016 — CSV formula-injection (latent) in stats export
- **CWE:** 1236 / 74 · **Confidence:** Low · **Tracked:** #44 · **Location:** `app.py:2186-2190`.
- Current keys/values are hardcoded/int-cast (safe today). Harden: quote any cell beginning with `= + - @` before `writerow` to prevent regression.

### 🟢 SEC-017 — Absolute path disclosure in logs / toasts
- **CWE:** 209 · **Confidence:** Medium · **Tracked:** #44 · **Location:** `export.py:61`; `app.py:1035,2160,2291`.
- Log/show `path.name` or a cwd-relative path instead of the absolute path.

### 🟢 SEC-018 — Google Fonts loaded without SRI (integrity + privacy)
- **CWE:** 829 · **Confidence:** High · **Tracked:** #44 · **Location:** `docs/web/`, `web2/`, `web3/` `index.html:8-10`.
- Self-host the two font families (eliminates the third-party dependency, the integrity gap, and the per-load IP leak to Google).

### 🟢 SEC-019 — Latent client-side DOM sinks
- **CWE:** 79 / 1321 / 20 / 835 · **Confidence:** Med · **Tracked:** #44
- **Location:** `web6/main.js:292` (innerHTML template — currently static data only); `web/presets.js:3` + `sim.js:173` (bare-object preset lookup, proto-pollution-prone); `web6/experiment/rules/life.js:32` (`atlas.json` numeric fields used as modulo divisors, unvalidated); `web6/experiment/rules/natural_selection.js:112` (unbounded `do-while`).
- Not exploitable today (data is static/same-origin) but each becomes a real bug if data ever becomes dynamic. Use `textContent`/DOM construction; `Object.create(null)` + `Object.hasOwn`; clamp `atlas.json` fields; add a finite retry cap.

### 🟢 SEC-020 — Developer path/identity disclosure in tools
- **CWE:** 312 / 540 · **Confidence:** High · **Tracked:** #44 · **Location:** `tools/render_aaa_visuals.py:55-59`, `render_release_poster.py:34-37`.
- Hardcoded `C:/Users/guru8/…/local-agent-mode-sessions/…/<UUID>/…` font paths leak an internal layout and developer username into a public repo. Bundle fonts under `cellauto/assets/fonts/` and use repo-relative paths.

### 🟢 SEC-021 — Dev-tool script robustness
- **CWE:** 73 / 426 / 20 · **Confidence:** Med · **Tracked:** #44 · **Location:** `tools/shot.py:85` (unsanitized output path / unvalidated rule arg), `render_release_poster.py:222` (cwd-relative output), font-path joins without `Path(name).name` guard.
- Dev-machine context (not shipped in the wheel) → low severity. Anchor outputs to `REPO_ROOT`, validate args, strip path components from font names.

### ⚪ SEC-022 — No `SECURITY.md` / disclosure policy / threat model
- **Confidence:** High · **Tracked:** #44. A `SECURITY.md` (private disclosure policy + supported-versions + snapshot-trust warning) is **added in this PR**. Recommend also documenting the snapshot format as a trust boundary in the README and adding a brief threat model.

### ⚪ SEC-023 — web2/web3 client smoke tests excluded from CI deploy gate
- **CWE:** 1059 · **Confidence:** High · **Tracked:** #44 · **Location:** `pages.yml:36-41` runs only `web6/tests/*`. Add `node docs/web2/tests/smoke.mjs` and `node docs/web3/tests/smoke.mjs` to the gate.

### ⚪ SEC-024 — Package version inconsistency
- **Confidence:** High · **Tracked:** #44. `pyproject.toml` says `4.1.1`; CHANGELOG/commits describe "v5 / Stage XIII". Reconcile the version of record (integrity/provenance hygiene; clarifies "what is released").

### ⚪ SEC-025 — Baseline positives (recorded)
- Secrets sweep clean (tree + 96 commits); Stage XIII VM core sandbox sound; web1/2/3 client XSS clean; `Image.eval` lambdas benign. Recorded so future regressions are visible against a known-good baseline.

---

## 4. Remediation roadmap

| Phase | Goal | Findings |
|---|---|---|
| **P0 — block release** | Close the snapshot RCE/DoS trust boundary | SEC-001, SEC-002, SEC-003, SEC-012 |
| **P1 — this cycle** | Local file/image/DoS surfaces + dependency/CI | SEC-004, SEC-005, SEC-006, SEC-007, SEC-008, SEC-009 |
| **P2 — hardening** | Web (CSP/SRI), container, supply chain, CI pinning | SEC-010 … SEC-015 |
| **P3 — cleanup/process** | Low-severity + governance | SEC-016 … SEC-024 |

A single high-value change covers the P0 cluster: **make `Engine.load()` parse a validated, JSON-only schema and never deserialize untrusted binary** (removes pickle, bounds dimensions/arrays, validates organism/rule state).

---

## 5. Tracking & ownership

- **Single source of truth:** epic [#44](https://github.com/rizzleroc/CellAutomata/issues/44). The PM checks items off as linked issues close.
- **Discrete issues:** Critical + High → [#35](https://github.com/rizzleroc/CellAutomata/issues/35)–[#43](https://github.com/rizzleroc/CellAutomata/issues/43).
- **Medium/Low/Info:** tracked as checklist items in #44 and detailed in §3 here; promote to standalone issues when scheduled.
- **Labels:** `security`, `severity:{critical,high}`, plus `vulnerability`/`dependencies`/`ci` as applicable; epic carries `epic`/`tracking`.
- **Definition of done per finding:** code fix + a regression test (e.g. a malicious-snapshot fixture that must be rejected) + epic checkbox ticked.

---

## 6. Appendix — non-findings explicitly verified

- No `eval`/`exec`/`os.system`/`subprocess`/`marshal`/`shelve` on untrusted input anywhere in the package (the only `pickle` is SEC-001; `Image.eval` lambdas are hardcoded arithmetic).
- No committed secrets, `.env`, `.pem`, or keys; `.mcp.json`/`.env`/`snapshots/` are git-ignored.
- No network calls in the Python package (offline by design).
- web1/web2/web3: no `eval`/`new Function`/`document.write`; URL-hash inputs coerced via `Number()`/whitelist and rendered with `textContent`; `localStorage` use is a boolean flag only.
- Stage XIII `life_vm`: integer-dispatched opcodes, one instruction per organism per step, masked registers, capped genome/population — no host escape from an evolved genome.

*End of audit record. Generated 2026-06-03 against commit `b260496`.*

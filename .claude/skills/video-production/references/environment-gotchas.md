# Environment gotchas (Claude Code cloud containers)

- **Python:** `/usr/local/bin/python3` is 3.11; bare `pip` belongs to another interpreter → always `python3 -m pip`.
  Known-good: skia-python 144.0.post2, numpy 2.x, soundfile 0.14, pillow 12, imageio-ffmpeg 0.6, onnxruntime 1.31.
- **skia-python needs libEGL/libGLESv2:** symlink them from the pre-installed Playwright chromium and export
  `LD_LIBRARY_PATH=$B/lib`:
  `ln -sf /opt/pw-browsers/chromium-*/chrome-linux/libEGL.so $B/lib/libEGL.so.1` (same for `libGLESv2.so` → `.so.2`).
  Without it: `ImportError: libEGL.so.1`.
- **ffmpeg:** `python3 -c "import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())"` (static 7.0.2 build).
- **Fonts:** fetched from `https://raw.githubusercontent.com/google/fonts/main/<ofl|apache>/<family>/<File>.ttf`
  (see boxed-episode `engine/setup.sh`).
- **whip MCP daemon is on a Windows host:** `savedTo` paths use backslashes (use `ntpath.basename`), don't pass
  `saveTo`, results spill to `tool-results/` (see audio-elevenlabs.md).
- **The container can reset at any time.** `/tmp` scratchpad, installed packages and `tool-results/` vanish; the
  session transcript `~/.claude/projects/<project>/<session>.jsonl` survives. Recovery: parse it for tool calls and
  results (Write/Edit inputs, heredoc `cat > file <<'EOF'` commands, Read outputs, image blocks for reference frames)
  and replay them. Prevention: keep engines/scripts in a skill folder in the repo and offer to commit.
- **Shell cwd:** `cd` inside a Bash call can change the session's primary working directory — prefer absolute paths or
  subshells `(cd dir && ...)`, and `cd` back to the repo root if it moved.
- **CPU:** 4 cores, 15 GB RAM. Parallel subagents rendering stills + background segment renders compete; run renders
  at `nice 15`, cap workers at 2 while agents are active, 4 when the machine is free.
- **Disk:** a fixed allowance; segments + raw stills add up — delete stills/segments you no longer need.
- **Git:** commit/push only when the user asks; feature branch (never `main`); draft PR after pushing; no model names
  or IDs in commits/PRs/code comments.

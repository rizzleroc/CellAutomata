#!/usr/bin/env python3
"""Harvest ElevenLabs (whip) results that the harness spilled to tool-results/*.txt: decode base64 -> local files,
named after the daemon-side savedTo basename. PCM payloads are wrapped as 16-bit mono WAV (rate from contentType or
--rate). Usage: grab.py <dest_dir> [prefix] [--rate 44100] [--ch 2]   (processed spill files are moved to tool-results/_done)
The spill folder is $WHIP_TR, else the most recently written ~/.claude/projects/*/*/tool-results (this session's)."""
import base64, glob, json, ntpath, os, re, shutil, sys, wave
def _tool_results():
    if os.environ.get("WHIP_TR"):
        return os.environ["WHIP_TR"]
    dirs = glob.glob(os.path.expanduser("~/.claude/projects/*/*/tool-results"))
    if not dirs:
        raise SystemExit("no tool-results folder found; set WHIP_TR=<session folder>/tool-results")
    return max(dirs, key=os.path.getmtime)


TR = _tool_results()
args = [a for i, a in enumerate(sys.argv[1:], 1) if not a.startswith("--") and sys.argv[i - 1] not in ("--rate", "--ch")]
rate = int(sys.argv[sys.argv.index("--rate") + 1]) if "--rate" in sys.argv else 24000
nch = int(sys.argv[sys.argv.index("--ch") + 1]) if "--ch" in sys.argv else 1
dest = args[0]
prefix = args[1] if len(args) > 1 else ""
os.makedirs(dest, exist_ok=True)
done = os.path.join(TR, "_done"); os.makedirs(done, exist_ok=True)
n = 0
for f in sorted(glob.glob(os.path.join(TR, "mcp-whip-whipgen_elevenlabs_*.txt"))):
    try:
        d = json.load(open(f))
    except Exception as e:
        print("skip", os.path.basename(f), e); continue
    if "base64" not in d:
        continue
    base = ntpath.basename(d.get("savedTo", "") or "") or os.path.basename(f)
    if prefix and not base.startswith(prefix):
        continue
    raw = base64.b64decode(d["base64"])
    stem = os.path.splitext(base)[0]
    ct = d.get("contentType", "")
    if raw[:3] == b"ID3" or raw[:2] in (b"\xff\xfb", b"\xff\xf3", b"\xff\xf2") or "mpeg" in ct:
        out = os.path.join(dest, stem + ".mp3"); open(out, "wb").write(raw)
    else:
        m = re.search(r"(\d{4,5})", ct)
        r = int(m.group(1)) if m else rate
        out = os.path.join(dest, stem + ".wav")
        with wave.open(out, "wb") as w:
            w.setnchannels(nch); w.setsampwidth(2); w.setframerate(r); w.writeframes(raw)
    shutil.move(f, os.path.join(done, os.path.basename(f)))
    n += 1
    print(f"{os.path.basename(out):24s} {len(raw):8d} B  {ct}")
print("harvested", n)

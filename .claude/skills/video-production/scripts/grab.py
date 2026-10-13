#!/usr/bin/env python3
"""Harvest ElevenLabs (whip) results that the harness spilled to tool-results/*.txt: decode base64 -> local files,
named after the daemon-side savedTo basename. PCM payloads are wrapped as 16-bit mono WAV (rate from contentType or
--rate). Usage: grab.py <dest_dir> [prefix] [--rate 44100]   (processed spill files are moved to tool-results/_done)"""
import base64, glob, json, ntpath, os, re, shutil, sys, wave
TR = "/root/.claude/projects/-home-user-CellAutomata/8662a024-9ac2-5e4b-966a-7caff567786e/tool-results"
args = [a for a in sys.argv[1:] if not a.startswith("--")]
rate = int(sys.argv[sys.argv.index("--rate") + 1]) if "--rate" in sys.argv else 24000
dest = args[0]
prefix = args[1] if len(args) > 1 and args[1] != str(rate) else ""
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
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(r); w.writeframes(raw)
    shutil.move(f, os.path.join(done, os.path.basename(f)))
    n += 1
    print(f"{os.path.basename(out):24s} {len(raw):8d} B  {ct}")
print("harvested", n)

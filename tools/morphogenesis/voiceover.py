"""VOICEOVER — generate an ElevenLabs narration mp3 for a blend cut.
Needs ELEVENLABS_API_KEY and network egress to api.elevenlabs.io. NOTE: the Claude-on-the-web sandbox
blocks that host (x-deny-reason: host_not_allowed), so run this where ElevenLabs is reachable (your
machine / CI with the domain allow-listed), then feed the mp3 to blend_cut.py via BLEND_CFG.vo, OR upload
the mp3 here and we mux it.

  export ELEVENLABS_API_KEY=sk_...
  python3 tools/morphogenesis/voiceover.py tools/morphogenesis/vo_script.json /tmp/vo.mp3 [voice_id]
Emits the combined mp3 and (with --per-line) one mp3 per line for tight caption sync."""
import os, sys, json, requests

API = "https://api.elevenlabs.io/v1/text-to-speech"
KEY = os.environ.get("ELEVENLABS_API_KEY", "")
DEFAULT_VOICE = os.environ.get("ELEVENLABS_VOICE_ID", "JBFqnCBsd6RMkjVDRZzb")  # warm narrator; override per project
MODEL = os.environ.get("ELEVENLABS_MODEL", "eleven_multilingual_v2")

DEFAULT_SETTINGS = {"stability": 0.5, "similarity_boost": 0.85, "style": 0.4, "use_speaker_boost": True}

def tts(text, voice, out, model=MODEL, settings=None):
    if not KEY:
        raise SystemExit("set ELEVENLABS_API_KEY")
    r = requests.post(f"{API}/{voice}", headers={"xi-api-key": KEY, "accept": "audio/mpeg",
        "content-type": "application/json"},
        json={"text": text, "model_id": model, "voice_settings": settings or DEFAULT_SETTINGS}, timeout=60)
    if r.status_code != 200:
        raise SystemExit(f"ElevenLabs {r.status_code}: {r.text[:300]}")
    open(out, "wb").write(r.content)
    print(f"-> {out}  {len(r.content)/1024:.0f} KB")

def main():
    script = json.load(open(sys.argv[1] if len(sys.argv) > 1 else "tools/morphogenesis/vo_script.json"))
    out = sys.argv[2] if len(sys.argv) > 2 else "/tmp/vo.mp3"
    voice = sys.argv[3] if len(sys.argv) > 3 and not sys.argv[3].startswith("--") else script.get("voice_id", DEFAULT_VOICE)
    model = script.get("model", MODEL); settings = script.get("voice_settings")
    lines = script["lines"]
    if "--per-line" in sys.argv:
        for i, ln in enumerate(lines):
            tts(ln, voice, out.replace(".mp3", f"_{i:02d}.mp3"), model, settings)
    else:
        tts(script.get("join", " … ").join(lines), voice, out, model, settings)   # combined narration

if __name__ == "__main__":
    main()

"""Render the swarm's viral cuts to delivered web MP4s.
Reads the leaderboard (/tmp/lb/*.json — each {"score":N,"cfg":{...VCUT_CFG...}}), picks the highest-scoring
cut per specimen (tag), renders each via viral_cut.py (config passed through the environment, so captions with
apostrophes are safe), and trims each to a <25 MB web cut (the raw grainy masters are huge).
  python3 tools/morphogenesis/run_viral.py            # best cut per specimen
  python3 tools/morphogenesis/run_viral.py 8          # top 8 by score
  python3 tools/morphogenesis/run_viral.py vg_luca2 vg_coac1 ...   # explicit ids
Output: /tmp/viral_<id>_web.mp4 (delivered)."""
import json, os, glob, subprocess, sys
import imageio_ffmpeg
FF = imageio_ffmpeg.get_ffmpeg_exe()
ROOT = os.path.dirname(os.path.abspath(__file__))
LB = sorted(glob.glob('/tmp/lb/*.json'))
entries = [json.load(open(p)) for p in LB]
args = sys.argv[1:]
explicit = [a for a in args if not a.isdigit()]
limit = next((int(a) for a in args if a.isdigit()), None)
if explicit:
    picks = [d for d in entries if d['cfg']['id'] in explicit]
else:
    best = {}
    for d in entries:
        t = d['cfg']['tag']
        if t not in best or d['score'] > best[t]['score']: best[t] = d
    picks = sorted(best.values(), key=lambda d: -d['score'])
    if limit: picks = picks[:limit]
print(f"rendering {len(picks)} viral cuts:", [f"{d['cfg']['id']}({d['score']})" for d in picks])
done = []
for d in picks:
    cfg = d['cfg']; idd = cfg['id']
    env = dict(os.environ); env['VCUT_CFG'] = json.dumps(cfg)
    subprocess.run(['python3', f'{ROOT}/viral_cut.py', 'render'], env=env, check=True)
    src = f"/tmp/viral_{idd}.mp4"; out = f"/tmp/viral_{idd}_web.mp4"
    # temporal denoise crushes the per-frame grain the encoder chokes on; a maxrate ceiling guarantees <25 MB
    # even for the bright/busy specimens (grayscott, minerals, soup) whose grain blows past a plain crf.
    subprocess.run([FF, '-y', '-hide_banner', '-loglevel', 'error', '-i', src, '-vf', 'hqdn3d=4:3:5:5',
                    '-c:v', 'libx264', '-crf', '23', '-maxrate', '9000k', '-bufsize', '18000k', '-preset', 'medium',
                    '-c:a', 'aac', '-b:a', '128k', '-movflags', '+faststart', out], check=True)
    mb = os.path.getsize(out) / 1e6; done.append((out, mb)); print(f"-> {out}  {mb:.1f} MB")
print("\n=== DONE ===")
for out, mb in done: print(f"{mb:6.1f} MB  {out}")

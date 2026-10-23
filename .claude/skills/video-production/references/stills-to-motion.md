# Animating a still (album covers, posters)

Worked example: "FREE ED SHEERAN" animated cover — 60 s, 1080×1920, 24 fps, delivered at 26.98 MiB
(`examples/cover/prep.py`, `examples/cover/anim.py`; the original audio script depended on lost synth modules).

## 1. Clean, big source
- Photographed/cropped art: find the corners, perspective-rectify to a square (`cv2`-free: solve the homography with
  numpy, resample with skia or PIL).
- Upscale 4× with Real-ESRGAN **without torch**: `scripts/upscale.py in.png out.png` parses the `.pth` zip with a
  minimal unpickler, rebuilds SRVGGNetCompact as an ONNX graph and runs it tiled in onnxruntime. Model:
  `curl -L -o models/realesr-general-x4v3.pth https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesr-general-x4v3.pth`
  (or set `REALESRGAN_PTH`).

## 2. Layer stack (2.5D multiplane)
- Author polygons for each element on a small preview grid (e.g. 720 px) and scale up (×4); cut RGBA layers
  (title, figures, props, foreground), inpaint/extend the background behind them (`prep.py` → `layers/*.png`,
  `bg.png`).

## 3. Motion design (`anim.py` pattern)
- Acts with a clear arc: an object reveal (a real 3D jewel case with front art + spine, turning in a spotlight), a
  push through into the art, per-layer parallax + procedural motion (sway, pumps, drips, shimmer, flags, sparks),
  a climax event (crack → shatter) on the musical beat, pull back out, fade.
- Everything keyed to a beat grid (BPM + downbeat) shared with the audio script.
- `--stills t1 t2 ...` for QC, 4 workers for the full render.

## 4. Audio + delivery
- Original music only (never imitate a real artist): build the bed and hits on the same beat grid; two-pass linear
  loudness to −14 LUFS (`scripts/loud.sh`).
- One file < 30 MiB (re-encode at a computed bitrate if the first pass is over).

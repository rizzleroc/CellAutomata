#!/usr/bin/env python3
"""Tile stills into 2x2 contact sheets: sheet.py <dir> <out_prefix> [files...] (default: all still_*.png sorted)."""
import sys, os, glob
from PIL import Image, ImageDraw
d, pre = sys.argv[1], sys.argv[2]
files = sys.argv[3:] or sorted(glob.glob(os.path.join(d, "still_*.png")))
for i in range(0, len(files), 4):
    sheet = Image.new("RGB", (1920, 1080))
    for j, f in enumerate(files[i:i + 4]):
        im = Image.open(f).resize((960, 540))
        dr = ImageDraw.Draw(im)
        dr.rectangle((0, 0, 110, 22), fill=(0, 0, 0)); dr.text((4, 4), os.path.basename(f)[6:-4], fill=(255, 255, 0))
        sheet.paste(im, ((j % 2) * 960, (j // 2) * 540))
    sheet.save(f"{pre}_{i // 4:02d}.png")
    print(f"{pre}_{i // 4:02d}.png")

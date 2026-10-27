#!/usr/bin/env python3
"""Convert evidence PNGs to JPEG (default quality 82) for embedding in a PDF.
Usage: python3 compress_images.py evidence/ evidence_jpg/ [quality]
A 40-page report with 25 full-size PNGs is tens of MB; JPEG q82 keeps highlighted text legible."""
import os, sys
from PIL import Image
src, dst = sys.argv[1], sys.argv[2]
q = int(sys.argv[3]) if len(sys.argv) > 3 else 82
os.makedirs(dst, exist_ok=True)
for f in sorted(os.listdir(src)):
    if f.lower().endswith(".png"):
        Image.open(os.path.join(src, f)).convert("RGB").save(os.path.join(dst, f[:-4] + ".jpg"), quality=q, optimize=True)
        print(f)

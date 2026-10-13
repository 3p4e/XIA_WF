#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AI-Art face — post-processing + preview (Task 2 scope).

Takes raw AI-generated backgrounds (1024x1024 RGB) and produces watch-safe
sprites: center-crop 464x464, circular dial mask, adaptive <=256-color
quantization (firmware decoder limit). Renders review previews with the widget
zones marked so the human can approve art before full face authoring (Task 4).

Usage:
  python3 gen_assets.py              # process all raw/*.png
  python3 gen_assets.py <file.png>   # process one input
"""
import os, sys
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(ROOT, "raw")
OUT = os.path.join(ROOT, "processed")
PREV = os.path.join(ROOT, "previews")
os.makedirs(OUT, exist_ok=True)
os.makedirs(PREV, exist_ok=True)

W = H = 464
CENTER = 232
MAX_COLORS = 256


def load_background(path):
    im = Image.open(path).convert("RGB")
    # center crop to square, then resize to 464x464
    side = min(im.size)
    left = (im.width - side) // 2
    top = (im.height - side) // 2
    im = im.crop((left, top, left + side, top + side)).resize((W, H), Image.LANCZOS)
    return im


def circular_mask(im, feather=2):
    """Circular dial mask with soft edge on an RGBA canvas."""
    base = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    mask = Image.new("L", (W * 4, H * 4), 0)
    d = ImageDraw.Draw(mask)
    d.ellipse([0, 0, W * 4 - 1, H * 4 - 1], fill=255)
    if feather:
        d.ellipse(
            [feather * 4, feather * 4, W * 4 - 1 - feather * 4, H * 4 - 1 - feather * 4],
            fill=255,
        )
    mask = mask.resize((W, H), Image.LANCZOS)
    base.paste(im.convert("RGBA"), (0, 0), mask)
    return base


def quantize_under_limit(im, max_colors=MAX_COLORS):
    """Adaptive quantization, returns an RGBA image guaranteed <= max_colors.

    Quantizes in RGBA space (not RGB) so transparency and the circular dial mask
    survive; the packer's index-256 path requires <= max_colors per image.
    """
    rgba = im.convert("RGBA")
    samples = rgba.getcolors(maxcolors=2 << 20)
    n = 2 << 20 if samples is None else len(samples)
    if n <= max_colors:
        return rgba
    q = rgba.quantize(colors=max_colors)
    return q.convert("RGBA")


def process(name):
    src = os.path.join(RAW, name)
    im = load_background(src)
    masked = circular_mask(im)
    out = quantize_under_limit(masked)
    dest = os.path.join(OUT, name)
    out.save(dest)
    n_colors = len(out.resize((W, H)).getcolors(maxcolors=2 << 20) or [])
    print(f"{name}: {out.size} {out.mode} colors={n_colors} -> {dest}")
    return dest


def render_preview(name, processed_path):
    """Compose a review preview with widget zones marked."""
    bg = Image.open(processed_path).convert("RGBA")
    im = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    im.alpha_composite(bg, (0, 0))
    d = ImageDraw.Draw(im)
    F = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 26)

    # mark widget zones (to be finalized in Task 4)
    zones = [
        ("time", (232, 232), 160),
        ("date", (232, 54), 0),
        ("health", (232, 396), 0),
    ]
    for label, (cx, cy), r in zones:
        color = (255, 255, 255, 200)
        if r:
            d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color, width=2)
        else:
            d.rectangle([cx - 100, cy - 20, cx + 100, cy + 20], outline=color, width=2)
        # small centered label
        if label == "time":
            txt = "22:14"
            tw = F.getlength(txt)
            d.text((cx - tw / 2, cy - 16), txt, font=F, fill=(255, 255, 255, 220))
        elif label == "date":
            txt = "TUE 10 . 13"
            tw = F.getlength(txt)
            d.text((cx - tw / 2, cy - 14), txt, font=F, fill=(255, 255, 255, 220))
        else:
            txt = "100%  72  24"
            tw = F.getlength(txt)
            d.text((cx - tw / 2, cy - 18), txt, font=F, fill=(255, 255, 255, 220))
    out = os.path.join(PREV, name)
    im.convert("RGB").save(out)
    print(f"preview -> {out}")


def main():
    args = sys.argv[1:]
    if args:
        names = [os.path.basename(a) for a in args]
    else:
        names = sorted(f for f in os.listdir(RAW) if f.lower().endswith(".png"))
    for name in names:
        if not os.path.exists(os.path.join(RAW, name)):
            print(f"skip (missing raw): {name}")
            continue
        dest = process(name)
        render_preview(name, dest)


if __name__ == "__main__":
    main()

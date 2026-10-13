#!/usr/bin/env python3
"""Generate 3 AI art concepts via Google Gemini image model.
Usage: GEMINI_API_KEY=... python3 gen_concepts.py
Saves project/ai-art/raw/<slug>.png
"""
import base64, json, os, pathlib, urllib.request

KEY = os.environ["GEMINI_API_KEY"]
MODEL = "gemini-2.5-flash-image"
OUT = pathlib.Path(__file__).resolve().parent / "raw"
OUT.mkdir(parents=True, exist_ok=True)

CONCEPTS = [
    ("photoreal_ocean", "Photorealistic top-down aerial view of a serene turquoise ocean with a tiny lush island at the center, gentle concentric ripples, soft natural daylight, circular composition, luxury smartwatch dial background, ultra detailed, no text, no numbers, no hands"),
    ("minimal_abstract", "Minimal abstract circular design, deep navy to black gradient, a single fine brushed-gold geometric arc and subtle radial texture, premium elegant luxury smartwatch dial background, generous negative space, no text, no numbers, no hands"),
    ("cyberpunk", "Illustrated cyberpunk city looking upward at towering neon skyscrapers, purple and cyan glow, rain reflections, dramatic one-point perspective, stylized digital art, circular composition, premium smartwatch dial background, no text, no numbers, no hands"),
]

url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={KEY}"
for slug, prompt in CONCEPTS:
    body = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as r:
        data = json.load(r)
    parts = data["candidates"][0]["content"]["parts"]
    inline = next(p["inlineData"] for p in parts if isinstance(p.get("inlineData"), dict))
    raw = base64.b64decode(inline["data"])
    dest = OUT / f"{slug}.png"
    dest.write_bytes(raw)
    print(f"WROTE {dest} ({len(raw)} bytes, {inline.get('mimeType')})")

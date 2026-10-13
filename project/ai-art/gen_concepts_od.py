#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate 3 AI art concepts NATIVELY through Open Design (Google Nano Banana).

Requires env: OD_BASE_URL, OD_API_TOKEN, OD_PROJECT_ID
Optional env: OD_IMAGE_MODEL (default gemini-3.1-flash-image-preview)

Writes project/ai-art/raw/<slug>.png (normalized to PNG for the asset pipeline).
Prompts are deliberately distinct from the first-generation set so results differ.
"""
import os, io, json, time, base64, pathlib, urllib.request, urllib.error, urllib.parse
from PIL import Image

BASE = os.environ["OD_BASE_URL"].rstrip("/")
TOKEN = os.environ["OD_API_TOKEN"]
PROJ = os.environ["OD_PROJECT_ID"]
MODEL = os.environ.get("OD_IMAGE_MODEL", "gemini-3.1-flash-image-preview")
OUT = pathlib.Path(__file__).resolve().parent / "raw"
OUT.mkdir(parents=True, exist_ok=True)

AUTH = "Basic " + base64.b64encode(f"open-design:{TOKEN}".encode()).decode()

CONCEPTS = [
    ("photoreal_ocean",
     "Photorealistic aerial drone view of a dramatic deep-blue ocean, white foam waves "
     "curling around a small black volcanic island at the centre, moody overcast light, "
     "rich water texture, circular composition, luxury smartwatch dial background, "
     "ultra detailed, no text, no numbers, no hands"),
    ("minimal_abstract",
     "Minimal abstract circular design, charcoal black base with a soft teal-to-violet "
     "aurora glow, thin concentric rings and one subtle radial highlight, matte premium "
     "finish, generous negative space, luxury smartwatch dial background, no text, "
     "no numbers, no hands"),
    ("cyberpunk",
     "Neon cyberpunk street at night seen in the rain, glowing magenta and electric-blue "
     "signage bokeh, wet reflective pavement, cinematic shallow depth of field, stylized "
     "digital art, circular composition, premium smartwatch dial background, no text, "
     "no numbers, no hands"),
]


def _req(method, path, body=None, timeout=180):
    url = BASE + path
    headers = {"Authorization": AUTH, "Origin": BASE}
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    r = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r, timeout=timeout) as resp:
            return resp.read()
    except urllib.error.HTTPError as e:
        raise SystemExit(f"{method} {path} -> HTTP {e.code}: {e.read()[:400]!r}")


def _json(method, path, body=None, timeout=180):
    return json.loads(_req(method, path, body, timeout))


def newest_image(since):
    files = _json("GET", f"/api/projects/{PROJ}/files")["files"]
    imgs = [f for f in files if f.get("kind") == "image" and f.get("mtime", 0) >= since]
    if not imgs:
        raise SystemExit("no produced image found")
    return max(imgs, key=lambda f: f["mtime"])


def generate(slug, prompt):
    out_name = f"gen_{slug}.png"
    start = time.time() * 1000 - 2000
    resp = _json("POST", f"/api/projects/{PROJ}/media/generate",
                 {"surface": "image", "model": MODEL, "prompt": prompt, "output": out_name})
    task = resp.get("taskId")
    if not task:
        raise SystemExit(f"no taskId: {resp}")
    status = "running"
    for _ in range(90):
        st = _json("POST", f"/api/media/tasks/{task}/wait", {"timeoutMs": 25000})
        status = st.get("status")
        if status == "done":
            break
        if status in ("failed", "interrupted"):
            raise SystemExit(f"{slug}: task {status}: {json.dumps(st.get('error'))[:400]}")
        time.sleep(2)
    if status != "done":
        raise SystemExit(f"{slug}: task did not finish ({status})")
    f = newest_image(start)
    raw = _req("GET", f"/api/projects/{PROJ}/raw/{urllib.parse.quote(f['name'])}", timeout=120)
    im = Image.open(io.BytesIO(raw)).convert("RGB")
    dest = OUT / f"{slug}.png"
    im.save(dest)
    print(f"WROTE {dest} ({im.size}, {len(raw)} raw bytes from {f['name']})")


for slug, prompt in CONCEPTS:
    generate(slug, prompt)

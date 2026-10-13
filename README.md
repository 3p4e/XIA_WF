# XIA_WF — Custom Watch Faces for Xiaomi Watch S3

Original watch-face designs for the **Xiaomi Watch S3** (model `M2313W1`), built with a
fully **Linux-native toolchain** (no Windows required).

| | |
|---|---|
| Panel | 466×466 AMOLED · logical canvas **464×464** · center (232,232) |
| Format | reverse-engineered `ws3` binary (see `docs/BUILDING.md`) |
| Texture budget | ≲ 4 MB per face, ≤ 256 colors per image |
| License | Source under **MIT**; compiled `.bin` + artwork are original works (see `vendor/NOTICE`) |

---

## Faces

### `Mono`

A minimal monochrome digital dial.

- Date row: `MM · DD · DDD` (prerendered frames)
- Large `HH:MM` time with a **1 Hz blinking colon**
- Bottom row: battery % · heart rate · temperature
- **AOD face** (dimmer, no blinking colon, saves power)

Previews:

- Normal: `project/mono/preview.png`
- AOD: `project/mono/preview_aod.png`

Compiled binary: `deliverables/Mono.bin`

### `AiArt-*` — AI-artwork dials

Three faces built on AI-generated full-bleed dial artwork, each with an AOD variant.
Same proven widget set as `Mono` (date · HH:MM blink · steps · HR · calories · battery),
composited over a processed AI-art background.

| Face | Art direction | Binary |
|---|---|---|
| `AiArt-photoreal_ocean` | aerial deep-blue ocean, volcanic island | `deliverables/AiArt-photoreal_ocean.bin` |
| `AiArt-minimal_abstract` | charcoal + teal/violet aurora rings | `deliverables/AiArt-minimal_abstract.bin` |
| `AiArt-cyberpunk` | rainy neon street, magenta/blue bokeh | `deliverables/AiArt-cyberpunk.bin` |

Generation pipeline (Open Design in the loop): the 3 backgrounds are generated
**natively through the self-hosted Open Design instance** by
`project/ai-art/gen_concepts_od.py` (surface `image`, model
`gemini-3.1-flash-image-preview` via the `nanobanana` provider), which calls
Open Design's `POST /api/projects/<id>/media/generate`, waits on
`POST /api/media/tasks/<id>/wait`, and downloads the result from
`/api/projects/<id>/raw/<file>` into `project/ai-art/raw/`.
`project/ai-art/gen_assets.py` then post-processes each raw image
(crop 464×464, circular mask, **≤256 colors**) into `project/ai-art/processed/`,
and `project/ai-art/gen_face.py` composes the watch-safe sprites + `wfDef.json`.

Legacy direct-API generator (kept for reference): `project/ai-art/gen_concepts.py`.
Previews: `project/ai-art/<face>/preview.png` and `preview_aod.png`.

---

## Build (Linux / macOS)

Prerequisites: **JDK 21+** (`java`/`javac`), **Python 3** + Pillow.

```bash
# 1. generate artwork + wfDef.json
python3 project/mono/gen_assets.py

# 2. compile the packer (once)
bash vendor/Mi8WfBinTool/build.sh

# 3. pack the face into a .bin
java -cp vendor/Mi8WfBinTool Mi8WfBinTool pack project/mono build/Mono.bin ws3

# 4. patch the header (smooth-sweep switch, reserved flag, styleCount)
python3 vendor/scripts/patch_header.py build/Mono.bin 1 4 1

# 5. verify by round-tripping
java -cp vendor/Mi8WfBinTool Mi8WfBinTool unpack build/Mono.bin /tmp/mono_check ws3
```

> `build/` and `*.class` are gitignored; the committed deliverable lives in `deliverables/`.

---

## Install on the watch

1. Install the **modified MiFitness APK** (Android only) from the `mi_watch_int`
   Telegram channel.
2. Open the online watch-faces list and import `deliverables/Mono.bin`
   (Mi Fitness → Watch faces → Custom → Import).
3. **On-device check is the only acceptance test** — verify time, date, blink,
   bottom-row widgets, and the AOD transition.

---

## Project layout

```
project/mono/          Mono face: gen_assets.py + wfDef.json + images/ + images_aod/
vendor/Mi8WfBinTool/   Java ws3 packer (MIT, vendored — see NOTICE)
vendor/scripts/        patch_header.py (MIT, vendored)
deliverables/          compiled .bin watch faces
docs/                 format + build documentation
```

---

## Credits & legality

The `ws3` binary-format knowledge (data-source ids, `prop7Raw` templates, header
layout, smooth-sweep/AOD requirements) is **reverse-engineered fact** originating
from the MIT-licensed project **[thecoolboyhan/xiaomi-watch-s3-diy](https://github.com/thecoolboyhan/xiaomi-watch-s3-diy)**,
which itself builds on **ooflet/Mi-Create** (MIT). The vendored toolchain is included
with attribution and full license text (`vendor/NOTICE`, `LICENSE`).

The watch-face **design, layout, and artwork** in this repository are original.
Compiled `.bin` files and embedded artwork are **not** covered by the MIT license —
personal use only; do not redistribute commercially. Xiaomi firmware/trademarks are
out of scope.

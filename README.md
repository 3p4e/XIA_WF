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

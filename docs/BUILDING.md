# Building XIA_WF watch faces

This document explains the `ws3` build pipeline used in this repository. It summarizes the
reverse-engineered format facts required to produce a working Xiaomi Watch S3 watch face.

The authoritative, byte-level format reference is the upstream
[xiaomi-watch-s3-diy `FORMAT.md`](https://github.com/thecoolboyhan/xiaomi-watch-s3-diy/blob/main/docs/FORMAT.md).
Everything below is consistent with it.

---

## Device and canvas

| Item | Value |
|---|---|
| Panel | 466×466 AMOLED |
| Logical canvas | **464×464** (all images must fit) |
| Center | (232, 232) |
| Texture budget | ≲ 4 MB per face |
| Color limit | ≤ 256 colors per image |

---

## Build order (mandatory)

```
1. edit wfDef.json / assets
2. pack  (Java Mi8WfBinTool)
3. patch_header  1 4 1   (smooth = 1, styleCount = 4, flag16 = 1)
4. unpack & verify
5. install on watch
```

The packer never writes the smooth-sweep switch (`byte[6]`) or reserved flag (`0x16`).
**Always** run `patch_header.py` after `pack`.

---

## Project format (wfDef.json)

A watch face is a JSON project plus PNG assets. Key fields:

- `name`, `id`, `previewImg` (defaults to `preview`)
- `faceStyleCount` — number of styles (use 4)
- `elementsNormal` — main face element list
- `elementsAod` — always-on-display face element list (optional)
- `namedFaceRecords` + `faceNames` — named-face layout (`true` for AOD dials)

Element types used in this repo:

| type | purpose |
|---|---|
| `element` | static image (`image` name) at `x`,`y` |
| `widge_dignum` | digital number rendered from `imageList` sprites (`dataSrc` controls what) |
| `widge_imagelist` | frame-based value (date, weekday, blink colon, weather) |

---

## `dataSrc` quick reference (Gregorian)

| id | meaning |
|---|---|
| `081102` | hour (2 digits) |
| `101102` | minute (2 digits) |
| `1811` | second (frame list, used for blink colon) |
| `1012` | month |
| `1812` | day |
| `2012` | weekday |
| `084103` | battery % (3 digits) |
| `082202` | heart rate |
| `203103` | temperature ℃ |
| `082105` | steps (5 digits) |

---

## `prop7Raw` — the critical channel data

Every `widge_dignum` / `widge_imagelist` element carries a `prop7Raw` hex string that
encodes per-widget refresh timing and frame tables. **Getting these wrong breaks live
rendering** (e.g. second hand ticks at 1 Hz instead of sweeping, or progress arcs die).

This repository reuses the device-verified canonical values from the upstream project:

- `dignum` refresh = `E8 03` (1000 ms) at bytes b6–b7
- `imagelist` with an index table must set bytes b12–b13 = `00 02`

**Never re-pack from an `unpack`-ed wfDef** — the unpacker strips `prop7Raw`.
Always keep the raw values in `project/*/wfDef.json`.

See `project/mono/gen_assets.py` for the exact templates.

---

## Asset constraints

- Image must fit 464×464; use cropped tiles for small sprites (never full-canvas frames for
  lists — this blows the texture budget).
- ≤ 256 colors per image.
- Transparent PNGs for sprites; the background `image_0000` draws the dial face.
- AOD assets live in `images_aod/`; the packer falls back to `images/` if absent.

---

## Verification

After packing and patching, sanity-check the header:

```python
import struct
b = open('build/Mono.bin','rb').read()
assert b[0:4].hex().upper() == '5AA53412'   # magic
assert b[6] == 1                              # smooth-sweep switch
assert b[0x16] == 1                            # reserved flag
assert struct.unpack_from('<H', b, 0x1C)[0] == 2   # faceCount (AOD dials)
# face records (named-face layout): main @0xA8, AOD @0x148
assert hex(struct.unpack_from('<I', b, 0xA8)[0]) == '0x80000000'
assert hex(struct.unpack_from('<I', b, 0x148)[0]) == '0x80000000'
```

**On-device check is the only acceptance test** — always install and verify on a real watch.

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AI-Art face — authoring (Slice 1, digital widget set over AI artwork).

Reuses the device-verified widget set from the Mono face (date row, HH:MM with
1 Hz blinking colon, health row) and composites it over a processed AI-art
dial background. Format knowledge (dataSrc ids, prop7Raw templates, build
order, max 256 colors/image) is reverse-engineered fact from the MIT-licensed
xiaomi-watch-s3-diy project. Artwork here is original.

Usage:
  python3 gen_face.py                 # build all concepts in processed/
  python3 gen_face.py minimal_abstract
"""
import os, sys, json
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.abspath(__file__))
PROCESSED = os.path.join(ROOT, "processed")
W = H = 464
CENTER = 232
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

# ---------------- palette (art: light ink over art, with dark stroke) ----------------
PAL = dict(ink=(245, 245, 248, 255), dim=(220, 222, 228, 255),
           stroke=(0, 0, 0, 200), ring=(255, 255, 255, 90),
           batt=(150, 240, 170, 255), heart=(255, 110, 110, 255),
           steps=(255, 210, 120, 255), kcal=(255, 150, 90, 255))
PAL_AOD = dict(ink=(150, 150, 156, 255), dim=(110, 110, 116, 255),
               stroke=(0, 0, 0, 0), ring=(60, 60, 64, 255),
               batt=(90, 150, 105, 255), heart=(150, 70, 70, 255),
               steps=(150, 120, 70, 255), kcal=(150, 95, 60, 255))


def load_font(size):
    return ImageFont.truetype(FONT, size)


def text_image(s, font, color, stroke=None, sw=0):
    tmp = Image.new("RGBA", (font.size * (len(s) + 3), int(font.size * 2.0)), (0, 0, 0, 0))
    kw = {}
    if stroke is not None and sw:
        kw["stroke_width"] = sw
        kw["stroke_fill"] = stroke
    ImageDraw.Draw(tmp).text((tmp.width // 2, tmp.height // 2), s, font=font, fill=color, anchor="mm", **kw)
    return tmp.crop(tmp.getbbox())


def ink_size(s, font):
    return text_image(s, font, (255, 255, 255, 255)).size


def glyph(s, font, color, cell, stroke=None, sw=0):
    im = text_image(s, font, color, stroke, sw)
    out = Image.new("RGBA", cell, (0, 0, 0, 0))
    out.alpha_composite(im, ((cell[0] - im.width) // 2, (cell[1] - im.height) // 2))
    return out


# ---------------- layout ----------------
DATE_SIZE = 34
F_DATE = load_font(DATE_SIZE)
MONTHS = [f"{m:02d}" for m in range(1, 13)]
DAYS = [f"{d:02d}" for d in range(1, 32)]
WEEK = ["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"]
M_CELL = (max(ink_size(t, F_DATE)[0] for t in MONTHS) + 8, DATE_SIZE + 12)
D_CELL = (max(ink_size(t, F_DATE)[0] for t in DAYS) + 8, DATE_SIZE + 12)
W_CELL = (max(ink_size(t, F_DATE)[0] for t in WEEK) + 10, DATE_SIZE + 12)
DOT_CELL = (18, DATE_SIZE + 12)
GAP = 8
DATE_TOTAL = M_CELL[0] + DOT_CELL[0] + D_CELL[0] + DOT_CELL[0] + W_CELL[0] + 4 * GAP
Y_DATE = 44
x = CENTER - DATE_TOTAL // 2
MONTH_X = x
DOT1_X = MONTH_X + M_CELL[0] + GAP
DAY_X = DOT1_X + DOT_CELL[0] + GAP
DOT2_X = DAY_X + D_CELL[0] + GAP
WK_X = DOT2_X + DOT_CELL[0] + GAP

TIME_SIZE = 128
F_TIME = load_font(TIME_SIZE)
TIME_INK = ink_size("0", F_TIME)[1]
T_CELL = (max(ink_size(str(d), F_TIME)[0] for d in range(10)) + 8, TIME_INK + 10)
COLON_W = 20
COLON_GAP = 10
TIME_BLOCK = 4 * T_CELL[0] + COLON_GAP
TIME_LEFT = CENTER - TIME_BLOCK // 2
Y_TIME = 140
HOUR_CX = TIME_LEFT + T_CELL[0]
COLON_X = TIME_LEFT + 2 * T_CELL[0]
MIN_CX = TIME_LEFT + 3 * T_CELL[0] + COLON_GAP
DIV_Y = Y_TIME + T_CELL[1] + 18

# health row: steps / heart / calories / battery (single row, 4 columns)
H_SIZE = 30
F_H = load_font(H_SIZE)
H_CELL = (max(ink_size(str(d), F_H)[0] for d in range(10)) + 4, H_SIZE + 8)
ICON = 32
HCOL = [70, 178, 286, 394]
Y_ICON_CY = 398
Y_NUM = 414


def ic_heart(color, w=ICON, h=ICON):
    ss = 4
    im = Image.new("RGBA", (w * ss, h * ss), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    W_, H_ = w * ss, h * ss
    r = W_ * 0.27
    cy = H_ * 0.42
    d.ellipse([W_ * 0.06, cy - r, W_ * 0.06 + 2 * r, cy + r], fill=color)
    d.ellipse([W_ * 0.94 - 2 * r, cy - r, W_ * 0.94, cy + r], fill=color)
    d.polygon([(W_ * 0.08, cy + r * 0.6), (W_ * 0.92, cy + r * 0.6), (W_ * 0.5, H_ * 0.94)], fill=color)
    return im.resize((w, h), Image.LANCZOS)


def ic_steps(color, w=ICON, h=ICON):
    ss = 4
    im = Image.new("RGBA", (w * ss, h * ss), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    W_, H_ = w * ss, h * ss
    # two stylised footprints
    d.ellipse([W_ * 0.16, H_ * 0.10, W_ * 0.42, H_ * 0.46], fill=color)
    d.ellipse([W_ * 0.20, H_ * 0.50, W_ * 0.38, H_ * 0.88], fill=color)
    d.ellipse([W_ * 0.58, H_ * 0.28, W_ * 0.84, H_ * 0.64], fill=color)
    d.ellipse([W_ * 0.62, H_ * 0.68, W_ * 0.80, H_ * 0.98], fill=color)
    return im.resize((w, h), Image.LANCZOS)


def ic_kcal(color, w=ICON, h=ICON):
    ss = 4
    im = Image.new("RGBA", (w * ss, h * ss), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    W_, H_ = w * ss, h * ss
    d.polygon([(W_ * 0.5, H_ * 0.06), (W_ * 0.78, H_ * 0.5), (W_ * 0.72, H_ * 0.86),
               (W_ * 0.5, H_ * 0.98), (W_ * 0.28, H_ * 0.86), (W_ * 0.22, H_ * 0.5)], fill=color)
    d.ellipse([W_ * 0.36, H_ * 0.54, W_ * 0.64, H_ * 0.86], fill=(0, 0, 0, 0))
    return im.resize((w, h), Image.LANCZOS)


def ic_battery(color, w=ICON + 6, h=20):
    ss = 4
    im = Image.new("RGBA", (w * ss, h * ss), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    W_, H_ = w * ss, h * ss
    lw = int(W_ * 0.07)
    d.rounded_rectangle([1, 1, W_ - W_ * 0.12, H_ - 1], radius=lw, outline=color, width=lw)
    d.rounded_rectangle([W_ - W_ * 0.10, H_ * 0.30, W_ - 1, H_ * 0.70], radius=2, fill=color)
    return im.resize((w, h), Image.LANCZOS)


# ---------------- asset generation ----------------
def gen_set(outdir, pal, bgsrc):
    os.makedirs(outdir, exist_ok=True)

    def save(name, im):
        im.save(os.path.join(outdir, name + ".png"))

    bg = Image.open(bgsrc).convert("RGBA").resize((W, H), Image.LANCZOS)
    save("image_0000", bg)

    sw = 3 if pal is PAL else 0
    st = pal["stroke"][:3] + (255,) if sw else None

    for i, t in enumerate(MONTHS):
        save(f"imagelist_0001_{i:04d}", glyph(t, F_DATE, pal["dim"], M_CELL, st, sw))
    for i, t in enumerate(DAYS):
        save(f"imagelist_0002_{i:04d}", glyph(t, F_DATE, pal["dim"], D_CELL, st, sw))
    for i, t in enumerate(WEEK):
        save(f"imagelist_0003_{i:04d}", glyph(t, F_DATE, pal["dim"], W_CELL, st, sw))
    save("image_0006", glyph("\u00b7", F_DATE, pal["dim"], DOT_CELL, st, sw))

    dv = Image.new("RGBA", (160, 3), (0, 0, 0, 0))
    ImageDraw.Draw(dv).rounded_rectangle([0, 0, 159, 2], radius=1, fill=pal["ring"])
    save("image_0007", dv)

    for i in range(10):
        save(f"imagelist_0000_{i:04d}", glyph(str(i), F_TIME, pal["ink"], T_CELL, st, sw))

    col = Image.new("RGBA", (COLON_W, T_CELL[1]), (0, 0, 0, 0))
    dc = ImageDraw.Draw(col)
    top = (T_CELL[1] - TIME_INK) / 2
    for fy in (0.34, 0.82):
        cy = top + fy * TIME_INK
        r = TIME_INK * 0.062
        dc.ellipse([COLON_W / 2 - r, cy - r, COLON_W / 2 + r, cy + r], fill=pal["ink"])
    save("image_0001", col)

    for i in range(10):
        save(f"imagelist_0004_{i:04d}", glyph(str(i), F_H, pal["ink"], H_CELL, st, sw))

    save("image_0002", ic_battery(pal["batt"]))
    save("image_0003", ic_heart(pal["heart"]))
    save("image_0004", ic_steps(pal["steps"]))
    save("image_0005", ic_kcal(pal["kcal"]))


BLINK_RAW = ("1811" + "00" + "20" + "0000" + "0000" + "000000" + "03" + "0002"
             + "".join(v.to_bytes(4, "little").hex() for v in range(60)))


def gen_blink(outdir):
    os.makedirs(outdir, exist_ok=True)
    for sec in range(60):
        im = Image.new("RGBA", (COLON_W, T_CELL[1]), (0, 0, 0, 0))
        if sec % 2 == 1:
            ImageDraw.Draw(im).rectangle([0, 0, COLON_W - 1, T_CELL[1] - 1], fill=(0, 0, 0, 255))
        im.save(os.path.join(outdir, f"imagelist_0005_{sec:04d}.png"))


# ---------------- dataSrc templates (device-verified from reference) ----------------
RAW_DIGNUM = {
    "081102": "081102120000E803000000030000000000000000",
    "101102": "101102120000E803000000030000000000000000",
    "082105": "082105120000E8030A0000030000000000000000",
    "082203": "082203120000E803090000030000000000000000",
    "082305": "082305120000E8030A0000030000000000000000",
    "084103": "084103120000E8030A0000030000000000000000",
}
RAW_MONTH = ("301200200000000003000003000200000100000002000000030000000400000005000000"
             "060000000700000008000000090000000A0000000B0000000C000000")
RAW_DAY = ("381200200000000004000003000200000100000002000000030000000400000005000000"
           "060000000700000008000000090000000A0000000B0000000C0000000D0000000E000000"
           "0F0000001000000011000000120000001300000014000000150000001600000017000000"
           "18000000190000001A0000001B0000001C0000001D0000001E0000001F000000")
RAW_WEEK = "20120020000000000000000300020000" + "".join(
    v.to_bytes(4, "little").hex() for v in range(7))


def dignum(idx, x, y, ds, lst, n, show_count=2, show_zero=True):
    return {"type": "widge_dignum", "x": int(x), "y": int(y), "showCount": show_count,
            "spacing": 0, "align": 2, "showZero": show_zero, "dataSrc": ds,
            "imageList": [f"{lst}_{i:04d}" for i in range(n)],
            "prop7Index": idx, "prop7Length": 20, "prop7Raw": RAW_DIGNUM[ds]}


def imagelist_el(idx, x, y, ds, lst, n, raw, index_list=None):
    e = {"type": "widge_imagelist", "x": int(x), "y": int(y), "dataSrc": ds,
         "imageList": [f"{lst}_{i:04d}" for i in range(n)],
         "prop7Index": idx, "prop7Length": (16 + n * 4), "prop7Raw": raw}
    if index_list is not None:
        e["imageIndexList"] = index_list
    return e


def centered(name, cx, cy, src):
    im = Image.open(os.path.join(src, name + ".png"))
    return {"type": "element", "x": int(round(cx - im.width / 2)),
            "y": int(round(cy - im.height / 2)), "image": name}


def build(src, aod=False):
    e, p = [], 0
    e.append({"type": "element", "x": 0, "y": 0, "image": "image_0000"})
    # date row
    e.append(imagelist_el(p, MONTH_X, Y_DATE, "1012", "imagelist_0001", 12, RAW_MONTH, list(range(1, 13))))
    p += 1
    e.append(centered("image_0006", DOT1_X + DOT_CELL[0] // 2, Y_DATE + M_CELL[1] // 2, src))
    e.append(imagelist_el(p, DAY_X, Y_DATE, "1812", "imagelist_0002", 31, RAW_DAY, list(range(1, 32))))
    p += 1
    e.append(centered("image_0006", DOT2_X + DOT_CELL[0] // 2, Y_DATE + M_CELL[1] // 2, src))
    e.append(imagelist_el(p, WK_X, Y_DATE, "2012", "imagelist_0003", 7, RAW_WEEK, list(range(7))))
    p += 1
    # time
    e.append(dignum(p, HOUR_CX, Y_TIME, "081102", "imagelist_0000", 10))
    p += 1
    e.append({"type": "element", "x": COLON_X, "y": Y_TIME, "image": "image_0001"})
    if not aod:
        e.append(imagelist_el(p, COLON_X, Y_TIME, "1811", "imagelist_0005", 60, BLINK_RAW, list(range(60))))
        p += 1
    e.append(dignum(p, MIN_CX, Y_TIME, "101102", "imagelist_0000", 10))
    p += 1
    e.append(centered("image_0007", CENTER, DIV_Y, src))
    # health row: steps | heart | calories | battery
    e.append(centered("image_0004", HCOL[0], Y_ICON_CY, src))
    e.append(dignum(p, HCOL[0], Y_NUM, "082105", "imagelist_0004", 10, show_count=5, show_zero=False))
    p += 1
    e.append(centered("image_0003", HCOL[1], Y_ICON_CY, src))
    e.append(dignum(p, HCOL[1], Y_NUM, "082203", "imagelist_0004", 10, show_count=3, show_zero=False))
    p += 1
    e.append(centered("image_0005", HCOL[2], Y_ICON_CY, src))
    e.append(dignum(p, HCOL[2], Y_NUM, "082305", "imagelist_0004", 10, show_count=5, show_zero=False))
    p += 1
    e.append(centered("image_0002", HCOL[3], Y_ICON_CY, src))
    e.append(dignum(p, HCOL[3], Y_NUM, "084103", "imagelist_0004", 10, show_count=3, show_zero=False))
    p += 1
    return e


# ---------------- build one concept ----------------
def build_concept(concept):
    bg_art = os.path.join(PROCESSED, concept + ".png")
    if not os.path.exists(bg_art):
        print(f"skip {concept}: missing {bg_art}")
        return None
    outdir = os.path.join(ROOT, concept)
    os.makedirs(outdir, exist_ok=True)
    IMG = os.path.join(outdir, "images")
    IMG_AOD = os.path.join(outdir, "images_aod")

    # normal + aod backgrounds
    aod_bg = os.path.join(outdir, "_aod_bg.png")
    Image.new("RGBA", (W, H), (0, 0, 0, 255)).save(aod_bg)

    gen_set(IMG, PAL, bg_art)
    gen_set(IMG_AOD, PAL_AOD, aod_bg)
    gen_blink(IMG)

    els = build(IMG)
    els_aod = build(IMG_AOD, aod=True)
    wf = {"name": f"AiArt-{concept}", "id": "000000000", "previewImg": "preview",
          "faceStyleCount": 4, "elementsNormal": els, "elementsAod": els_aod,
          "extraProp7Normal": [], "extraProp7Aod": [],
          "namedFaceRecords": True, "faceNames": ["\u6837\u5f0f1", "\u606f\u5c4f"]}
    with open(os.path.join(outdir, "wfDef.json"), "w") as f:
        json.dump(wf, f, ensure_ascii=False, indent=1)

    # previews
    prev = render(PAL, IMG, els)
    prev.convert("RGB").save(os.path.join(outdir, "preview.png"))
    prev.convert("RGB").quantize(256).save(os.path.join(IMG, "preview.png"))
    prev_aod = render(PAL_AOD, IMG_AOD, els_aod, hour=21, minute=7, bat=60, hr=68,
                      steps=6421, kcal=1340, wday=4, sec=41)
    prev_aod.convert("RGB").save(os.path.join(outdir, "preview_aod.png"))

    n_img = len(os.listdir(IMG))
    n_aod = len(os.listdir(IMG_AOD))
    print(f"{concept}: elements={len(els)} aod={len(els_aod)} | images={n_img} aod={n_aod}")
    return outdir


def render(pal, src, els_list, hour=9, minute=41, bat=82, hr=72, steps=8712,
           kcal=1520, month=10, day=13, wday=1, sec=41):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    im.alpha_composite(Image.open(os.path.join(src, "image_0000.png")).convert("RGBA"))
    for el in els_list:
        t = el["type"]
        if t == "element":
            im.alpha_composite(Image.open(os.path.join(src, el["image"] + ".png")).convert("RGBA"), (el["x"], el["y"]))
        elif t == "widge_dignum":
            txt = {"081102": f"{hour:02d}", "101102": f"{minute:02d}",
                   "082105": str(steps), "082203": f"{hr:02d}",
                   "082305": str(kcal), "084103": str(bat)}[el["dataSrc"]]
            cw = Image.open(os.path.join(src, el["imageList"][0] + ".png")).width
            x0 = el["x"] - cw * len(txt) // 2
            for k, ch in enumerate(txt):
                gi = 10 if ch == "-" else int(ch)
                g = Image.open(os.path.join(src, el["imageList"][gi] + ".png")).convert("RGBA")
                im.alpha_composite(g, (int(x0) + k * cw, el["y"]))
        elif t == "widge_imagelist":
            codes = el.get("imageIndexList", list(range(len(el["imageList"]))))
            ds = el["dataSrc"]
            if ds == "1012":
                fi = codes.index(month)
            elif ds == "1812":
                fi = codes.index(day)
            elif ds == "2012":
                fi = codes.index(wday)
            else:
                fi = sec % 60
            g = Image.open(os.path.join(src, el["imageList"][fi] + ".png")).convert("RGBA")
            im.alpha_composite(g, (el["x"], el["y"]))
    return im


def main():
    args = sys.argv[1:]
    if args:
        concepts = args
    else:
        concepts = sorted(os.path.splitext(f)[0] for f in os.listdir(PROCESSED) if f.endswith(".png"))
    for c in concepts:
        build_concept(c)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Mono — original Xiaomi Watch S3 (M2313W1) watch face.

Minimal monochrome digital dial:
  - date row:  MM . DD . DDD   (1012 / 1812 / 2012 prerendered frames)
  - big HH:MM time with 1 Hz blinking colon (081102 / 101102 / 1811)
  - bottom row: battery %  |  heart rate  |  temperature
  - AOD face (dimmer, no blink)

Format knowledge (dataSrc ids, prop7Raw templates, build order) is reverse-engineered
fact required for the ws3 binary format; it originates from the MIT-licensed
xiaomi-watch-s3-diy project. Artwork here is original.
"""
import os, json, math, sys
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(ROOT, "images")
IMG_AOD = os.path.join(ROOT, "images_aod")
os.makedirs(IMG, exist_ok=True)
os.makedirs(IMG_AOD, exist_ok=True)
W = H = 464

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

# ---------------- palette ----------------
PAL = dict(bg=(11, 12, 14, 255), ring=(30, 32, 38, 255), ink=(240, 240, 244, 255),
           dim=(150, 150, 158, 255), batt=(110, 220, 140, 255),
           heart=(255, 92, 92, 255), temp=(110, 170, 255, 255))
PAL_AOD = dict(bg=(0, 0, 0, 255), ring=(20, 20, 24, 255), ink=(158, 158, 166, 255),
               dim=(100, 100, 106, 255), batt=(90, 150, 105, 255),
               heart=(150, 70, 70, 255), temp=(90, 120, 170, 255))


def load_font(size):
    return ImageFont.truetype(FONT, size)


def text_image(s, font, color):
    tmp = Image.new("RGBA", (font.size * (len(s) + 2), int(font.size * 1.8)), (0, 0, 0, 0))
    ImageDraw.Draw(tmp).text((tmp.width // 2, tmp.height // 2), s, font=font, fill=color, anchor="mm")
    return tmp.crop(tmp.getbbox())


def ink_size(s, font):
    im = text_image(s, font, (255, 255, 255, 255))
    return im.size


def glyph(s, font, color, cell):
    im = text_image(s, font, color)
    out = Image.new("RGBA", cell, (0, 0, 0, 0))
    out.alpha_composite(im, ((cell[0] - im.width) // 2, (cell[1] - im.height) // 2))
    return out


# ---------------- layout ----------------
CENTER = 232

# date row
DATE_SIZE = 34
F_DATE = load_font(DATE_SIZE)
MONTHS = [f"{m:02d}" for m in range(1, 13)]
DAYS = [f"{d:02d}" for d in range(1, 32)]
WEEK = ["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"]
M_CELL = (max(ink_size(t, F_DATE)[0] for t in MONTHS) + 8, DATE_SIZE + 10)
D_CELL = (max(ink_size(t, F_DATE)[0] for t in DAYS) + 8, DATE_SIZE + 10)
W_CELL = (max(ink_size(t, F_DATE)[0] for t in WEEK) + 10, DATE_SIZE + 10)
DOT = text_image("\u00b7", F_DATE, (120, 120, 128, 255))
DOT_CELL = (DOT.width + 14, DATE_SIZE + 10)
GAP = 8
DATE_TOTAL = M_CELL[0] + DOT_CELL[0] + D_CELL[0] + DOT_CELL[0] + W_CELL[0] + 4 * GAP
Y_DATE = 54
x = CENTER - DATE_TOTAL // 2
MONTH_X = x
DOT1_X = MONTH_X + M_CELL[0] + GAP
DAY_X = DOT1_X + DOT_CELL[0] + GAP
DOT2_X = DAY_X + D_CELL[0] + GAP
WK_X = DOT2_X + DOT_CELL[0] + GAP

# big time
TIME_SIZE = 128
F_TIME = load_font(TIME_SIZE)
TIME_INK = ink_size("0", F_TIME)[1]
T_CELL = (max(ink_size(str(d), F_TIME)[0] for d in range(10)) + 6, TIME_INK + 8)
COLON_W = 18
COLON_GAP = 12
TIME_BLOCK = 4 * T_CELL[0] + COLON_GAP
TIME_LEFT = CENTER - TIME_BLOCK // 2
Y_TIME = 156
HOUR_CX = TIME_LEFT + T_CELL[0]
COLON_X = TIME_LEFT + 2 * T_CELL[0]
MIN_CX = TIME_LEFT + 3 * T_CELL[0] + COLON_GAP

# divider line under time
DIV_Y = Y_TIME + T_CELL[1] + 26

# bottom row: battery / heart / temperature
B_SIZE = 44
F_B = load_font(B_SIZE)
B_CELL = (max(ink_size(str(d), F_B)[0] for d in range(10)) + 3, B_SIZE + 8)
ICON = 44
COL = [116, 232, 348]
Y_ICON_CY = 392
Y_NUM = 408


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


def ic_battery(color, w=ICON + 6, h=26):
    ss = 4
    im = Image.new("RGBA", (w * ss, h * ss), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    W_, H_ = w * ss, h * ss
    lw = int(W_ * 0.08)
    d.rounded_rectangle([1, 1, W_ - W_ * 0.12, H_ - 1], radius=lw, outline=color, width=lw)
    d.rounded_rectangle([W_ - W_ * 0.10, H_ * 0.30, W_ - 1, H_ * 0.70], radius=2, fill=color)
    return im.resize((w, h), Image.LANCZOS)


def ic_temp(color, w=ICON, h=ICON):
    ss = 4
    im = Image.new("RGBA", (w * ss, h * ss), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    W_, H_ = w * ss, h * ss
    d.line([W_ * 0.5, H_ * 0.12, W_ * 0.5, H_ * 0.88], fill=color, width=int(W_ * 0.10))
    d.ellipse([W_ * 0.5 - W_ * 0.16, H_ * 0.72, W_ * 0.5 + W_ * 0.16, H_ * 0.98], fill=color)
    return im.resize((w, h), Image.LANCZOS)


# ---------------- asset generation ----------------
def gen_set(outdir, pal):
    os.makedirs(outdir, exist_ok=True)

    def save(name, im):
        im.save(os.path.join(outdir, name + ".png"))

    # background: dark circle + subtle ring
    bg = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(bg)
    d.ellipse([0, 0, W - 1, H - 1], fill=pal["bg"])
    d.ellipse([6, 6, W - 7, H - 7], outline=pal["ring"], width=3)
    save("image_0000", bg)

    # date frames
    for i, t in enumerate(MONTHS):
        save(f"imagelist_0001_{i:04d}", glyph(t, F_DATE, pal["dim"], M_CELL))
    for i, t in enumerate(DAYS):
        save(f"imagelist_0002_{i:04d}", glyph(t, F_DATE, pal["dim"], D_CELL))
    for i, t in enumerate(WEEK):
        save(f"imagelist_0003_{i:04d}", glyph(t, F_DATE, pal["dim"], W_CELL))

    # date dot separator
    save("image_0004", glyph("\u00b7", F_DATE, pal["dim"], DOT_CELL))

    # divider line
    dv = Image.new("RGBA", (200, 4), (0, 0, 0, 0))
    ImageDraw.Draw(dv).rounded_rectangle([0, 0, 199, 3], radius=2, fill=pal["ring"])
    save("image_0005", dv)

    # time digits
    for i in range(10):
        save(f"imagelist_0000_{i:04d}", glyph(str(i), F_TIME, pal["ink"], T_CELL))

    # static colon
    col = Image.new("RGBA", (COLON_W, T_CELL[1]), (0, 0, 0, 0))
    dc = ImageDraw.Draw(col)
    top = (T_CELL[1] - TIME_INK) / 2
    for fy in (0.34, 0.82):
        cy = top + fy * TIME_INK
        r = TIME_INK * 0.062
        dc.ellipse([COLON_W / 2 - r, cy - r, COLON_W / 2 + r, cy + r], fill=pal["ink"])
    save("image_0001", col)

    # bottom digits + minus
    for i in range(10):
        save(f"imagelist_0006_{i:04d}", glyph(str(i), F_B, pal["ink"], B_CELL))
    save("imagelist_0006_0010", glyph("-", F_B, pal["ink"], B_CELL))

    # icons
    save("image_0002", ic_battery(pal["batt"]))
    save("image_0003", ic_heart(pal["heart"]))
    save("image_0007", ic_temp(pal["temp"]))


BLINK_RAW = ("1811" + "00" + "20" + "0000" + "0000" + "000000" + "03" + "0002"
             + "".join(v.to_bytes(4, "little").hex() for v in range(60)))


def gen_blink(outdir):
    os.makedirs(outdir, exist_ok=True)
    for sec in range(60):
        im = Image.new("RGBA", (COLON_W, T_CELL[1]), (0, 0, 0, 0))
        if sec % 2 == 1:
            ImageDraw.Draw(im).rectangle([0, 0, COLON_W - 1, T_CELL[1] - 1], fill=(0, 0, 0, 255))
        im.save(os.path.join(outdir, f"imagelist_0008_{sec:04d}.png"))


gen_set(IMG, PAL)
gen_set(IMG_AOD, PAL_AOD)
gen_blink(IMG)


# ---------------- wfDef ----------------
RAW_DIGNUM = {
    "081102": "081102120000E803000000030000000000000000",
    "101102": "101102120000E803000000030000000000000000",
    "082202": "082202120000E803000000030000000000000000",
    "084103": "084103120000E803000000030000000000000000",
    "203103": "203103120000E803000000030000000000000000",
}
RAW_MONTH = ("301200200000000003000003000200000100000002000000030000000400000005000000"
             "060000000700000008000000090000000A0000000B0000000C000000")
RAW_DAY = ("381200200000000004000003000200000100000002000000030000000400000005000000"
           "060000000700000008000000090000000A0000000B0000000C0000000D0000000E000000"
           "0F0000001000000011000000120000001300000014000000150000001600000017000000"
           "18000000190000001A0000001B0000001C0000001D0000001E0000001F000000")
RAW_WEEK = "20120020000000000000000300020000" + "".join(
    v.to_bytes(4, "little").hex() for v in range(7))


def dignum(idx, x, y, ds, lst, n, show_zero=True):
    return {"type": "widge_dignum", "x": int(x), "y": int(y), "showCount": 2,
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


def centered(name, cx, cy, src=IMG):
    im = Image.open(os.path.join(src, name + ".png"))
    return {"type": "element", "x": int(round(cx - im.width / 2)),
            "y": int(round(cy - im.height / 2)), "image": name}


def build(aod=False):
    e, p = [], 0
    e.append({"type": "element", "x": 0, "y": 0, "image": "image_0000"})
    # date row
    e.append(imagelist_el(p, MONTH_X, Y_DATE, "1012", "imagelist_0001", 12, RAW_MONTH, list(range(1, 13))))
    p += 1
    e.append(centered("image_0004", DOT1_X + DOT_CELL[0] // 2, Y_DATE + M_CELL[1] // 2))
    e.append(imagelist_el(p, DAY_X, Y_DATE, "1812", "imagelist_0002", 31, RAW_DAY, list(range(1, 32))))
    p += 1
    e.append(centered("image_0004", DOT2_X + DOT_CELL[0] // 2, Y_DATE + M_CELL[1] // 2))
    e.append(imagelist_el(p, WK_X, Y_DATE, "2012", "imagelist_0003", 7, RAW_WEEK, list(range(7))))
    p += 1
    # time
    e.append(dignum(p, HOUR_CX, Y_TIME, "081102", "imagelist_0000", 10))
    p += 1
    e.append({"type": "element", "x": COLON_X, "y": Y_TIME, "image": "image_0001"})
    if not aod:
        e.append(imagelist_el(p, COLON_X, Y_TIME, "1811", "imagelist_0008", 60, BLINK_RAW, list(range(60))))
        p += 1
    e.append(dignum(p, MIN_CX, Y_TIME, "101102", "imagelist_0000", 10))
    p += 1
    # divider
    e.append(centered("image_0005", CENTER, DIV_Y))
    # bottom row
    e.append(centered("image_0002", COL[0], Y_ICON_CY))
    e.append(dignum(p, COL[0], Y_NUM, "084103", "imagelist_0006", 10, show_zero=False))
    p += 1
    e.append(centered("image_0003", COL[1], Y_ICON_CY))
    e.append(dignum(p, COL[1], Y_NUM, "082202", "imagelist_0006", 10, show_zero=False))
    p += 1
    e.append(centered("image_0007", COL[2], Y_ICON_CY))
    e.append(dignum(p, COL[2], Y_NUM, "203103", "imagelist_0006", 11, show_zero=False))
    p += 1
    return e


els = build()
els_aod = build(aod=True)
wf = {"name": "Mono", "id": "000000000", "previewImg": "preview", "faceStyleCount": 4,
      "elementsNormal": els, "elementsAod": els_aod,
      "extraProp7Normal": [], "extraProp7Aod": [],
      "namedFaceRecords": True, "faceNames": ["样式1", "息屏"]}
with open(os.path.join(ROOT, "wfDef.json"), "w") as f:
    json.dump(wf, f, ensure_ascii=False, indent=1)


# ---------------- preview ----------------
def render(pal, src, els_list, hour=9, minute=41, bat=82, hr=72, temp=24,
           month=10, day=13, wday=1, sec=41):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    im.alpha_composite(Image.open(os.path.join(src, "image_0000.png")).convert("RGBA"))
    for el in els_list:
        t = el["type"]
        if t == "element":
            im.alpha_composite(Image.open(os.path.join(src, el["image"] + ".png")).convert("RGBA"), (el["x"], el["y"]))
        elif t == "widge_dignum":
            txt = {"081102": f"{hour:02d}", "101102": f"{minute:02d}",
                   "082202": f"{hr:02d}", "084103": str(bat), "203103": str(temp)}[el["dataSrc"]]
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


prev = render(PAL, IMG, els)
prev.convert("RGB").save(os.path.join(ROOT, "preview.png"))
prev.convert("RGB").quantize(256).save(os.path.join(IMG, "preview.png"))
prev_aod = render(PAL_AOD, IMG_AOD, els_aod, hour=21, minute=7, bat=60, hr=68, temp=18, wday=4)
prev_aod.convert("RGB").save(os.path.join(ROOT, "preview_aod.png"))

print(f"OK elements={len(els)} (aod {len(els_aod)}) | date_total={DATE_TOTAL} | time_block={TIME_BLOCK}")
print(f"images: {len(os.listdir(IMG))} normal, {len(os.listdir(IMG_AOD))} aod")

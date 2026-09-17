"""ココナラ出品サムネイル合成スクリプト(v4・ダーク/プレミアム)

1220x1240px。全面ダークネイビー地＋ティールのアクセント。
上：英字ラベル(ティール)＋キャッチ(白)＋ティールの下線
中央：実サイトのスクショ/図解をグロー付きで配置
下：枠線ピルのタグ
検索一覧の上下120pxトリミングに対して、重要文言は安全圏(SAFE以降/H-SAFE以前)に収める。
"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1220, 1240
SAFE = 120

BG = (15, 22, 29)
INK = (255, 255, 255)
SUB = (206, 212, 214)
TEAL = (74, 214, 200)
TEAL_DIM = (96, 150, 145)

HIRA = "/System/Library/Fonts/ヒラギノ角ゴシック W{}.ttc"
ASSETS = "/Users/nagomutsuhiro/開発/video-notes/_secretary/coconala_assets"
OUT = ASSETS


def font(w, size):
    return ImageFont.truetype(HIRA.format(w), size)


def draw_centered(d, lines, cx, top_y, f, fill, line_gap=12):
    y = top_y
    for line in lines:
        b = d.textbbox((0, 0), line, font=f)
        d.text((cx - (b[2] - b[0]) / 2 - b[0], y - b[1]), line, font=f, fill=fill)
        y += (b[3] - b[1]) + line_gap
    return y


def draw_tracked(d, text, cx, y, f, fill, tracking=8):
    ws = [d.textbbox((0, 0), c, font=f)[2] for c in text]
    total = sum(ws) + tracking * (len(text) - 1)
    x = cx - total / 2
    b = d.textbbox((0, 0), "A", font=f)
    for c, wch in zip(text, ws):
        d.text((x, y - b[1]), c, font=f, fill=fill)
        x += wch + tracking


def rounded_mask(size, radius):
    m = Image.new("L", size, 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, size[0] - 1, size[1] - 1), radius=radius, fill=255)
    return m


def cover_crop(im, tw, th, focus="top"):
    sw, sh = im.size
    if sw / sh > tw / th:
        nh, nw = th, int(sw * (th / sh))
    else:
        nw, nh = tw, int(sh * (tw / sw))
    im2 = im.resize((nw, nh), Image.LANCZOS)
    top = 0 if focus == "top" else (nh - th) // 2
    return im2.crop(((nw - tw) // 2, top, (nw - tw) // 2 + tw, top + th))


def browser_frame(path_or_img, fw, fh, chrome_h=32, radius=13):
    frame = Image.new("RGBA", (fw, fh), (0, 0, 0, 0))
    d = ImageDraw.Draw(frame)
    d.rounded_rectangle((0, 0, fw - 1, fh - 1), radius=radius, fill=(238, 240, 243, 255))
    d.rounded_rectangle((0, 0, fw - 1, chrome_h + radius), radius=radius, fill=(224, 226, 230, 255))
    d.rectangle((0, radius, fw - 1, chrome_h), fill=(224, 226, 230, 255))
    for i, col in enumerate([(237, 106, 94), (245, 191, 79), (97, 197, 79)]):
        cxx = 16 + i * 21
        d.ellipse((cxx - 6, chrome_h / 2 - 6, cxx + 6, chrome_h / 2 + 6), fill=col)
    src = path_or_img if isinstance(path_or_img, Image.Image) else Image.open(path_or_img)
    shot = cover_crop(src.convert("RGB"), fw - 14, fh - chrome_h - 10, focus="top")
    frame.paste(shot, (7, chrome_h + 5))
    out = Image.new("RGBA", (fw, fh), (0, 0, 0, 0))
    out.paste(frame, (0, 0), rounded_mask((fw, fh), radius))
    return out


def phone_frame(path, fw, fh, bezel=11, radius=44):
    frame = Image.new("RGBA", (fw, fh), (0, 0, 0, 0))
    d = ImageDraw.Draw(frame)
    d.rounded_rectangle((0, 0, fw - 1, fh - 1), radius=radius, fill=(18, 18, 20, 255))
    sw, sh = fw - bezel * 2, fh - bezel * 2
    shot = cover_crop(Image.open(path).convert("RGB"), sw, sh, focus="top")
    layer = Image.new("RGBA", (sw, sh), (0, 0, 0, 0))
    layer.paste(shot, (0, 0), rounded_mask((sw, sh), radius - bezel))
    frame.paste(layer, (bezel, bezel), layer)
    nw = fw * 0.32
    d.rounded_rectangle((fw / 2 - nw / 2, bezel - 2, fw / 2 + nw / 2, bezel + 18), radius=10, fill=(18, 18, 20, 255))
    out = Image.new("RGBA", (fw, fh), (0, 0, 0, 0))
    out.paste(frame, (0, 0), rounded_mask((fw, fh), radius))
    return out


def rounded_card(img, radius=16):
    out = Image.new("RGBA", img.size, (0, 0, 0, 0))
    out.paste(img.convert("RGB"), (0, 0), rounded_mask(img.size, radius))
    return out


def place(canvas, piece, pos, glow=True, glow_rgb=TEAL, glow_op=120, glow_blur=40,
          shadow=True, shadow_op=150, shadow_blur=30, shadow_off=(0, 20)):
    if glow:
        g = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        a = piece.split()[-1].point(lambda v: glow_op if v > 0 else 0)
        s = Image.new("RGBA", piece.size, glow_rgb + (255,))
        s.putalpha(a)
        g.paste(s, pos, s)
        canvas.alpha_composite(g.filter(ImageFilter.GaussianBlur(glow_blur)))
    if shadow:
        sh = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        a = piece.split()[-1].point(lambda v: shadow_op if v > 0 else 0)
        s = Image.new("RGBA", piece.size, (0, 0, 0, 255))
        s.putalpha(a)
        sh.paste(s, (pos[0] + shadow_off[0], pos[1] + shadow_off[1]), s)
        canvas.alpha_composite(sh.filter(ImageFilter.GaussianBlur(shadow_blur)))
    canvas.alpha_composite(piece, pos)


def bg_texture():
    img = Image.new("RGBA", (W, H), BG + (255,))
    # ごく淡いラジアルグロー（中央上）
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse((W / 2 - 520, 40, W / 2 + 520, 900), fill=(30, 60, 62, 90))
    img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(160)))
    return img


def pill_row(d, labels, cy, fnt):
    ws = [d.textbbox((0, 0), l, font=fnt)[2] + 54 for l in labels]
    gap = 18
    x = W / 2 - (sum(ws) + gap * (len(ws) - 1)) / 2
    for l, w in zip(labels, ws):
        cx = x + w / 2
        b = d.textbbox((0, 0), l, font=fnt)
        th = b[3] - b[1]
        y0, y1 = cy - th / 2 - 14, cy + th / 2 + 14
        d.rounded_rectangle((x, y0, x + w, y1), radius=(y1 - y0) / 2, outline=TEAL_DIM, width=2)
        d.text((cx - (b[2] - b[0]) / 2 - b[0], cy - th / 2 - b[1]), l, font=fnt, fill=(230, 245, 243))
        x += w + gap


def build(name, eyebrow, catch_lines, tags, mockup_fn, catch_size=52):
    img = bg_texture()
    d = ImageDraw.Draw(img)
    draw_tracked(d, eyebrow, W / 2, 150, font(5, 22), TEAL, tracking=9)
    y = draw_centered(d, catch_lines[:1], W / 2, 186, font(8, catch_size), INK)
    y = draw_centered(d, catch_lines[1:], W / 2, y + 2, font(7, int(catch_size * 0.76)), SUB)
    d.line((W / 2 - 66, y + 16, W / 2 + 66, y + 16), fill=TEAL, width=4)

    mockup_fn(img)

    pill_row(d, tags, H - 96, font(6, 27))
    img.convert("RGB").save(f"{OUT}/{name}")
    print("saved", name)


# ---- 1. LP制作 : shiro-clinic 白クリニック ----
def lp_mockup(canvas):
    lap = browser_frame(f"{ASSETS}/shiro_pc.png", 880, 545)
    place(canvas, lap, (60, 372))
    ph = phone_frame(f"{ASSETS}/shiro_mobile.png", 248, 508)
    place(canvas, ph, (852, 458), glow_op=90)


# ---- 2. ホームページ制作 : momemo 3Dスクロールデモ ----
def hp_mockup(canvas):
    lap = browser_frame(f"{ASSETS}/demo3d_pc.png", 880, 545)
    place(canvas, lap, (60, 372))
    ph = phone_frame(f"{ASSETS}/demo3d_mobile.png", 248, 508)
    place(canvas, ph, (852, 458), glow_op=90)


# ---- 3. 社内ツール開発 : バーコード→表→通知の図解を白パネルで配置 ----
def sw_mockup(canvas):
    src = Image.open(f"{ASSETS}/sw_v1_full.png").convert("RGB")
    dia = src.crop((60, 360, W - 60, 1006))       # 図解の中身だけタイトに
    dia = dia.resize((1020, int(dia.height * 1020 / dia.width)), Image.LANCZOS)
    card = rounded_card(dia, radius=18)
    px = (W - card.width) // 2
    py = 400
    place(canvas, card, (px, py), glow_op=110, glow_blur=46)


if __name__ == "__main__":
    build(
        "coconala出品画像_LP制作_v2.png",
        "LANDING PAGE",
        ["高品質なのに1.5万円〜。", "スマホ対応・SEO込みのLP制作"],
        ["1.5万円〜", "スマホ対応", "SEO対策込み"],
        lp_mockup, catch_size=52,
    )
    build(
        "coconala出品画像_ホームページ制作_v2.png",
        "WEBSITE",
        ["集客・信頼につながる", "ホームページを3万円〜"],
        ["3万円〜", "SEO対策込み", "ドメイン設定サポート"],
        hp_mockup, catch_size=54,
    )
    build(
        "coconala出品画像_社内ツール開発_v2.png",
        "GAS BUSINESS TOOL",
        ["バーコード管理から記録作成まで", "GAS業務ツールを開発します"],
        ["GAS開発", "自動化", "5,000円〜"],
        sw_mockup, catch_size=50,
    )

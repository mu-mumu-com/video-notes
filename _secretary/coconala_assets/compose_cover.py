"""ココナラ プロフィールカバー画像(1280x420)

awwwards の dark-minimal hero 定石 + フォント刷新:
 - ラテンのワードマーク/ラベルを Futura(幾何学サンス)へ。studio ブランドらしい佇まい
 - 日本語タグラインはヒラギノ明朝でエディトリアルなコントラスト
 - 可読性重視: 地は締まった黒、文字は高コントラスト、左3分の1にダークスクリム
 - 右の実制作物は暗く落として端で切る(証拠写真として静かに置く)
左下はアバターが重なるため本文は左上〜中央、モックアップは右側。
"""
from PIL import Image, ImageEnhance
import compose_coconala_image as cc

W, H = 1280, 420
DIR = cc.ASSETS
OUT = f"{DIR}/coconala_cover.png"

BASE = (13, 13, 15)
INK = (247, 247, 249)
SOFT = (206, 210, 212)
MUTE = (150, 156, 158)
TEAL = (86, 222, 208)

FUTURA = "/System/Library/Fonts/Supplemental/Futura.ttc"
MINCHO = "/System/Library/Fonts/ヒラギノ明朝 ProN.ttc"
KAKU = "/System/Library/Fonts/ヒラギノ角ゴシック W{}.ttc"


def lat(size, bold=False):
    return cc.ImageFont.truetype(FUTURA, size, index=(2 if bold else 0))


def mincho(size):
    return cc.ImageFont.truetype(MINCHO, size)


def kaku(w, size):
    return cc.ImageFont.truetype(KAKU.format(w), size)


def grain(alpha=8, sigma=40):
    n = Image.effect_noise((W, H), sigma).convert("L")
    px = Image.new("RGBA", (W, H), (255, 255, 255, 255))
    px.putalpha(n.point(lambda v: int(abs(v - 128) / 128 * alpha)))
    return px


def bg():
    img = Image.new("RGBA", (W, H), BASE + (255,))
    g = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    cc.ImageDraw.Draw(g).ellipse((W - 600, -260, W + 260, 360), fill=(28, 44, 44, 66))
    img.alpha_composite(g.filter(cc.ImageFilter.GaussianBlur(160)))
    img.alpha_composite(grain(8))
    return img


def darken(rgba, factor, sat=0.8):
    r, g, b, a = rgba.split()
    rgb = Image.merge("RGB", (r, g, b))
    rgb = ImageEnhance.Brightness(rgb).enhance(factor)
    rgb = ImageEnhance.Color(rgb).enhance(sat)
    r2, g2, b2 = rgb.split()
    return Image.merge("RGBA", (r2, g2, b2, a))


def left_scrim(img, upto=640, strength=225):
    s = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = cc.ImageDraw.Draw(s)
    for x in range(upto):
        a = int(strength * (1 - x / upto) ** 1.6)
        sd.line((x, 0, x, H), fill=BASE + (a,))
    img.alpha_composite(s)


def tracked(d, text, x, y, f, fill, tr=8):
    b = d.textbbox((0, 0), "H", font=f)
    for ch in text:
        d.text((x, y - b[1]), ch, font=f, fill=fill)
        x += d.textbbox((0, 0), ch, font=f)[2] + tr


def build():
    img = bg()

    lap = cc.browser_frame(f"{DIR}/demo3d_pc.png", 690, 412)
    lap = darken(lap, 0.6, 0.7).rotate(-6, expand=True, resample=Image.BICUBIC)
    cc.place(img, lap, (812, 70), glow=True, glow_rgb=TEAL, glow_op=42, glow_blur=55,
             shadow_op=175, shadow_blur=42, shadow_off=(0, 26))

    left_scrim(img)

    d = cc.ImageDraw.Draw(img)

    # ● AVAILABLE FOR WORK
    d.ellipse((92, 106, 103, 117), fill=TEAL)
    tracked(d, "AVAILABLE FOR WORK", 116, 102, lat(14), MUTE, tr=3)

    # ワードマーク: Futura
    f_wm = lat(60, bold=True)
    x = 88
    b = d.textbbox((0, 0), "momemo", font=f_wm)
    d.text((x - b[0], 140 - b[1]), "momemo", font=f_wm, fill=INK)
    x2 = x + (b[2] - b[0]) + 22
    f_wm2 = lat(60, bold=False)
    tracked(d, "studio", x2, 140, f_wm2, SOFT, tr=4)
    wm_bottom = 140 + (b[3] - b[1])

    d.line((90, wm_bottom + 24, 150, wm_bottom + 24), fill=TEAL, width=3)

    # タグライン: 明朝・高コントラスト
    tl = "ホームページ・LP制作 ／ GASによる業務自動化ツール開発"
    fb = mincho(21)
    lb = d.textbbox((0, 0), tl, font=fb)
    d.text((90 - lb[0], wm_bottom + 46 - lb[1]), tl, font=fb, fill=(224, 227, 228))

    img.convert("RGB").save(OUT)
    print("saved", OUT)


if __name__ == "__main__":
    build()

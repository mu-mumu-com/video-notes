"""ココナラ出品 詳細画像(2〜5枚目)合成スクリプト・ダーク/プレミアム

1枚目サムネイル(compose_coconala_image.py)と同じ世界観:
全面ダークネイビー地＋ティールのアクセント、英字ラベル＋白見出し＋ティール下線。
2枚目=依頼できること / 3枚目=進め方 / 4枚目=強み / 5枚目=料金プラン＆注意事項

出力: coconala_assets/ 配下に `詳細_<サービス>_<n>_<種別>.png`
検索一覧トリミング(上下120px)は詳細画像では影響しないが、余白は広めに取る。
"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter

from compose_coconala_image import (
    W, H, BG, INK, SUB, TEAL, TEAL_DIM,
    font, draw_tracked, bg_texture, rounded_mask,
)

ASSETS = "/Users/nagomutsuhiro/開発/video-notes/_secretary/coconala_assets"
OUT = ASSETS

CARD_BG = (24, 34, 43)
CARD_LINE = (44, 60, 70)

# コンテンツを縦中央に置く領域
REGION_TOP = 312
REGION_BOT = 1150


def region_y(total):
    # 上部にヘッダーがある分、やや上寄せ(0.42)にすると視覚的に釣り合う
    return int(REGION_TOP + max(0, (REGION_BOT - REGION_TOP - total)) * 0.42)


# ---------- 共通パーツ ----------
def wrap(d, text, f, maxw):
    """日本語は文字単位で折り返す。"""
    lines, cur = [], ""
    for ch in text:
        if ch == "\n":
            lines.append(cur)
            cur = ""
            continue
        if d.textlength(cur + ch, font=f) <= maxw or not cur:
            cur += ch
        else:
            lines.append(cur)
            cur = ch
    if cur:
        lines.append(cur)
    return lines


def text_l(d, xy, s, f, fill):
    b = d.textbbox((0, 0), s, font=f)
    d.text((xy[0], xy[1] - b[1]), s, font=f, fill=fill)


def text_c(d, cx, y, s, f, fill):
    b = d.textbbox((0, 0), s, font=f)
    d.text((cx - (b[2] - b[0]) / 2 - b[0], y - b[1]), s, font=f, fill=fill)


def header(img, eyebrow, title):
    d = ImageDraw.Draw(img)
    draw_tracked(d, eyebrow, W / 2, 150, font(5, 22), TEAL, tracking=9)
    text_c(d, W / 2, 196, title, font(8, 46), INK)
    d.line((W / 2 - 66, 272, W / 2 + 66, 272), fill=TEAL, width=4)


def footer(img, label):
    d = ImageDraw.Draw(img)
    text_c(d, W / 2, 1176, f"—  {label}  —", font(5, 20), TEAL_DIM)


def panel(img, box, radius=18, fill=CARD_BG, outline=CARD_LINE, width=2):
    x0, y0, x1, y1 = box
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    ld.rounded_rectangle(box, radius=radius, fill=fill + (255,),
                         outline=outline + (255,), width=width)
    img.alpha_composite(layer)


def save(img, name):
    img.convert("RGB").save(f"{OUT}/{name}")
    print("saved", name)


# ---------- 2枚目: 依頼できること ----------
def slide_list(svc, items):
    img = bg_texture()
    header(img, "WHAT YOU CAN ORDER", "こんなご依頼に対応します")
    d = ImageDraw.Draw(img)
    x0, x1 = 96, W - 96
    tx = x0 + 76
    maxw = x1 - tx - 44
    f = font(6, 31)

    blocks = [wrap(d, it, f, maxw) for it in items]
    lh = 44
    pads = 28
    gap = 18
    heights = [len(b) * lh + pads * 2 for b in blocks]
    total = sum(heights) + gap * (len(blocks) - 1)
    y = region_y(total)

    for it_lines, h in zip(blocks, heights):
        panel(img, (x0, y, x1, y + h))
        d = ImageDraw.Draw(img)
        # ティールのチェック丸（1行目の中心に合わせる）
        cyc = y + pads + lh / 2 - 4
        d.ellipse((x0 + 28, cyc - 15, x0 + 58, cyc + 15), outline=TEAL, width=3)
        d.line((x0 + 35, cyc, x0 + 41, cyc + 7), fill=TEAL, width=3)
        d.line((x0 + 41, cyc + 7, x0 + 52, cyc - 7), fill=TEAL, width=3)
        ty = y + pads
        for ln in it_lines:
            text_l(d, (tx, ty), ln, f, INK)
            ty += lh
        y += h + gap

    footer(img, svc)
    return img


# ---------- 3枚目: 進め方 ----------
def slide_steps(svc, steps):
    img = bg_texture()
    header(img, "HOW IT WORKS", "ご依頼から納品までの流れ")
    d = ImageDraw.Draw(img)
    x0 = 128
    cx = x0 + 30
    tx = x0 + 92
    ftitle = font(7, 31)
    fdetail = font(5, 24)
    fnum = font(8, 25)
    ldet = 36

    rows = []
    for s in steps:
        title, _, detail = s.partition("｜")
        det_lines = wrap(d, detail, fdetail, W - tx - 96) if detail else []
        h = 40 + (len(det_lines) * ldet + 10 if det_lines else 0)
        h = max(h, 74)
        rows.append((title, det_lines, h))

    gap = 44
    total = sum(h for _, _, h in rows) + gap * (len(rows) - 1)
    y = region_y(total)

    centers = []
    yy = y
    for _, _, h in rows:
        centers.append(yy + h / 2)
        yy += h + gap
    d.line((cx, centers[0], cx, centers[-1]), fill=TEAL_DIM, width=2)

    yy = y
    for i, (title, det_lines, h) in enumerate(rows):
        cyc = centers[i]
        d.ellipse((cx - 26, cyc - 26, cx + 26, cyc + 26), fill=BG, outline=TEAL, width=3)
        text_c(d, cx, cyc, str(i + 1), fnum, TEAL)
        block_h = 34 + (len(det_lines) * ldet if det_lines else 0)
        ty = cyc - block_h / 2
        text_l(d, (tx, ty), title, ftitle, INK)
        ty += 44
        for ln in det_lines:
            text_l(d, (tx, ty), ln, fdetail, SUB)
            ty += ldet
        yy += h + gap

    footer(img, svc)
    return img


# ---------- 4枚目: 強み ----------
def slide_strengths(svc, strengths):
    img = bg_texture()
    header(img, "WHY CHOOSE ME", "選ばれる3つの理由")
    d = ImageDraw.Draw(img)
    x0, x1 = 96, W - 96
    gap = 30
    fl = font(8, 33)
    fd = font(5, 25)
    inx = x0 + 40
    ldd = 37

    cards = []
    for s in strengths:
        lead, desc = s.split(" — ", 1)
        dlines = wrap(d, desc, fd, x1 - inx - 40)
        h = 60 + 46 + len(dlines) * ldd + 34
        cards.append((lead, dlines, h))

    total = sum(h for _, _, h in cards) + gap * (len(cards) - 1)
    y = region_y(total)

    for i, (lead, dlines, h) in enumerate(cards):
        panel(img, (x0, y, x1, y + h))
        d = ImageDraw.Draw(img)
        d.rounded_rectangle((x0, y, x0 + 8, y + h), radius=4, fill=TEAL)
        text_l(d, (inx, y + 34), f"0{i + 1}", font(8, 29), TEAL)
        text_l(d, (inx + 62, y + 32), lead, fl, INK)
        dy = y + 60 + 46
        for ln in dlines:
            text_l(d, (inx, dy), ln, fd, SUB)
            dy += ldd
        y += h + gap
    footer(img, svc)
    return img


# ---------- 5枚目: 料金プラン & 注意事項 ----------
def slide_price_notes(svc, plans, notes):
    img = bg_texture()
    header(img, "PRICING & NOTES", "料金プランとご依頼前の注意")
    d = ImageDraw.Draw(img)
    x0, x1 = 96, W - 96
    fp = font(6, 27)
    fv = font(8, 30)
    fn = font(5, 25)
    ph = 78
    prow = ph + 16
    lh = 36

    note_lines = [wrap(d, n, fn, x1 - x0 - 56) for n in notes]
    price_block = 34 + len(plans) * prow - 16
    notes_block = 34 + 20 + sum(len(nl) * lh + 14 for nl in note_lines)
    total = price_block + 52 + notes_block
    # このスライドは上寄せ固定（1プランのときに間延びしないよう）
    y = max(330, region_y(total) - 90)

    draw_tracked(d, "PRICING", W / 2, y, font(6, 20), TEAL, tracking=6)
    y += 36
    for name, price in plans:
        panel(img, (x0, y, x1, y + ph))
        d = ImageDraw.Draw(img)
        b0 = d.textbbox((0, 0), name, font=fp)
        d.text((x0 + 34, y + ph / 2 - (b0[3] - b0[1]) / 2 - b0[1]), name, font=fp, fill=INK)
        b = d.textbbox((0, 0), price, font=fv)
        d.text((x1 - 34 - (b[2] - b[0]), y + ph / 2 - (b[3] - b[1]) / 2 - b[1]), price, font=fv, fill=TEAL)
        y += prow

    y += 44
    draw_tracked(d, "NOTES", W / 2, y, font(6, 20), TEAL, tracking=6)
    y += 42
    for lines in note_lines:
        d.ellipse((x0 + 5, y + 15, x0 + 15, y + 25), fill=TEAL_DIM)
        for ln in lines:
            text_l(d, (x0 + 38, y), ln, fn, SUB)
            y += lh
        y += 14

    footer(img, svc)
    return img


# ================= コンテンツ =================
DATA = {
    "LP制作": {
        "list": [
            "LPの新規制作（デザイン〜実装〜公開まで一括対応）",
            "既存LPのリニューアル・改善",
            "スマートフォン対応（レスポンシブデザイン）",
            "基本的なSEO対策（メタタグ・OGP設定）",
            "お問い合わせフォームの設置",
        ],
        "steps": [
            "ヒアリング｜目的・ターゲット・掲載したい情報をお伺いします",
            "デザイン案のご提案｜1案をベースに調整し、方向性を固めます",
            "実装・公開準備",
            "公開前の最終確認・修正（軽微な修正2回まで込み）",
            "公開・納品",
        ],
        "strengths": [
            "制作者本人が一貫対応 — デザインから実装まで分業・仲介なし。意図のズレが少なく、この価格を実現しています",
            "実績を公開しています — ポートフォリオサイトと、実際に運用中のサンプルサイトをご確認いただけます",
            "“売れる導線”を意識 — 見た目を整えるだけでなく、問い合わせ・申し込みにつながる構成で制作します",
        ],
        "plans": [("LP（1ページ）", "15,000円〜")],
        "notes": [
            "EC（決済・カート）、会員登録・ログイン機能を含むサイトは対応しておりません",
            "ドメイン・サーバー費用はお客様負担です（取得・設定のご相談は可能）",
            "テキスト・画像などの素材はお客様にご用意いただきます",
            "軽微な修正は2回まで無料、大幅な仕様変更は追加料金の場合があります",
            "納期目安：ご依頼内容の確定後、約1〜2週間",
        ],
    },
    "ホームページ制作": {
        "list": [
            "複数ページ構成のホームページ制作（コーポレート／店舗）",
            "基本ページ一式（会社概要・サービス紹介・問い合わせ等）",
            "スマートフォン対応（レスポンシブデザイン）",
            "基本的なSEO対策（メタタグ・OGP・構造化データ）",
            "ドメイン・公開設定のサポート（取得代行のご相談も可能）",
        ],
        "steps": [
            "ヒアリング｜会社・サービス内容、必要なページ構成をお伺いします",
            "サイトマップ・デザイン案のご提案",
            "実装・各ページの制作",
            "公開前の最終確認・修正（軽微な修正2回まで込み）",
            "公開・納品｜簡単な更新方法もご案内します",
        ],
        "strengths": [
            "制作者本人が一貫対応 — AI開発ツールを使いこなし、デザインから実装まで一人で担当します",
            "実績を公開しています — ポートフォリオサイトと、実際に運用中のサンプルサイトをご確認いただけます",
            "統一感のある設計 — ページ数が増えても、一貫したデザインと導線設計で仕上げます",
        ],
        "plans": [("コーポレートサイト（複数ページ）", "30,000円〜")],
        "notes": [
            "EC（決済・カート）、会員登録・ログイン機能を含むサイトは対応しておりません",
            "基本料金に含むページ数の目安は5ページ程度まで（超過分は追加ページ料金）",
            "ドメイン・サーバー費用はお客様負担です（取得・設定のご相談は可能）",
            "テキスト・画像などの素材はお客様にご用意いただきます",
            "納期目安：ご依頼内容の確定後、約2〜3週間",
        ],
    },
    "社内ツール開発": {
        "list": [
            "Google Apps Script（GAS）による業務自動化ツールの開発",
            "バーコードを使った在庫管理システム",
            "転記・集計・通知・顧客管理などの手作業の自動化",
            "フォーム入力から記録・文章を自動作成（生成AI込み）",
            "LINE連携（通知・簡易な問い合わせ対応など）",
            "ちょっとしたGASスクリプトの単体作成（入口プラン）",
        ],
        "steps": [
            "ヒアリング｜今の作業の流れ・困りごと・理想の状態を伺います。曖昧なご相談も歓迎です",
            "仕様のご提案｜できること・できないことを明確にしてから開始します",
            "開発・動作確認",
            "実際の業務データでのテスト運用",
            "納品・簡単な使い方説明",
        ],
        "strengths": [
            "データはお客様のGoogleアカウント内 — 外部にデータを預ける一般的なSaaSより、管理面で安心です",
            "一歩進んだ自動化 — 生成AIが記録用の文章まで自動作成。同カテゴリでは珍しい対応です",
            "月額利用料なし — GASは追加費用なしで動作するため、ランニングコストがかかりません",
        ],
        "plans": [
            ("入口：GASスクリプト単体作成", "5,000円〜"),
            ("本命：業務ツール一式", "30,000円〜"),
            ("本格システム（要相談）", "300,000円〜"),
        ],
        "notes": [
            "EC（決済・カート）、会員登録・ログイン機能を含むシステムは対応しておりません",
            "内容により難易度・工数が大きく変わるため、まずは無料相談を推奨します",
            "Googleアカウントの操作（共有設定など）にご協力いただく場合があります",
            "納期目安：内容により1〜3週間程度",
        ],
    },
}

SLUG = {"LP制作": "LP制作", "ホームページ制作": "HP制作", "社内ツール開発": "社内ツール"}

if __name__ == "__main__":
    for svc, c in DATA.items():
        s = SLUG[svc]
        save(slide_list(svc, c["list"]), f"詳細_{s}_2_できること.png")
        save(slide_steps(svc, c["steps"]), f"詳細_{s}_3_進め方.png")
        save(slide_strengths(svc, c["strengths"]), f"詳細_{s}_4_強み.png")
        save(slide_price_notes(svc, c["plans"], c["notes"]), f"詳細_{s}_5_料金と注意.png")

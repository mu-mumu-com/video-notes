#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
video_transcript.py  <動画URL>

動画URLから文字起こしテキストを取り出して、JSONで標準出力に返す。
  1. yt-dlp で字幕を取得（手動字幕 → 自動字幕 の順で ja / en を優先）
  2. 字幕が無ければ音声だけDLして faster-whisper でローカル文字起こし
  3. (Instagramのみ) yt-dlpが動画として取得できない場合、instaloaderで
     画像投稿(カルーセル含む)のキャプション＋画像、または動画を取得する

出力(JSON) 動画の場合:
{
  "ok": true,
  "type": "video",
  "title": "...",
  "url": "...",
  "platform": "youtube",
  "source": "subtitle" | "whisper",
  "lang": "ja",
  "transcript": "..."
}

出力(JSON) Instagram画像投稿の場合:
{
  "ok": true,
  "type": "image_post",
  "title": "...",
  "url": "...",
  "platform": "instagram",
  "source": "caption",
  "lang": "ja",
  "transcript": "<キャプション本文>",
  "images": ["/絶対パス/1.jpg", "/絶対パス/2.jpg", ...]
}
images は保存先のローカル絶対パス。Readツール等で画像そのものを目視確認できる。

必要ツール:
  - yt-dlp        (pip install yt-dlp)
  - ffmpeg        (brew install ffmpeg)   ※音声フォールバック時のみ
  - faster-whisper(pip install faster-whisper) ※字幕が無い動画のときだけ
  - instaloader   (pip install instaloader) ※Instagramの画像投稿フォールバック時のみ
環境変数:
  - WHISPER_MODEL   … faster-whisper のモデル名 (既定: small)
                      精度優先なら medium、速度優先なら base
"""

import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

DOWNLOADS_DIR = Path.home() / "開発" / "video-notes" / "_bin" / "downloads"


def eprint(*a):
    print(*a, file=sys.stderr, flush=True)


def fail(msg):
    print(json.dumps({"ok": False, "error": msg}, ensure_ascii=False))
    sys.exit(1)


def run(cmd, **kw):
    """コマンド実行。戻り値 (returncode, stdout, stderr)。"""
    p = subprocess.run(cmd, capture_output=True, text=True, **kw)
    return p.returncode, p.stdout, p.stderr


def find_ytdlp():
    """yt-dlp の実行パス。

    venv を activate せず venv/bin/python を直接呼ぶと venv/bin は PATH に入らない。
    まず自分と同じ bin/ を見て、無ければ PATH 上の yt-dlp に委ねる。
    """
    local = Path(sys.executable).parent / "yt-dlp"
    return str(local) if local.exists() else "yt-dlp"


YTDLP = find_ytdlp()


class MetaFetchError(Exception):
    """yt-dlpでメタデータ/動画情報が取得できなかったときに投げる。"""


# --------------------------------------------------------------------------
# メタデータ取得
# --------------------------------------------------------------------------
def get_meta(url):
    code, out, err = run([YTDLP, "--dump-single-json", "--skip-download",
                          "--no-warnings", url])
    # Instagramのカルーセル投稿等は、個々のスライドが動画フォーマットを
    # 持たずエラー終了(code!=0)することがあるが、投稿自体のJSONは
    # stdoutに出力されていることがあるので、まずパースを試みる。
    try:
        info = json.loads(out)
    except json.JSONDecodeError:
        info = None
    if not isinstance(info, dict):
        raise MetaFetchError(
            "動画情報を取得できませんでした。URLが正しいか、yt-dlpが最新か確認してください。\n" + err.strip()[:500])
    entries = info.get("entries")
    has_real_entries = bool(entries) and any(e for e in entries)
    if code != 0 and "formats" not in info and not has_real_entries:
        raise MetaFetchError(
            "動画情報を取得できませんでした。URLが正しいか、yt-dlpが最新か確認してください。\n" + err.strip()[:500])
    title = info.get("title") or info.get("id") or "untitled"
    vid = info.get("id") or "video"
    platform = (info.get("extractor_key") or info.get("extractor") or "web").lower()
    return title, vid, platform


# --------------------------------------------------------------------------
# 字幕の取得
# --------------------------------------------------------------------------
SUB_LANGS = "ja,ja-JP,ja-orig,en,en-US,en-orig,ja.*,en.*"


def try_subs(url, tmpdir, auto=False):
    """字幕を取得。取得できたら vtt ファイルパスを返す。無ければ None。"""
    flag = "--write-auto-subs" if auto else "--write-subs"
    outtmpl = str(Path(tmpdir) / "%(id)s.%(ext)s")
    cmd = [YTDLP, "--skip-download", flag,
           "--sub-langs", SUB_LANGS, "--sub-format", "vtt/best",
           "--no-warnings", "-o", outtmpl, url]
    run(cmd)  # 失敗しても vtt が無いだけなので戻り値は見ない
    vtts = sorted(Path(tmpdir).glob("*.vtt"))
    if not vtts:
        return None, None
    # ja を優先、次に en
    def score(p):
        n = p.name.lower()
        if ".ja" in n:
            return 0
        if ".en" in n:
            return 1
        return 2
    vtts.sort(key=score)
    best = vtts[0]
    lang = "ja" if ".ja" in best.name.lower() else ("en" if ".en" in best.name.lower() else "?")
    return best, lang


TAG_RE = re.compile(r"<[^>]+>")            # <c>, <00:00:01.000> などのタグ
CUE_RE = re.compile(r"^\d+$")               # 連番のキュー番号
TIME_RE = re.compile(r"-->")                # タイムコード行
HEADER_RE = re.compile(r"^(WEBVTT|Kind:|Language:|NOTE)")


def vtt_to_text(path):
    """VTTをプレーンテキストへ。YouTube自動字幕の重複行も畳む。"""
    lines = Path(path).read_text(encoding="utf-8", errors="ignore").splitlines()
    out = []
    last = None
    for raw in lines:
        s = raw.strip()
        if not s or HEADER_RE.match(s) or TIME_RE.search(s) or CUE_RE.match(s):
            continue
        s = TAG_RE.sub("", s).strip()
        # HTMLエンティティの簡易復元
        s = (s.replace("&nbsp;", " ").replace("&amp;", "&")
              .replace("&lt;", "<").replace("&gt;", ">").replace("&#39;", "'"))
        if not s or s == last:
            continue
        # 直前の行の末尾と重複する“ローリング字幕”を軽く除去
        if last and last.endswith(s):
            continue
        out.append(s)
        last = s
    text = "\n".join(out)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text


# --------------------------------------------------------------------------
# 音声フォールバック（faster-whisper）
# --------------------------------------------------------------------------
class AudioFetchError(Exception):
    """音声ダウンロードに失敗したときに投げる。"""


def download_audio(url, tmpdir):
    outtmpl = str(Path(tmpdir) / "audio.%(ext)s")
    cmd = [YTDLP, "-f", "bestaudio/best", "-x", "--audio-format", "mp3",
           "--no-warnings", "-o", outtmpl, url]
    code, out, err = run(cmd)
    audios = list(Path(tmpdir).glob("audio.*"))
    if code != 0 or not audios:
        raise AudioFetchError(
            "音声のダウンロードに失敗しました。ffmpegが入っているか確認してください。\n" + err.strip()[:500])
    return str(audios[0])


def whisper_transcribe(audio_path):
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        fail("字幕が無い動画でした。文字起こしには faster-whisper が必要です。\n"
             "  pip install faster-whisper   を実行してください。")
    model_name = os.environ.get("WHISPER_MODEL", "small")
    eprint(f"[whisper] モデル {model_name} で文字起こし中…（初回はモデルDLで時間がかかります）")
    model = WhisperModel(model_name, device="cpu", compute_type="int8")
    segments, info = model.transcribe(audio_path, vad_filter=True)
    lang = info.language if info and info.language else "?"
    text = "".join(seg.text for seg in segments).strip()
    if not text:
        fail("文字起こし結果が空でした。動画に音声が無い可能性があります。")
    return text, lang


# --------------------------------------------------------------------------
# Instagram画像投稿フォールバック（instaloader）
# yt-dlpが動画として取得できないとき（カルーセル・静止画投稿）に使う。
# --------------------------------------------------------------------------
IG_SHORTCODE_RE = re.compile(r"instagram\.com/(?:[^/]+/)?(?:p|reel|reels|tv)/([A-Za-z0-9_-]+)")


def instaloader_flow(url):
    """Instagram投稿をinstaloaderで取得。動画として扱えなければNoneを返す。"""
    m = IG_SHORTCODE_RE.search(url)
    if not m:
        return None
    shortcode = m.group(1)

    try:
        import instaloader
    except ImportError:
        eprint("[info] instaloaderが無いため画像投稿フォールバックをスキップします。"
               " pip install instaloader で導入できます。")
        return None

    try:
        L = instaloader.Instaloader(quiet=True, download_video_thumbnails=False,
                                     save_metadata=False, download_comments=False,
                                     post_metadata_txt_pattern="")
        post = instaloader.Post.from_shortcode(L.context, shortcode)
    except Exception as e:
        eprint(f"[info] instaloaderでの投稿取得に失敗しました: {e}")
        return None

    caption = post.caption or ""
    owner = post.owner_username or "unknown"
    title = f"Post by {owner}"
    outdir = DOWNLOADS_DIR / shortcode
    outdir.mkdir(parents=True, exist_ok=True)

    def save(remote_url, dest):
        resp = L.context.get_raw(remote_url)
        dest.write_bytes(resp.content)

    try:
        if post.typename == "GraphSidecar":
            images = []
            skipped_video_slides = 0
            for i, node in enumerate(post.get_sidecar_nodes(), start=1):
                if node.is_video:
                    skipped_video_slides += 1
                    continue
                dest = outdir / f"{shortcode}_{i}.jpg"
                save(node.display_url, dest)
                images.append(str(dest))
            if skipped_video_slides:
                eprint(f"[info] カルーセル内の動画スライド{skipped_video_slides}件は未対応のためスキップしました。")
            return {
                "ok": True,
                "type": "image_post",
                "title": title,
                "url": url,
                "platform": "instagram",
                "source": "caption",
                "lang": "ja",
                "transcript": caption,
                "images": images,
            }
        elif post.typename == "GraphVideo":
            # 動画投稿だがyt-dlpが取得できなかったケース。動画を落としてwhisperにかける。
            dest = outdir / f"{shortcode}.mp4"
            save(post.video_url, dest)
            transcript, lang = whisper_transcribe(str(dest))
            return {
                "ok": True,
                "type": "video",
                "title": title,
                "url": url,
                "platform": "instagram",
                "source": "whisper",
                "lang": lang,
                "transcript": transcript,
            }
        else:  # GraphImage: 単一の写真投稿
            dest = outdir / f"{shortcode}_1.jpg"
            save(post.url, dest)
            return {
                "ok": True,
                "type": "image_post",
                "title": title,
                "url": url,
                "platform": "instagram",
                "source": "caption",
                "lang": "ja",
                "transcript": caption,
                "images": [str(dest)],
            }
    except Exception as e:
        eprint(f"[info] instaloaderでのダウンロードに失敗しました: {e}")
        return None


# --------------------------------------------------------------------------
# メイン
# --------------------------------------------------------------------------
def main():
    if len(sys.argv) < 2 or not sys.argv[1].strip():
        fail("使い方: video_transcript.py <動画URL>")
    url = sys.argv[1].strip()

    # yt-dlp があるか
    if run([YTDLP, "--version"])[0] != 0:
        fail("yt-dlp が見つかりません。 pip install yt-dlp を実行してください。")

    is_instagram = "instagram.com" in url.lower()

    try:
        title, vid, platform = get_meta(url)
    except MetaFetchError as e:
        if is_instagram:
            eprint("[info] yt-dlpでの動画取得に失敗したため、画像投稿として再試行します。")
            result = instaloader_flow(url)
            if result is not None:
                print(json.dumps(result, ensure_ascii=False))
                return
        fail(str(e))

    with tempfile.TemporaryDirectory() as tmp:
        # 1) 手動字幕
        sub, lang = try_subs(url, tmp, auto=False)
        source = "subtitle"
        # 2) 自動字幕
        if sub is None:
            sub, lang = try_subs(url, tmp, auto=True)
        # 3) 音声フォールバック
        if sub is None:
            eprint("[info] 字幕が見つからないため、音声から文字起こしします。")
            try:
                audio = download_audio(url, tmp)
            except AudioFetchError as e:
                if is_instagram:
                    eprint("[info] 動画としての取得に失敗したため、画像投稿として再試行します。")
                    result = instaloader_flow(url)
                    if result is not None:
                        print(json.dumps(result, ensure_ascii=False))
                        return
                fail(str(e))
            transcript, lang = whisper_transcribe(audio)
            source = "whisper"
        else:
            transcript = vtt_to_text(sub)
            if len(transcript) < 20:
                eprint("[info] 字幕が短すぎたため、音声から文字起こしします。")
                try:
                    audio = download_audio(url, tmp)
                except AudioFetchError as e:
                    if is_instagram:
                        eprint("[info] 動画としての取得に失敗したため、画像投稿として再試行します。")
                        result = instaloader_flow(url)
                        if result is not None:
                            print(json.dumps(result, ensure_ascii=False))
                            return
                    fail(str(e))
                transcript, lang = whisper_transcribe(audio)
                source = "whisper"

    print(json.dumps({
        "ok": True,
        "type": "video",
        "title": title,
        "url": url,
        "platform": platform,
        "source": source,
        "lang": lang,
        "transcript": transcript,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()

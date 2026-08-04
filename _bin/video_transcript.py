#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
video_transcript.py  <動画URL>

動画URLから文字起こしテキストを取り出して、JSONで標準出力に返す。
  1. yt-dlp で字幕を取得（手動字幕 → 自動字幕 の順で ja / en を優先）
  2. 字幕が無ければ音声だけDLして faster-whisper でローカル文字起こし

出力(JSON):
{
  "ok": true,
  "title": "...",
  "url": "...",
  "platform": "youtube",
  "source": "subtitle" | "whisper",
  "lang": "ja",
  "transcript": "..."
}

必要ツール:
  - yt-dlp        (pip install yt-dlp)
  - ffmpeg        (brew install ffmpeg)   ※音声フォールバック時のみ
  - faster-whisper(pip install faster-whisper) ※字幕が無い動画のときだけ
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


# --------------------------------------------------------------------------
# メタデータ取得
# --------------------------------------------------------------------------
def get_meta(url):
    code, out, err = run([YTDLP, "--dump-single-json", "--skip-download",
                          "--no-warnings", url])
    if code != 0:
        fail("動画情報を取得できませんでした。URLが正しいか、yt-dlpが最新か確認してください。\n" + err.strip()[:500])
    try:
        info = json.loads(out)
    except json.JSONDecodeError:
        fail("動画情報の解析に失敗しました。")
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
def download_audio(url, tmpdir):
    outtmpl = str(Path(tmpdir) / "audio.%(ext)s")
    cmd = [YTDLP, "-f", "bestaudio/best", "-x", "--audio-format", "mp3",
           "--no-warnings", "-o", outtmpl, url]
    code, out, err = run(cmd)
    audios = list(Path(tmpdir).glob("audio.*"))
    if code != 0 or not audios:
        fail("音声のダウンロードに失敗しました。ffmpegが入っているか確認してください。\n" + err.strip()[:500])
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
# メイン
# --------------------------------------------------------------------------
def main():
    if len(sys.argv) < 2 or not sys.argv[1].strip():
        fail("使い方: video_transcript.py <動画URL>")
    url = sys.argv[1].strip()

    # yt-dlp があるか
    if run([YTDLP, "--version"])[0] != 0:
        fail("yt-dlp が見つかりません。 pip install yt-dlp を実行してください。")

    title, vid, platform = get_meta(url)

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
            audio = download_audio(url, tmp)
            transcript, lang = whisper_transcribe(audio)
            source = "whisper"
        else:
            transcript = vtt_to_text(sub)
            if len(transcript) < 20:
                eprint("[info] 字幕が短すぎたため、音声から文字起こしします。")
                audio = download_audio(url, tmp)
                transcript, lang = whisper_transcribe(audio)
                source = "whisper"

    print(json.dumps({
        "ok": True,
        "title": title,
        "url": url,
        "platform": platform,
        "source": source,
        "lang": lang,
        "transcript": transcript,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()

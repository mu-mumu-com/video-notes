---
title: Claude CodeからCodexの画像生成を呼び出す方法
url: https://www.instagram.com/reel/Ddaji8jTQ5V/?stkn=MWtudDZjcWRjeXBsMw==
platform: instagram
genre: AIツール
date: 2026-09-23
source: whisper
tags: [ClaudeCode, Codex, 画像生成]
---

# Claude CodeからCodexの画像生成を呼び出す方法

## ひとことで
OpenAI公式のCodex連携プラグインと画像生成専用プラグインを組み合わせ、Claude Codeから日本語で頼むだけでCodex経由の画像生成ができるようになる設定方法。

## 手順 / やり方
1. Codex CLI連携プラグイン（Claude Code用）を導入する
2. 画像生成専用プラグイン（codex-image系）を追加する。これで画像生成コマンドが使えるようになる
3. Claude Codeに「この画像を作ってここに保存して」と日本語で頼むだけで、Codex経由の画像生成結果がClaude Code側で確認できる

## 要点メモ
- APIキーは不要、追加費用もかからない（ChatGPTプランに含まれる範囲で動作）
- 実演では1分もかからずに画像が生成された

## 信憑性・再現性
- 信憑性: 高い — WebSearchで実在を確認。`codex-image-in-cc`、`Codex-ImageGen--Claude-Code`など複数の実装がGitHub上に公開されている。前提として `@openai/codex` CLI v0.142.0以降、Node.js 18.18以降、Codexへのログインセッションが必要
- 再現性: 高い — 導入手順が具体的で、無料（ChatGPTプランの範囲内）

## 思考パーツ・自分ごと化
- 保存メリット: 薄い（手順そのものが価値）
- 取り入れた方がいい部分: 画像生成が必要な案件（バナー等）でAPIキー管理をせずに使える選択肢として、実際に導入して試す

## 元URL
https://www.instagram.com/reel/Ddaji8jTQ5V/?stkn=MWtudDZjcWRjeXBsMw==

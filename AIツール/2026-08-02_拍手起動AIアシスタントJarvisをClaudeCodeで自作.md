---
title: 拍手起動の音声AIアシスタント「Jarvis」をClaude Codeで自作する
url: https://www.instagram.com/reel/DbdG70ZPQIx/?igsh=NndyOWEwMXJvZzdv
platform: instagram
genre: AIツール
date: 2026-08-02
source: whisper
tags: [Claude Code, 音声アシスタント, 自動化, AIエージェント]
---

# 拍手起動の音声AIアシスタント「Jarvis」をClaude Codeで自作する

## ひとことで
拍手2回で起動する音声操作AIアシスタント「Jarvis」を、Claude Codeベースで自作する方法の紹介。動画自体はDM誘導だが、同様の構成はGitHubに複数の実装例が公開されている。

## 手順 / やり方
1. 専用のプロジェクトフォルダを作成する
2. AIエージェント（Claude Codeなど）に構築用のプロンプトを渡す
3. AIからの質問（環境設定など）に答えて実装を完了させる
4. 拍手2回+「ジャービス」で起動、話しかけて操作（YouTube検索・文字起こし、Googleカレンダー確認など）
5. 「閉じて」で待機状態に戻せる

## 要点メモ
- 動画内では実際のプロンプトは非公開（コメント+DMでのみ配布）
- 同様の構成はGitHubに実装例が複数公開されている
  - Julian-Ivanov/jarvis-voice-assistant（double-clap起動、ブラウザ操作・画面キャプチャ込み、Claude Code製）
  - civitas-cerebrum/jarvis-plugin（ローカル完結の音声プラグイン）
  - viamus/jarvis-cli（faster-whisperによる音声認識ミドルウェア）
- いずれもローカル完結・オフライン動作を謳うものが多い

## 信憑性・再現性
- 信憑性: 普通 — AIエージェント構築自体は技術的に妥当。動画本体の主張に誇張はない
- 再現性: 高い（動画外の情報を含めると）— DMを待たなくても、上記GitHubリポジトリを参照すれば同等のものを自作できる

## 元動画
https://www.instagram.com/reel/DbdG70ZPQIx/?igsh=NndyOWEwMXJvZzdv

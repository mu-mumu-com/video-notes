---
title: Obsidian×Claude Codeで会社の脳を作りAI社員を量産
url: https://www.instagram.com/reel/DcTSZ81z9Y6/?igsi=NGk1b2hraTlleXh6
platform: instagram
genre: AIツール
date: 2026-08-22
source: whisper
tags: [Claude Code, Obsidian, マルチエージェント, セカンドブレイン]
---

# Obsidian×Claude Codeで会社の脳を作りAI社員を量産

## ひとことで
Obsidian（無料メモアプリ）を「会社の共有記憶（セカンドブレイン）」として使い、Claude Codeで業務特化のAIエージェントを何人でも量産する手法。

## 手順 / やり方
1. Obsidianで新規フォルダを1つ作り、これを「会社の脳」とする
2. その中にホルダー（サブフォルダ）を1つ用意する
3. Claude Codeに「〇〇のAI社員を作って」と頼む。既に作った第二の脳（共有記憶）に接続されるため、新規エージェントでも過去の重要な開発内容を引き継げる
4. さらに業務特化させたい場合は「〇〇業務特化のエージェントを作りたいからMD作って」と頼むと、その業務専用のエージェント定義（MDファイル）ができる
5. 会社の説明（コンテキスト）は最初の1回だけで済み、以降のエージェント作成では再入力不要

## 要点メモ
- 手順1〜3までは誰がやっても同じ汎用エージェントになるため、差別化は手順4の「業務特化MD」の作り込みにかかっている
- Obsidianのvaultはただのmarkdownフォルダなので、Claude Codeがそのままファイルとして読み書きできる（API連携不要）

## 信憑性・再現性
- 信憑性: 高い — Obsidian + Claude Codeを「セカンドブレイン」として使う手法は、複数の技術ブログ・GitHubプロジェクト（obsidian-second-brain、claude-obsidian等）で広く実践されている実在のワークフロー。CLAUDE.md/memory.mdを軸に記憶を構造化する構成が一般的で、動画の説明と整合する。
- 再現性: 高い — Obsidian・Claude Codeともに既存ツール（前者は無料）で追加コストなし。具体的なプロンプト文言はやや曖昧（「〇〇のAI社員を作って」レベル）だが、大枠の技術・手順は今すぐ試せる。

## 思考パーツ・自分ごと化
- 保存メリット: りかちゃん（秘書エージェント）のマルチエージェント設計に直結する発想。「1つの共有記憶（会社の脳）に、複数の業務特化エージェントが接続する」という構造がそのまま応用できる。
- 取り入れた方がいい部分: りかちゃんの記憶をObsidian Vault（フォルダ）として構造化し、新しい業務特化エージェントを作るときは既存Vaultに接続する形にする。CLAUDE.md的な「最初の説明だけ書けば以降は引き継がれる」設計を意識する。

## 元URL
https://www.instagram.com/reel/DcTSZ81z9Y6/?igsi=NGk1b2hraTlleXh6

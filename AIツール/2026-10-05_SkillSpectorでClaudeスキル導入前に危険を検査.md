---
title: SkillSpectorでClaudeスキル導入前に危険を検査
url: https://www.instagram.com/reel/DdbEFx9Brhr/
platform: instagram
genre: AIツール
date: 2026-10-05
source: whisper
tags: [ClaudeCode, セキュリティ, スキル, NVIDIA]
---

# SkillSpectorでClaudeスキル導入前に危険を検査

## ひとことで
Claudeのスキルをそのまま入れるのは危険。NVIDIA公開の無料スキャナ「SkillSpector」で、入れる前に悪意のあるコードを検査する。

## 手順 / やり方
1. インストール（公式README確認済み、Python 3.12以上）: `uv tool install git+https://github.com/NVIDIA/skillspector.git`（uvが無ければ3.12のvenvに`pip install git+https://github.com/NVIDIA/skillspector.git`）
2. 検査: `skillspector scan <スキルのフォルダ or GitHubのURL>`。AI(LLM)なしの静的解析だけなら`--no-llm`
3. 0〜100点で返る。0-20 安全 / 21-50 注意 / 51-80 入れるな / 81-100 入れるな(重大)。危険箇所も出る
4. 「スキルを入れる時は必ずスキャンして」とClaudeに覚えさせると以後自動で検査

## 要点メモ
- 出回っているスキルの20本に1本は悪質とされる
- 使ってしまってからでは遅いので事前検査

## 信憑性・再現性
- 信憑性: 高い — NVIDIA/SkillSpectorは実在。約3.1万スキルの調査で26.1%に脆弱性、5.2%に悪意の疑い（動画の「20本に1本」と一致）
- 再現性: 高い — 無料で手順も短い。51点以上＝入れるな、は公式READMEで確認済み

## 思考パーツ・自分ごと化
- 保存メリット: 普通 — 「入れる前に検査する」習慣として
- 取り入れた方がいい部分: 外部スキルを新しく入れる前に必ずこのスキャナを通す

## 元URL
https://www.instagram.com/reel/DdbEFx9Brhr/

## 追記(2026-10-05 検証)
- 根拠論文: Liu et al. 2026 "Agent Skills in the Wild"。42,447件中31,132件を分析し、26.1%に脆弱性、5.2%に悪意の疑い。実行スクリプト付きは脆弱な確率が約2.12倍
- 「悪意の疑い」は静的解析＋AI判定による推定で、確定した悪意ではない。ただ「スクリプト付きの外部スキルは慎重に」は妥当
- 未導入: 自動モードの権限で、GitHubからのインストールがブロックされたため、まだ入れていない
- 導入済み(2026-10-05): `~/開発/video-notes/_bin/skillspector-venv/bin/skillspector scan <パス> --no-llm`
- 公式プラグインのスキャン結果(静的のみ): frontend-design 13点、skill-creator 84、superpowers 100、discord 100、vercel 100。大型プラグインは依存一覧や指示文を大量に拾って高得点になりやすく、解析も一部失敗(degraded)。個別の検出は未精査＝危険の確定ではない。小さな個人製スキルの検査向き

---
title: Video by itota.design
url: https://www.instagram.com/reel/Dbs28uYTW50/?igsh=MWgxZzlwOXBwcm01cA==
platform: instagram
genre: SNS運用
date: 2026-08-07
source: whisper
tags: [AI活用, SNS分析, Claude, プロンプト]
---

# ClaudeとInstagramを連携してアカウント分析

## ひとことで
Claudeにコネクタ経由でInstagramアカウントを接続し、指定プロンプトで投稿分析・30日間の投稿プランまで自動生成させる方法を紹介する動画。

## 手順 / やり方
1. Claudeを開き「コネクト」からInstagram連携ツール（動画内の聞き取りは「スーパーマトリックス」だったが、後日調査でおそらく実在サービス「Supermetrics」の聞き間違いと判明）を接続する
2. Instagramアカウントと接続する
3. 概要欄記載のプロンプトをチャットに貼って実行する（人気投稿ランキング・インサイトまとめ・オーディエンス分析・30日間の投稿プランを生成）

実際に試す場合の裏取り済み条件（2026-08-07調査）:
- Porter Metrics / Windsor.ai / Supermetrics / Adzviser / Data BlooなどのMCPコネクタで実現可能（Claude.aiの「コネクタを管理」からカスタム/公式コネクタを追加）
- **Instagramのビジネス/クリエイターアカウントが必須**（個人アカウントはInsights APIにアクセスできず不可）
- Meta公式のOAuth認証で連携。多くは読み取り専用で自動投稿等は行わない
- 無料枠があるものが多いが、詳細分析は有料プラン誘導のケースもある

## 要点メモ
- 肝心のプロンプトと連携ツールの詳細は動画外の「概要欄」頼みで、動画単体では完結していない
- 同種の手法を紹介する動画が他に複数あり（#alien_sabo、#misawo0930）、2026年8月時点でのトレンドと見られる
- 手法自体はWeb検索で裏取り済み・実在する（下記ソース）

## 信憑性・再現性
- 信憑性: 高い — ClaudeにMCP経由でInstagram Insightsを接続して分析させる仕組みは実在の第三者サービス複数（Porter Metrics等）で確認済み
- 再現性: 普通 — ビジネス/クリエイターアカウントであれば、上記条件で自分でも再現可能。動画自体は情報不足だが、外部調査で補完できた

## 思考パーツ・自分ごと化
- 保存メリット: 「AI(Claude等)に自社SNSの投稿データを渡して、伸びた投稿の共通点や改善点を定量分析させる」という発想は、momemoのポートフォリオ導線改善やてだこナビの効果測定にも転用できそう
- 取り入れた方がいい部分: momemoやSNS運用アカウントがビジネス/クリエイターアカウントであれば、Porter Metrics等のMCPコネクタを試して実際にAI分析を回してみる

## 参考ソース（裏取り）
- https://portermetrics.com/en/tutorial/claude/chat-instagram/
- https://portermetrics.com/en/connectors/claude/instagram/
- https://windsor.ai/how-to-connect-instagram-insights-to-claude/
- https://adzviser.com/connect/instagram-insights-to-claude-integration

## 元動画
https://www.instagram.com/reel/Dbs28uYTW50/?igsh=MWgxZzlwOXBwcm01cA==

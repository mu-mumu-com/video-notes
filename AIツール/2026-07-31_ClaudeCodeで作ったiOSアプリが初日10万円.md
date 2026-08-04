---
title: Claude Codeだけで作ったiOSアプリ、リリース初日に10万円売れました【サブスクBox】
url: https://youtu.be/r59VWUegxW4?si=7TLhlPM6ce1IfPsJ
platform: youtube
genre: AIツール
date: 2026-07-31
source: subtitle
tags: [ClaudeCode, iOSアプリ, Expo, 個人開発]
---

# Claude Codeで作ったiOSアプリが初日10万円

## ひとことで
Claude Codeだけでコーディングしたサブスク管理アプリが、X(旧Twitter)でバズって初日10万円を売り上げた開発記録と考え方。

## 手順 / やり方
1. フロントエンドはExpo(React Nativeのフレームワーク)を使用。iOS/Android両対応、Windows環境からでもiOS申請ができる
2. バックエンドは使わず、データはExpo SQLiteで端末内にローカル保存(プライバシー面でも安全、複数端末同期はしない設計)
3. 課金機能はRevenueCatで実装(自前実装は大変なため既存サービスに任せる)
4. 分析はPostHogを導入し、MCPサーバー経由でClaude Codeと連携してユーザー行動を分析
5. App Store申請もApple Store MCPサーバーを使いClaude Codeにほぼ任せる。プレビュー用スクリーンショットのみChatGPTの画像生成で自作
6. 開発前に「逆算思考」で進める: ゴール金額を具体的にイメージ→必要ダウンロード数を逆算→世の中のトレンドや日常の「小さなイライラ(マイクロフラストレーション)」からアイデアを探す

## 要点メモ
- Apple審査の手数料は売上の30%(中小企業向け申請をすれば15%に軽減可能)
- 実績: ファイナンスランキング1位、全体ランキング一時4位、31,000ダウンロード、売上約17〜18万円(初日約10万円、その後は1日1万円未満に減少)
- 「開発」より「Apple審査に出す準備」の方が時間がかかるケースが多い
- 目標を具体的にイメージすることが逆算思考の起点になるという話は、本人も「スピリチュアルな話」と前置きしており、目標設定の心理的効果として捉えるのが妥当

## 元動画
https://youtu.be/r59VWUegxW4?si=7TLhlPM6ce1IfPsJ

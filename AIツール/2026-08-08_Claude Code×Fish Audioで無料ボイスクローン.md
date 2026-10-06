---
title: Claude Code×Fish Audioで無料ボイスクローン
url: https://www.instagram.com/reel/DbvKejqTemj/?igsh=N3kzMzB1MmI1eGNq
platform: instagram
genre: AIツール
date: 2026-08-08
source: whisper
tags: [Claude Code, Fish Audio, ボイスクローン, 音声AI]
---

# Claude Code×Fish Audioで無料ボイスクローン

## ひとことで
Claude CodeとFish AudioのS2.1 Proモデルを組み合わせて、無料枠内で自分の声のボイスクローンを作る方法。

## 手順 / やり方
1. Googleで「Fish Audio Coding Agents」を検索し、一番上のリンク（公式ドキュメント: docs.fish.audio/developer-guide/resources/coding-agents）を開く
2. 出てきたセットアップ用コードをClaude Codeに貼って実行
3. 「Fish Audio APIキー」で検索し、APIキーを無料発行する
4. 発行したAPIキーもClaude Codeに貼る
5. 自分の声を15秒分アップロードし、「この音声のクローンを作って」と指示する

## 要点メモ
- Fish AudioのS2.1 Proは2026年6月時点でFair Use下の無料TTS APIとして公式提供されている（モデル名 `s2.1-pro-free`、クレカ登録不要、ハード上限なし）
- 料金プラン（2026年時点）: Free（月7分程度、基本的なボイスクローン含む、API利用不可）/ Plus 月$11〜（API利用込み・25万クレジット/月）/ Pro 月$75〜（200万クレジット/月）/ Enterprise
- 通常のFreeプラン（クレジット制）は「個人・非商用利用のみ、商用利用は有料プラン必須」と公式が明言。**S2.1 Pro無料APIも「これは初期期間限定の無料公開であり、条件変更時は事前告知する」と明記されており、いつまで続くか保証はない**
- 商用ライセンス・SLA保証は公式ブログ上「有料プラン（本番運用向け）」の扱いになっており、**S2.1 Pro無料枠での商用利用（収益化動画・クライアント案件）が正式に許諾されているかはグレー**。テスト・プロトタイプ用途は問題ないが、本業で継続利用するなら有料プラン(Plus以上)への切り替えを検討すべき
- 動画内の詳細な手順（Claude Codeに貼るコードの中身）自体は開示されておらず、コメント欄で「クローン」と送ると別途詳細ガイドが届く仕組み（フォロー誘導込み）

## 信憑性・再現性
- 信憑性: 高い — WebSearchで確認、S2.1 Proの無料API提供、AI Coding Agents向け公式ドキュメントの実在、15秒サンプルでのクローン仕様、いずれもFish Audio公式情報と一致。ただし動画の「実質無料」という表現は、期間限定性・商用利用のグレーさに触れていない点でやや楽観的
- 再現性: 普通 — 大まかな流れは正しいが、Claude Codeに貼る実際のセットアップコードが動画内で示されておらず、この動画単体では最後まで再現しきれない（公式ドキュメントページに直接アクセスすれば代替可能）

## 思考パーツ・自分ごと化
- 保存メリット: 中程度 — 「無料枠のあるAPIをコーディングエージェントに直接繋いで使う」という組み合わせ方は、他のAPI活用にも応用できる視点
- 取り入れた方がいい部分: docs.fish.audio/developer-guide/resources/coding-agents を実際に開き、Claude Codeとの連携コードを取得して試してみる

## 元動画
https://www.instagram.com/reel/DbvKejqTemj/?igsh=N3kzMzB1MmI1eGNq

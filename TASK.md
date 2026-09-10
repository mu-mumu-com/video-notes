# りかちゃん・情報収集エージェント構築 作業ログ

設計書: `_secretary/specs/2026-08-19-rika-mentor-secretary-design.md`

## 完了した作業（2026-08-20）

### 1. 基盤ファイル新設
- `_secretary/profile.md`: 関心領域（AIツール活用の探求／個人開発の収益化事例／Web制作・GAS副業拡大）、避けたいこと（EC/会員機能など重い開発案件、バズり系の煽り話）をヒアリングして作成
- `_secretary/ideas.md`: 検討済みアイデア台帳を新設

### 2. クラウドルーティン「りかちゃん 情報収集」拡張（trig_01LY7pundG7KpaBG6XPGxzKu、毎週月曜18:00 JST）
- `profile.md`を参照し、候補ごとに「合いそうか」の一言を追加
- 候補ごとに「おすすめ度: 高/中/低」を付与するよう変更。「高」は毎回0〜1件想定
- 「おすすめ度: 高」の候補だけ、同じセッション内で追加WebSearchし「再現性」「自分に取り入れた方がいい部分」を深く精査する手順（5b）を追加

### 3. ローカルりかちゃん人格（`agent/secretary/CLAUDE.md`）拡張
- profile.md/ideas.mdの読み込みを追加
- 事業アイデアを思いついたら**Agentツール（subagent_type: general-purpose）で調査役に丸ごと委任**し、実現可能性（ツール・費用・難易度・代替手段・情報源）を調べさせる方式に決定・実装
- 「私生活・考え方」セクションとトーン切替（プロジェクト報告=テキパキ／私生活=温かめ）を追加

### 4. `rika-line-bot`（Cloudflare Workers）改修
- 一度は週次・月次通知を「■プロジェクト/ビジネス」「■私生活・考え方」の2セクションAI生成に変更したが、**APIコストがかかる点をユーザーが懸念**したため設計変更
- 最終形: 週次通知はテンプレート方式（AI呼び出しなし、レポート有無＋死活監視のみ）に戻し、research-queue.mdの「おすすめ度: 高」候補だけを**文字列抽出**（AI呼び出しなし）してLINEに1件添える。深い精査結果（再現性・取り入れ方）も同様に抽出して表示
- 月次チェックインは元の`askRikaCheckin`（roadmap/projects限定）のまま維持、今回のコスト見直しの対象外
- デプロイ済み・LINEでの実表示を確認済み（重複アイコン等のバグは修正済み）

### 5. 動作確認テスト（2026-08-20）
- Agentツールでの実現可能性調査委任フローを実際にテスト: 「ig-auto-replyのサブスク型ミニSaaS化」を調査し`ideas.md`に記録
  - 結論: profile.mdの「避けたいこと（EC/会員機能など重い開発案件）」と性質が重なる、Meta App Review審査という非技術的な壁が大きい、既存ノーコードSaaSとの差別化が弱い、という理由で今の強み（AIでの高速開発）が活きにくいと判断し、優先度低いまま保留

## 残タスク・次回への申し送り
- `profile.md`の「大事にしたい価値観」「今わくわくしていること」は意図的に空欄のまま（りかちゃんが対話から気づいたら次回呼び出し時に更新提案する運用）
- `/リサーチ`スキル（`~/.claude/commands/リサーチ.md`）は今回profile.mdと接続していない。手動URL投入フローのため今回のスコープ外で保留
- `ideas.md`の「ig-auto-replyのサブスク型ミニSaaS化」案は「ユーザーの反応」欄が未回答のまま。次にりかちゃんが呼ばれたときに確認するとよい
- 次回の自動収集は2026-08-24(月)、次のLINE通知（週次）は2026-08-21(金)・（月次）は2026-09-01(火)

---

## `/リサーチ`キュー処理・スクリプト修正（2026-09-05）

### 1. `_bin/video_transcript.py` のバグ修正
- `get_meta()`が、yt-dlpが取得失敗時に標準出力へ`null`を返すケースを想定しておらず、`info.get(...)`で`AttributeError`を投げてクラッシュしていた（Instagramの非公開/削除済み投稿URLで発生）
- 修正: `info`が`dict`でない場合（`None`含む）は`MetaFetchError`を送出するよう変更。これによりInstagram URLでの正しいエラーメッセージ返却・instaloaderへのフォールバックが機能するようになった

### 2. キュー処理（GitHub Issue #8, #16, #21〜#27の9件）
- 全件評価・信憑性検証（WebSearchでの裏取り）まで実施し、ユーザーに提示
- 保存: 【Claude Fable 5.1の変更点とYouTubeショッピング副業】(`AIツール/2026-09-05_Claude Fable 5.1の変更点とYouTubeショッピング副業.md`) — 価格・キャッシュコスト削減の数字はAnthropic公式発表と一致確認済み
- 非保存（7件）: 自己啓発・煽り系（根拠不明の統計、有料コンテンツへの誘導）、内容未完結、実績アピールのみで再現性なし、AI検出回避ツール紹介（用途がグレー）等
- issue #8, #16は投稿が非公開/削除済みで取得不可（instaloaderでも失敗）と判明。9件全てのissueをクローズ済み

### 申し送り
- 今後は`/リサーチ`の信憑性評価（手順3）で、具体的な統計・引用・固有名詞が出てきたら省略せず必ずWebSearchで裏取りする方針を徹底する（今回、根拠不明の統計を含む投稿を複数弾けた）

---

## `/リサーチ`キュー処理（2026-09-08）

### 1. キュー処理（GitHub Issue #30, #31）
- **#30** Instagramリール（watanabe_yuta81、21st.dev紹介）: 音声から文字起こし。21st.devの実在・機能・料金をWebSearchで裏取り（無料枠はCopy prompt 1日2回まで、と判明。動画は未言及）。保存 →`AIツール/2026-09-08_フリーランスのLP制作を参考探しから解放する21st.dev.md`
- **#31** Instagram「なるほど図鑑」(@naruhodo_zukan_cha): プロフィールURLのため個別投稿は取得不可。ユーザーが「投稿内容が頭がいい」と評価 → アカウントの型を分解し、AI（Manim＋VOICEVOX）での量産可否を検討してメモ化。保存 →`SNS運用/2026-09-08_なるほど図鑑型の解説ショート動画をAIで量産する副業案.md`
- issue #30・#31 ともクローズ済み

### 2. UIパーツサイトの整理（派生）
- 21st.dev / shadcn/ui / shadcnblocks / Tailwind Plus / Aceternity UI / Magic UI / tweakcn の用途・無料可否・登録要否を一覧化してユーザーに提示（保存はしていない、チャット上の回答のみ）

### 申し送り（次回 2026-09-09）
- ユーザーが「明日続きをやる」と明言。**なるほど図鑑型の解説ショート動画をAIで量産できるか、テスト動画1本を最後まで作って実測する**
  - 題材例:「なぜ風船は手を離すと不規則に飛ぶか」／フロー: Claude台本 → Manimスクリプト → VOICEVOX音声 → テロップ → 書き出し
  - ゴール: 1本あたりの所要時間・詰まりポイントを数値で出し、継続可否を判断（想像で「いけそう」で止めない）
- メモリ: `ai-explainer-shorts-side-business.md` に同内容を記録済み

---

## りかちゃん日次マネージャー化（2026-09-09〜、進行中）

設計書: `_secretary/specs/2026-09-09-rika-daily-manager-design.md`（「2026-09-09 改訂」節が最新）
実装計画＋実行ログ: `_secretary/plans/2026-09-09-rika-daily-manager-plan.md`（末尾「実行ログ」に完了状況）

### 要件（確定）
- 朝7:00/夜21:30 にクラウドルーティンが `_secretary/daily/<日付>.md` 生成、rika-line-bot が 7:20/13:00/21:50 にLINEへ（文字抽出のみ＝0円）。対話返信だけ Claude API。
- **クラウド（LINE朝昼夜）は副業＋プライベートだけ**。本業は `~/SW/work-duties.md`（ローカル）＋iPhoneリマインダーの本業用リスト。Googleカレンダーは接続不可で不使用。
- 本業のリマインド・消化確認は**ローカルでりかちゃんを呼んだ時だけ**。
- 既存の月次チェックイン（`0 9 1 * *`＋`runMonthlyCheckin`）は廃止。
- 本業は月〜金、副業/プライベートは毎日。土日は本業ブロック省略。トーンは「決めてあげる＋励ます」。

### 完了（2026-09-09 夜、無人実行）— Task 0〜9
- bot コード: `mu-mumu-com/agent` の**ブランチ `rika-daily-manager`**（push済み・7コミット・main未マージ）。`npm test` 43 pass、typecheck クリーン。**本番未反映**。
  - 新規: `src/datetime.ts` `daily.ts` `ingest.ts` `ingest-route.ts` ＋各テスト。`github.ts` に `updateFileText`。`scheduled.ts` 全面改稿。`claude.ts` の `askRika` を stable/volatile 分離・`askRikaCheckin` 削除。`wrangler.toml` crons 差し替え。`types.ts` に `INGEST_SECRET`。
- video-notes: `_secretary/agenda.md` `kpi.md` `daily/_TEMPLATE.md`、`profile.md`に「セルフマネジメントの傾向」節、spec/plan。push済み。
- `~/SW/work-duties.md`: 本業の担当業務を記入済み（2026-09-10、ユーザーヒアリング）。都度項目・ニュース担当は未整理、経費入力の時期は要確認。

### 残タスク（ユーザー同席が必要）— Task 10〜13
1. **Task 10 デプロイ**: `INGEST_SECRET` 生成 → `wrangler secret put` → `npm run deploy`（`CLOUDFLARE_API_TOKEN` かユーザーの `! npx wrangler login`）。`/ingest` 本番疎通。
2. **Task 11 クラウドルーティン作成**: 朝(`0 22 * * *`)・夜(`30 12 * * *`)を `RemoteTrigger` で。既存 `env_018JLnu98AphHR6nuD8Md58N` 流用。プロンプトは plan 参照（本業ブロックなし版）。`enabled:false`→試走→目視→有効化。
3. **Task 12 iPhoneショートカット**: `agent/rika-line-bot/SHORTCUT.md` を書く → ユーザーが作成（本業リスト除外）。
4. **Task 13 ローカルりかちゃん**: `agent/secretary/CLAUDE.md` にローカル時の本業ブリーフィング（`~/SW/work-duties.md`＋iPhoneリマインダー全リスト、カレンダーなし）を明記 → memory 更新。ニュース担当・経費入力の時期を詰める。
5. ブランチ `rika-daily-manager` を main にマージ。

### 再開の合図
「**りかちゃん日次マネージャーの続き**」→ plan の「実行ログ」を読んで Task 10 から。

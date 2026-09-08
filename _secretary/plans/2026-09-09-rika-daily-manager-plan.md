# りかちゃん日次マネージャー化 実装計画

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** りかちゃんに朝・昼・夜の日次ブリーフィング（本業/副業/プライベート）と、本業の担当業務（毎日/週次/月次）のリマインド・消化確認、iPhoneリマインダー取り込みを追加する。

**Architecture:** 既存インフラの拡張。朝夜の文章生成は新規クラウドルーティン2本（Claude Codeプラン内、従量課金なし）が `_secretary/daily/<日付>.md` に書く。通知と昼pingと双方向対話は `rika-line-bot`（Cloudflare Workers）が担当（定型pushは文字抽出のみでAPI呼び出しなし、対話返信時だけ Claude API・プロンプトキャッシュ有効）。iPhoneショートカットがリマインダーをbotの `/ingest` に送り `agenda.md` へ蓄積。

**Tech Stack:** Cloudflare Workers + Hono + TypeScript（rika-line-bot）、vitest（新規・純関数のユニットテスト）、Anthropic Messages API（`claude-sonnet-5`）、GitHub Contents API、claude.ai RemoteTrigger（クラウドルーティン）、iOS ショートカット。

**Spec:** `_secretary/specs/2026-09-09-rika-daily-manager-design.md`（このリポジトリ `mu-mumu-com/video-notes`）

## Global Constraints

- 対象リポジトリは2つ: **`mu-mumu-com/video-notes`**（データファイル・spec・plan・クラウドルーティンのソース）と **`mu-mumu-com/agent`**（`rika-line-bot/` を含む）。ローカルパスは `~/開発/video-notes` と `~/開発/agent`。
- 本業の情報を含むファイル（`work-duties.md`, `agenda.md`）は **video-notes（プライベートリポジトリ）限定**。社名・顧客名・具体的機密は書かない。各ファイル冒頭にその注意書きを入れる。
- 機密値（`INGEST_SECRET` 他）は `wrangler.toml` に書かない。必ず `wrangler secret put` で登録。
- クラウドルーティンは **GitHub 以外への外部HTTPS通信不可**。既存の `environment_id` は `env_018JLnu98AphHR6nuD8Md58N` を流用。model は `claude-sonnet-5`。
- 稼働スケジュール: 本業は月〜金のみ。副業・プライベートは毎日（土日含む）。土日の朝夜ブリーフィングは本業ブロックを省略。祝日は当面平日扱い。
- トーンは「決めてあげる＋励ます」。詰問・ダメ出し禁止。できなかった日を責めず淡々と繰り越す。
- 時刻はすべて JST 基準で設計し、cron は UTC で記述する（対応表は Task 8 / Task 11 / Task 12 参照）。
- コスト方針: 定型pushは0円を維持（Claude API を呼ばない）。対話返信のみ課金。既存の月次チェックイン（`0 9 1 * *` cron ＋ `runMonthlyCheckin`/`askRikaCheckin`）は廃止する。
- コミットは小さく頻繁に。コミットメッセージ末尾に `Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>`。

---

## 2026-09-09 改訂（ユーザー確認済み・下記タスクを上書き）

spec の「2026-09-09 改訂」に対応。実行者はこの節を各タスクより優先する。

- **`_secretary/work-duties.md`（video-notes）は作らない。** 本業の担当業務は **`~/SW/work-duties.md`（ローカルのみ・git 管理外）**。`~/SW` はユーザーの本業関連の作業場所。
- **クラウドの朝夜ルーティンと LINE ブリーフィングは「副業＋プライベート」だけ**を扱う。本業ブロックは出さない。
- **本業の定期業務リマインド・消化確認は、ローカルでりかちゃんを呼んだ時だけ**動く（Task 13 のペルソナ側）。`~/SW/work-duties.md`（定期業務）＋ iPhone リマインダーの本業用リスト（単発）を読む。
- **Google カレンダー（職場アカウント）は接続不可のため設計から除外**。クラウド・ローカルとも参照しない。
- **予定・タスクの実体は iPhone リマインダー**。本業用リスト（例『仕事』）と個人リストを分けて運用。朝のショートカットは**本業用リストを除外**して個人リマインダーだけを送る（Task 12）。ローカルりかちゃんは全リスト読める。
- 本業の中身はユーザーが 2026-09-10 以降にまとめて送る。受け取り時に質問して `~/SW/work-duties.md` に落とす（別タスク／この計画の外でよい）。

タスク別の差分:
- **Task 1**: `_secretary/work-duties.md` を作らない。代わりに `~/SW/work-duties.md`（ローカル）にテンプレートを置く。`agenda.md` / `kpi.md` / `daily/` は video-notes に作る（変更なし）。
- **Task 8 / Task 9**: bot の対話・pushコンテキストから `work-duties.md` を外す。`agenda` / `daily` / `kpi` / `roadmap` / `projects` / `profile` は入れる。
- **Task 11 朝ルーティン**: プロンプトの手順4（【本業】ブロック抽出）を削除。「本業は平日、詳細はりかちゃんを呼んで」の一言だけ添える。読むファイルから work-duties を外す。
- **Task 11 夜ルーティン**: 「本業定期業務の消化確認」を削除。宣言消化率＋ロードマップ＋KPI＋明日の種のみ。「翌営業日の予告」も本業分は出さない（副業の予告は可）。
- **Task 4 daily テンプレート**: `### 本業` セクションを持たない。`### 副業` / `### プライベート` / `### りかちゃんから` のみ。
- **Task 13**: `agent/secretary/CLAUDE.md` に「ローカル呼び出し時は `~/SW/work-duties.md`（定期業務）と iPhone リマインダー全リスト（`reminders` CLI か AppleScript）を読んで、本業（平日のみ）を含むフルブリーフィングをする。Google カレンダーは参照しない」を明記。

---

## ファイル構成

### `mu-mumu-com/video-notes`（新規・変更）

| パス | 責務 |
|---|---|
| `_secretary/work-duties.md` | 新規。本業の担当業務マスター（担当領域／毎日／週次／月次）。朝夜ルーティンが曜日・日付と照合して「今日該当」を抽出する |
| `_secretary/agenda.md` | 新規。本業/プライベートの単発予定。iPhoneショートカット＋手動＋LINE「予定:」で追記 |
| `_secretary/kpi.md` | 新規。各副業の数値。週1で手動更新。夜ルーティンが推移コメント |
| `_secretary/daily/.gitkeep` | 新規ディレクトリ。`_secretary/daily/<YYYY-MM-DD>.md` を朝夜ルーティンが生成・追記 |
| `_secretary/daily/_TEMPLATE.md` | 新規。daily ファイルの構造見本（人間用リファレンス。ルーティンはこの構造で書く） |
| `_secretary/profile.md` | 変更。「セルフマネジメントの傾向」節を追加 |

### `mu-mumu-com/agent` → `rika-line-bot/`（新規・変更）

| パス | 責務 |
|---|---|
| `src/datetime.ts` | 新規。JST 日付・曜日・週末判定の共通ヘルパー（`scheduled.ts`/`webhook.ts` の重複定義をここへ集約） |
| `src/daily.ts` | 新規。daily ファイルのパス生成・セクション抽出・LINE用要約・宣言チェック更新・「できた」返信の解釈（純関数） |
| `src/ingest.ts` | 新規。`/ingest` が受け取ったリマインダー配列を `agenda.md` の当日ブロックに落とす整形関数（純関数） |
| `src/datetime.test.ts` / `src/daily.test.ts` / `src/ingest.test.ts` | 新規。上記純関数の vitest テスト |
| `src/github.ts` | 変更。`updateFileText`（read-modify-write、409で1回リトライ）を追加 |
| `src/scheduled.ts` | 変更。朝リレー/昼ping/夜リレーの cron 分岐を追加。`sendWeeklyNotify` は維持。`runMonthlyCheckin` と `0 9 1 * *` 分岐を削除 |
| `src/claude.ts` | 変更。`askRika` の system を「人格(cache)／マスターファイル(cache)／当日ファイル・ログ(no cache)」に再構成。`askRikaCheckin` と `CHECKIN_SYSTEM_PROMPT` を削除 |
| `src/webhook.ts` | 変更。コンテキストに work-duties/agenda/kpi/当日daily を追加。「できた」返信で当日 daily のチェックを更新。「予定:」接頭辞で agenda に追記 |
| `src/index.ts` | 変更。`POST /ingest` ルートを追加（`X-Ingest-Secret` 検証） |
| `src/types.ts` | 変更。`Bindings` に `INGEST_SECRET: string` を追加 |
| `wrangler.toml` | 変更。`[triggers] crons` を差し替え |
| `package.json` | 変更。`vitest` を devDependencies に、`"test": "vitest run"` を scripts に追加 |
| `SHORTCUT.md` | 新規。iPhone ショートカット作成手順（ユーザー向け） |

### クラウドルーティン（claude.ai、RemoteTrigger）

| 名前 | cron (UTC) | 責務 |
|---|---|---|
| りかちゃん 朝ブリーフィング | `0 22 * * *` | 毎朝7:00 JST。`daily/<今日>.md` を生成 |
| りかちゃん 夜ふりかえり | `30 12 * * *` | 毎日21:30 JST。`daily/<今日>.md` に夜セクションを追記 |

### agent ペルソナ

| パス | 責務 |
|---|---|
| `~/開発/agent/secretary/CLAUDE.md` | 変更。朝夜ブリーフィングの枠組み、マネージャー姿勢、ローカル呼び出し時のカレンダー/リマインダー参照、新ファイルの読み込みを追加 |

---

## Task 0: 作業ツリーの整理

**Files:**
- Modify: `~/開発/agent`（作業ツリーの未コミット差分を確認）

**Interfaces:**
- Consumes: なし
- Produces: なし（クリーンな作業ツリー）

- [ ] **Step 1: agent リポジトリの差分を確認**

```bash
cd ~/開発/agent && git status && git diff rika-line-bot/src/scheduled.ts secretary/CLAUDE.md
```

- [ ] **Step 2: 軽微な差分を判断してコミットまたは破棄**

`homupe/CLAUDE.md` の変更（スキル追記）と `rika-line-bot/src/scheduled.ts`・`secretary/CLAUDE.md` の軽微な変更を確認する。意味のある変更ならコミット、レビュー済みで不要なら `git checkout --` で破棄する。判断がつかない場合はユーザーに一言確認してから進める（[[concurrent-sessions-caution]]）。

```bash
cd ~/開発/agent && git add -A && git commit -m "作業ツリー整理: 保留していた軽微な変更を反映

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

- [ ] **Step 3: video-notes 側の spec/plan をリモートへ反映**

```bash
cd ~/開発/video-notes && git fetch origin && git rebase --autostash origin/main && git push origin main && git log --oneline -3
```

Expected: spec と plan のコミットが `origin/main` に載る。作業ツリーの未追跡ファイル（過去の動画メモ等）はこのタスクでは触らない。

---

## Task 1: データファイルのテンプレートを作成

**Files:**
- Create: `~/開発/video-notes/_secretary/work-duties.md`
- Create: `~/開発/video-notes/_secretary/agenda.md`
- Create: `~/開発/video-notes/_secretary/kpi.md`
- Create: `~/開発/video-notes/_secretary/daily/.gitkeep`
- Create: `~/開発/video-notes/_secretary/daily/_TEMPLATE.md`

**Interfaces:**
- Consumes: なし
- Produces: 朝夜ルーティン（Task 10/11）と bot（Task 4〜8）が読むファイル群。ファイル名・見出し構造がインターフェースになる。

- [ ] **Step 1: `work-duties.md` を作成**

内容は spec の「1. work-duties.md」のテンプレートをそのまま使う。冒頭に「機密情報（社名・顧客名・具体内容）は書かない」の注意書き。中身は `〈例〉…` のプレースホルダのまま置き、Task 9 でユーザーヒアリングして実データに差し替える。行頭タグの記法を明記:

```
- [毎日] / [平日] / [月火水木金] … 毎日系
- [月]…[日] / [毎週] … 週次系
- [第1営業日] / [15日] / [月末] … 月次系
```

- [ ] **Step 2: `agenda.md` を作成**

spec の「2. agenda.md」のテンプレート。冒頭に機密注意書き。当日ブロックの見本を1つ（今日の日付で）入れておく。`work:` / `private:` / `reminders:` の3種の行頭ラベルを説明。

- [ ] **Step 3: `kpi.md` を作成**

spec の「3. kpi.md」のテンプレート。「## 更新: <日付>」ブロックを今日の日付で1つ（現状の数値、ほぼ0）入れておく。

- [ ] **Step 4: `daily/.gitkeep` と `daily/_TEMPLATE.md` を作成**

`_TEMPLATE.md` は spec の「4. daily/<YYYY-MM-DD>.md」のフォーマット（frontmatter・`## 朝`・`## 宣言`・`## 昼`・`## 夜` と各サブ見出し）をコメント付きで。ルーティンが生成物の構造を合わせる基準になる。

- [ ] **Step 5: マークダウンの体裁を目視確認しコミット**

```bash
cd ~/開発/video-notes && git add _secretary/work-duties.md _secretary/agenda.md _secretary/kpi.md _secretary/daily/ && git commit -m "りかちゃん日次: データファイル(work-duties/agenda/kpi/daily)のテンプレートを追加

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

## Task 2: profile.md にセルフマネジメント節を追加

**Files:**
- Modify: `~/開発/video-notes/_secretary/profile.md`

**Interfaces:**
- Consumes: なし
- Produces: 朝夜ルーティンと bot が読み、トーンと「決定を引き取る」挙動の根拠にする節。見出しは `## セルフマネジメントの傾向（りかちゃんが決定を引き取る根拠）`。

- [ ] **Step 1: 「大事にしたい価値観」節の直後に新セクションを挿入**

spec の「5. profile.md（既存を拡張）」のブロックをそのまま挿入する。既存の他セクション（情報源ポートフォリオ等）は変更しない。

- [ ] **Step 2: 更新履歴に1行追加**

```
- 2026-09-09: 「セルフマネジメントの傾向」節を追加（日次マネージャー化に伴い、優先順位と次の一手の決定をりかちゃんが引き取る方針を明文化）
```

- [ ] **Step 3: コミット**

```bash
cd ~/開発/video-notes && git add _secretary/profile.md && git commit -m "りかちゃん日次: profile.mdにセルフマネジメントの傾向を追記

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

## Task 3: rika-line-bot に vitest を導入

**Files:**
- Modify: `~/開発/agent/rika-line-bot/package.json`
- Create: `~/開発/agent/rika-line-bot/src/datetime.ts`
- Create: `~/開発/agent/rika-line-bot/src/datetime.test.ts`

**Interfaces:**
- Consumes: なし
- Produces:
  - `todayJst(d?: Date): string` → `"YYYY-MM-DD"`（JST）
  - `nowJstStamp(d?: Date): string` → `"YYYY-MM-DD HH:mm"`（JST。既存の `nowJst()` と同じ体裁）
  - `jstParts(d?: Date): { year: number; month: number; day: number; dow: number }`（`dow`: 0=日〜6=土）
  - `isWeekendJst(d?: Date): boolean`

- [ ] **Step 1: vitest を追加**

```bash
cd ~/開発/agent/rika-line-bot && npm install -D vitest@^3
```

`package.json` の `scripts` に `"test": "vitest run"` を追加。

- [ ] **Step 2: 失敗するテストを書く**

`src/datetime.test.ts`:

```typescript
import { describe, it, expect } from "vitest";
import { todayJst, nowJstStamp, jstParts, isWeekendJst } from "./datetime";

// 2026-09-09 は火曜日
const tue = new Date("2026-09-09T01:00:00Z"); // JST 10:00
const satNightUtc = new Date("2026-09-12T15:30:00Z"); // JST 日曜 00:30
const friJst = new Date("2026-09-11T09:00:00Z"); // JST 金 18:00

describe("datetime", () => {
  it("todayJst formats JST date", () => {
    expect(todayJst(tue)).toBe("2026-09-09");
    expect(todayJst(satNightUtc)).toBe("2026-09-13"); // UTCでは12日でもJSTは13日
  });

  it("nowJstStamp includes date and HH:mm", () => {
    expect(nowJstStamp(tue)).toBe("2026-09-09 10:00");
  });

  it("jstParts returns day-of-week (0=Sun..6=Sat)", () => {
    expect(jstParts(tue).dow).toBe(2);
    expect(jstParts(friJst).dow).toBe(5);
    expect(jstParts(satNightUtc).dow).toBe(0); // JST日曜
  });

  it("isWeekendJst true for Sat/Sun in JST", () => {
    expect(isWeekendJst(tue)).toBe(false);
    expect(isWeekendJst(friJst)).toBe(false);
    expect(isWeekendJst(satNightUtc)).toBe(true);
  });
});
```

- [ ] **Step 3: 失敗を確認**

Run: `cd ~/開発/agent/rika-line-bot && npm test`
Expected: FAIL（`./datetime` が存在しない）

- [ ] **Step 4: 最小実装**

`src/datetime.ts`:

```typescript
function partsOf(d: Date) {
  const p = new Intl.DateTimeFormat("en-CA", {
    timeZone: "Asia/Tokyo",
    year: "numeric", month: "2-digit", day: "2-digit",
    hour: "2-digit", minute: "2-digit", hour12: false,
    weekday: "short",
  }).formatToParts(d);
  const get = (t: string) => p.find((x) => x.type === t)?.value ?? "";
  const wmap: Record<string, number> = { Sun: 0, Mon: 1, Tue: 2, Wed: 3, Thu: 4, Fri: 5, Sat: 6 };
  return {
    year: Number(get("year")),
    month: Number(get("month")),
    day: Number(get("day")),
    hour: get("hour") === "24" ? "00" : get("hour"),
    minute: get("minute"),
    dow: wmap[get("weekday")] ?? 0,
  };
}

export function todayJst(d: Date = new Date()): string {
  const p = partsOf(d);
  return `${p.year}-${String(p.month).padStart(2, "0")}-${String(p.day).padStart(2, "0")}`;
}

export function nowJstStamp(d: Date = new Date()): string {
  const p = partsOf(d);
  return `${todayJst(d)} ${p.hour}:${p.minute}`;
}

export function jstParts(d: Date = new Date()) {
  const p = partsOf(d);
  return { year: p.year, month: p.month, day: p.day, dow: p.dow };
}

export function isWeekendJst(d: Date = new Date()): boolean {
  const dow = jstParts(d).dow;
  return dow === 0 || dow === 6;
}
```

- [ ] **Step 5: テストが通ることを確認**

Run: `cd ~/開発/agent/rika-line-bot && npm test`
Expected: PASS（4 tests）

- [ ] **Step 6: 既存コードの重複を datetime.ts に寄せる**

`src/scheduled.ts` と `src/webhook.ts` のローカル `nowJst()` / `todayJst()` を削除し、`import { nowJstStamp as nowJst, todayJst } from "./datetime"` に置き換える。`npm run typecheck` が通ることを確認。

Run: `cd ~/開発/agent/rika-line-bot && npm run typecheck && npm test`
Expected: 型エラーなし、テスト PASS

- [ ] **Step 7: コミット**

```bash
cd ~/開発/agent && git add rika-line-bot/ && git commit -m "rika-line-bot: vitest導入とJST日付ヘルパー(datetime.ts)を追加

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

## Task 4: daily ファイルのパース純関数

**Files:**
- Create: `~/開発/agent/rika-line-bot/src/daily.ts`
- Create: `~/開発/agent/rika-line-bot/src/daily.test.ts`

**Interfaces:**
- Consumes: `todayJst` from `./datetime`
- Produces:
  - `DAILY_DIR = "_secretary/daily"`
  - `dailyPath(dateStr: string): string` → `"_secretary/daily/2026-09-09.md"`
  - `extractSection(md: string, heading: string): string | null` — `## <heading>` から次の `## ` 直前までの本文（見出し行は含まない、trim 済み）
  - `buildMorningPush(md: string): string` — 朝セクションから LINE 用テキスト（各サブ見出し＋先頭1〜2行＋「りかちゃんから」全文）
  - `buildMiddayPush(md: string): string | null` — 「今日の最優先:」の行の値。無ければ null
  - `buildEveningPush(md: string): string` — 夜セクションから LINE 用テキスト。「本業定期業務の消化確認」に未チェック項目があれば末尾に「できたものを番号で返してね（例: 1,3）」を付ける
  - `parseDoneReply(text: string): number[] | "all" | null` — `"1,3"` `"1と3"` `"1 3 完了"` → `[1,3]`、`"全部"` `"ぜんぶできた"` `"全部できた"` → `"all"`、該当しなければ null
  - `applyDoneMarks(md: string, done: number[] | "all"): string` — `## 宣言` 配下の `- [ ]` を n 番目（1始まり）だけ `- [x]` に。`"all"` は全部

- [ ] **Step 1: 失敗するテストを書く**

`src/daily.test.ts`:

```typescript
import { describe, it, expect } from "vitest";
import {
  dailyPath, extractSection, buildMorningPush, buildMiddayPush,
  buildEveningPush, parseDoneReply, applyDoneMarks,
} from "./daily";

const SAMPLE = `---
date: 2026-09-09
---

## 朝（07:00 生成）
### 今日の状態
火曜・平日・月初でも月末でもない

### 本業
- 定期業務（今日該当）: メール確認、日報提出
- 単発: 15:00 会議
- 今日ここだけ守る: 日報を17時までに出す

### 副業（りかちゃんが決めた）
- 今日の最優先: ココナラのカバー画像を確定してアップロード
- 最初の30分でやること: cover_A.html をブラウザで開いて文言を最終確認
- （理由: フェーズ1の最後の詰まりがカバー画像だから）

### プライベート
- 19:00 歯医者

### りかちゃんから
- 今日はカバーだけ。他は気にしなくていい。私が決めた。
- 予定が薄い場合の確認: （今日は予定あり、省略）

## 宣言
- [ ] ココナラのカバー画像を確定
- [ ] 日報提出
- [ ] 歯医者

## 昼（13:00 push のみ・記録なし）

## 夜（21:30 生成）
### 宣言タスクの消化
- 未確認

### 本業定期業務の消化確認
- [ ] メール確認
- [ ] 日報提出

### ロードマップ進捗
- 変化なし

### KPI
- kpi.md 最終更新 0日前。数値変化なし

### 明日の種
- ランサーズのプロフィール下書き
`;

describe("daily", () => {
  it("dailyPath", () => {
    expect(dailyPath("2026-09-09")).toBe("_secretary/daily/2026-09-09.md");
  });

  it("extractSection returns body between ## headings", () => {
    expect(extractSection(SAMPLE, "宣言")).toContain("- [ ] 日報提出");
    expect(extractSection(SAMPLE, "宣言")).not.toContain("## 昼");
    expect(extractSection(SAMPLE, "存在しない")).toBeNull();
  });

  it("buildMorningPush includes priority and りかちゃんから", () => {
    const push = buildMorningPush(SAMPLE);
    expect(push).toContain("ココナラのカバー画像を確定してアップロード");
    expect(push).toContain("私が決めた");
  });

  it("buildMiddayPush returns the priority line value", () => {
    expect(buildMiddayPush(SAMPLE)).toBe("ココナラのカバー画像を確定してアップロード");
    expect(buildMiddayPush("## 朝\n### 副業\n- なし")).toBeNull();
  });

  it("buildEveningPush appends done-number prompt when unchecked duties exist", () => {
    const push = buildEveningPush(SAMPLE);
    expect(push).toContain("明日の種");
    expect(push).toMatch(/番号で返して/);
  });

  it("parseDoneReply", () => {
    expect(parseDoneReply("1,3")).toEqual([1, 3]);
    expect(parseDoneReply("1と3 できた")).toEqual([1, 3]);
    expect(parseDoneReply("全部できた")).toBe("all");
    expect(parseDoneReply("今日は疲れた")).toBeNull();
  });

  it("applyDoneMarks toggles the Nth checkbox under ## 宣言 only", () => {
    const out = applyDoneMarks(SAMPLE, [1, 3]);
    const decl = extractSection(out, "宣言")!;
    expect(decl).toContain("- [x] ココナラのカバー画像を確定");
    expect(decl).toContain("- [ ] 日報提出");
    expect(decl).toContain("- [x] 歯医者");
    // 夜セクションのチェックボックスは触らない
    expect(extractSection(out, "本業定期業務の消化確認")).toContain("- [ ] メール確認");
  });

  it("applyDoneMarks 'all' checks everything under 宣言", () => {
    const decl = extractSection(applyDoneMarks(SAMPLE, "all"), "宣言")!;
    expect(decl).not.toContain("- [ ]");
  });
});
```

- [ ] **Step 2: 失敗を確認**

Run: `cd ~/開発/agent/rika-line-bot && npm test src/daily.test.ts`
Expected: FAIL（`./daily` が存在しない）

- [ ] **Step 3: 最小実装**

`src/daily.ts`:

```typescript
export const DAILY_DIR = "_secretary/daily";

export function dailyPath(dateStr: string): string {
  return `${DAILY_DIR}/${dateStr}.md`;
}

export function extractSection(md: string, heading: string): string | null {
  const lines = md.split("\n");
  const start = lines.findIndex((l) => l.replace(/（.*?）/g, "").trim() === `## ${heading}`
    || l.trim().startsWith(`## ${heading}`));
  if (start === -1) return null;
  let end = lines.length;
  for (let i = start + 1; i < lines.length; i++) {
    if (/^## /.test(lines[i])) { end = i; break; }
  }
  return lines.slice(start + 1, end).join("\n").trim();
}

function findSubValue(section: string, label: string): string | null {
  const m = section.match(new RegExp(`(?:^|\\n)\\s*-?\\s*${label}[:：]\\s*(.+)`));
  return m ? m[1].trim() : null;
}

export function buildMorningPush(md: string): string {
  const morning = extractSection(md, "朝") ?? "";
  const rika = (morning.match(/### りかちゃんから\n([\s\S]*?)(?:\n### |\n## |$)/)?.[1] ?? "").trim();
  const honmyo = findSubValue(morning, "定期業務（今日該当）");
  const tanpatsu = findSubValue(morning, "単発");
  const priority = findSubValue(morning, "今日の最優先");
  const first30 = findSubValue(morning, "最初の30分でやること");
  const priv = (morning.match(/### プライベート\n([\s\S]*?)(?:\n### |\n## |$)/)?.[1] ?? "").trim();
  const parts: string[] = ["☀️ おはよう。今日の組み立て"];
  if (honmyo) parts.push(`【本業】${honmyo}${tanpatsu ? ` / ${tanpatsu}` : ""}`);
  if (priority) parts.push(`【副業】今日はこれだけ: ${priority}${first30 ? `\n→まず: ${first30}` : ""}`);
  if (priv) parts.push(`【プライベート】${priv.replace(/\n/g, " / ")}`);
  if (rika) parts.push(`\n${rika}`);
  return parts.join("\n");
}

export function buildMiddayPush(md: string): string | null {
  const morning = extractSection(md, "朝") ?? md;
  return findSubValue(morning, "今日の最優先");
}

export function buildEveningPush(md: string): string {
  const night = extractSection(md, "夜") ?? "";
  const digest = findSubValue(night, "宣言タスクの消化") ?? "未確認";
  const roadmap = findSubValue(night, "ロードマップ進捗") ?? "";
  const kpi = findSubValue(night, "KPI") ?? "";
  const seed = findSubValue(night, "明日の種") ?? "";
  const duties = extractSection(md, "本業定期業務の消化確認") ?? "";
  const parts: string[] = ["🌙 おつかれさま。今日のふりかえり"];
  parts.push(`宣言の消化: ${digest}`);
  if (roadmap) parts.push(`進捗: ${roadmap}`);
  if (kpi) parts.push(`KPI: ${kpi}`);
  if (seed) parts.push(`明日の種: ${seed}`);
  if (/- \[ \]/.test(duties)) {
    parts.push("\n今日の本業定期業務、できたものを番号で返してね（例: 1,3 / 全部）:");
    duties.split("\n").filter((l) => /- \[[ x]\]/.test(l)).forEach((l, i) => {
      parts.push(`${i + 1}. ${l.replace(/- \[[ x]\]\s*/, "")}`);
    });
  }
  return parts.join("\n");
}

export function parseDoneReply(text: string): number[] | "all" | null {
  const t = text.trim();
  if (/(全部|ぜんぶ|すべて)(でき|完了|おわ|終わ)/.test(t) || /^(全部|ぜんぶ|すべて)$/.test(t)) return "all";
  const nums = [...t.matchAll(/\d+/g)].map((m) => Number(m[0])).filter((n) => n >= 1 && n <= 20);
  if (nums.length === 0) return null;
  // 「できた/完了/done/✓」等の完了サインが含まれる時だけ done 返信とみなす
  if (!/(でき|完了|done|終わ|おわ|✓|済)/i.test(t) && !/^[\d,、と\s]+$/.test(t)) return null;
  return [...new Set(nums)];
}

export function applyDoneMarks(md: string, done: number[] | "all"): string {
  const lines = md.split("\n");
  const start = lines.findIndex((l) => l.trim().startsWith("## 宣言"));
  if (start === -1) return md;
  let end = lines.length;
  for (let i = start + 1; i < lines.length; i++) {
    if (/^## /.test(lines[i])) { end = i; break; }
  }
  let n = 0;
  for (let i = start + 1; i < end; i++) {
    if (/^\s*- \[[ x]\] /.test(lines[i])) {
      n++;
      if (done === "all" || done.includes(n)) {
        lines[i] = lines[i].replace(/- \[ \] /, "- [x] ");
      }
    }
  }
  return lines.join("\n");
}
```

- [ ] **Step 4: テストが通ることを確認**

Run: `cd ~/開発/agent/rika-line-bot && npm test src/daily.test.ts`
Expected: PASS（8 tests）。落ちたケースは正規表現を調整（サブ見出しの全角括弧やスペースに注意）。

- [ ] **Step 5: 全テスト＋型チェック**

Run: `cd ~/開発/agent/rika-line-bot && npm test && npm run typecheck`
Expected: 全 PASS、型エラーなし

- [ ] **Step 6: コミット**

```bash
cd ~/開発/agent && git add rika-line-bot/ && git commit -m "rika-line-bot: daily.ts(dailyファイルのパース純関数)とテストを追加

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

## Task 5: リマインダー取り込みの整形純関数

**Files:**
- Create: `~/開発/agent/rika-line-bot/src/ingest.ts`
- Create: `~/開発/agent/rika-line-bot/src/ingest.test.ts`

**Interfaces:**
- Consumes: `todayJst` from `./datetime`
- Produces:
  - `AGENDA_PATH = "_secretary/agenda.md"`
  - `upsertAgendaReminders(current: string | null, dateStr: string, items: string[]): string` — `agenda.md` 全文を受け取り、`## <dateStr>` ブロックが無ければ先頭（`# 予定・単発タスク` 見出しの直後）に作り、その中の `- reminders:` 配下を `items` で置き換えた全文を返す。既存の `work:` / `private:` 行は保持。`items` が空なら現状の全文をそのまま返す
  - `parseIngestBody(body: unknown): { type: string; items: string[] } | null` — `{ type: "reminders", items: string[] }` 形式の検証。不正なら null

- [ ] **Step 1: 失敗するテストを書く**

`src/ingest.test.ts`:

```typescript
import { describe, it, expect } from "vitest";
import { upsertAgendaReminders, parseIngestBody, AGENDA_PATH } from "./ingest";

const EXISTING = `# 予定・単発タスク

## 2026-09-08
- work: 15:00 会議
- private: 19:00 歯医者
- reminders:
  - 古い項目
`;

describe("ingest", () => {
  it("AGENDA_PATH", () => {
    expect(AGENDA_PATH).toBe("_secretary/agenda.md");
  });

  it("adds a new dated block at top when absent", () => {
    const out = upsertAgendaReminders(EXISTING, "2026-09-09", ["A", "B"]);
    expect(out.indexOf("## 2026-09-09")).toBeLessThan(out.indexOf("## 2026-09-08"));
    expect(out).toContain("  - A");
    expect(out).toContain("  - B");
    expect(out).toContain("## 2026-09-08"); // 既存は残る
  });

  it("replaces reminders under existing block, keeps work/private", () => {
    const out = upsertAgendaReminders(EXISTING, "2026-09-08", ["新項目"]);
    expect(out).toContain("- work: 15:00 会議");
    expect(out).toContain("- private: 19:00 歯医者");
    expect(out).toContain("  - 新項目");
    expect(out).not.toContain("古い項目");
  });

  it("creates file body when current is null", () => {
    const out = upsertAgendaReminders(null, "2026-09-09", ["X"]);
    expect(out).toContain("# 予定・単発タスク");
    expect(out).toContain("## 2026-09-09");
    expect(out).toContain("  - X");
  });

  it("empty items is a no-op returning current text", () => {
    expect(upsertAgendaReminders(EXISTING, "2026-09-09", [])).toBe(EXISTING);
  });

  it("parseIngestBody validates shape", () => {
    expect(parseIngestBody({ type: "reminders", items: ["a"] })).toEqual({ type: "reminders", items: ["a"] });
    expect(parseIngestBody({ type: "reminders", items: "a" })).toBeNull();
    expect(parseIngestBody({ items: ["a"] })).toBeNull();
    expect(parseIngestBody(null)).toBeNull();
  });
});
```

- [ ] **Step 2: 失敗を確認**

Run: `cd ~/開発/agent/rika-line-bot && npm test src/ingest.test.ts`
Expected: FAIL（`./ingest` が存在しない）

- [ ] **Step 3: 最小実装**

`src/ingest.ts`:

```typescript
export const AGENDA_PATH = "_secretary/agenda.md";
const HEADER = "# 予定・単発タスク";

export function parseIngestBody(body: unknown): { type: string; items: string[] } | null {
  if (!body || typeof body !== "object") return null;
  const b = body as Record<string, unknown>;
  if (b.type !== "reminders") return null;
  if (!Array.isArray(b.items) || !b.items.every((x) => typeof x === "string")) return null;
  return { type: "reminders", items: b.items as string[] };
}

export function upsertAgendaReminders(
  current: string | null,
  dateStr: string,
  items: string[]
): string {
  if (items.length === 0 && current !== null) return current;
  const body = current ?? `${HEADER}\n`;
  const lines = body.split("\n");
  const blockStart = lines.findIndex((l) => l.trim() === `## ${dateStr}`);
  const reminderLines = items.map((i) => `  - ${i}`);

  if (blockStart === -1) {
    // 新規ブロックを HEADER 直後に挿入
    const headerIdx = lines.findIndex((l) => l.trim() === HEADER);
    const insertAt = headerIdx === -1 ? 0 : headerIdx + 1;
    const block = ["", `## ${dateStr}`, "- reminders:", ...reminderLines, ""];
    lines.splice(insertAt, 0, ...block);
    return lines.join("\n");
  }

  // 既存ブロック内の reminders: 配下を置換
  let blockEnd = lines.length;
  for (let i = blockStart + 1; i < lines.length; i++) {
    if (/^## /.test(lines[i])) { blockEnd = i; break; }
  }
  const remIdx = lines.findIndex((l, i) => i > blockStart && i < blockEnd && l.trim() === "- reminders:");
  if (remIdx === -1) {
    lines.splice(blockEnd, 0, "- reminders:", ...reminderLines);
  } else {
    let remEnd = blockEnd;
    for (let i = remIdx + 1; i < blockEnd; i++) {
      if (!/^\s+- /.test(lines[i])) { remEnd = i; break; }
    }
    lines.splice(remIdx + 1, remEnd - (remIdx + 1), ...reminderLines);
  }
  return lines.join("\n");
}
```

- [ ] **Step 4: テストが通ることを確認**

Run: `cd ~/開発/agent/rika-line-bot && npm test src/ingest.test.ts`
Expected: PASS（6 tests）

- [ ] **Step 5: コミット**

```bash
cd ~/開発/agent && git add rika-line-bot/ && git commit -m "rika-line-bot: ingest.ts(リマインダーをagenda.mdへ整形)とテストを追加

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

## Task 6: github.ts に updateFileText を追加

**Files:**
- Modify: `~/開発/agent/rika-line-bot/src/github.ts`
- Create: `~/開発/agent/rika-line-bot/src/github.test.ts`

**Interfaces:**
- Consumes: なし（`fetch` をテストでモック）
- Produces:
  - `updateFileText(token, owner, repo, path, transform: (current: string | null) => string | null, commitMessage: string): Promise<"updated" | "nochange" | "created">` — GET で現在値と sha を取得 → `transform` 適用 → 結果が null か現在値と同一なら `"nochange"` → それ以外は PUT。PUT が 409（sha 競合）なら1回だけ GET からやり直す

- [ ] **Step 1: 失敗するテストを書く**

`src/github.test.ts`（`vi.stubGlobal("fetch", ...)` でモック）:

```typescript
import { describe, it, expect, vi, afterEach } from "vitest";
import { updateFileText } from "./github";

function b64(s: string) { return Buffer.from(s, "utf8").toString("base64"); }

afterEach(() => vi.unstubAllGlobals());

describe("updateFileText", () => {
  it("returns 'nochange' when transform returns null", async () => {
    vi.stubGlobal("fetch", vi.fn(async () =>
      new Response(JSON.stringify({ content: b64("hi"), sha: "s1", encoding: "base64" }), { status: 200 })
    ));
    const r = await updateFileText("t", "o", "r", "p", () => null, "m");
    expect(r).toBe("nochange");
  });

  it("PUTs transformed content and returns 'updated'", async () => {
    const calls: string[] = [];
    vi.stubGlobal("fetch", vi.fn(async (url: string, init?: RequestInit) => {
      calls.push(init?.method ?? "GET");
      if ((init?.method ?? "GET") === "GET") {
        return new Response(JSON.stringify({ content: b64("old"), sha: "s1", encoding: "base64" }), { status: 200 });
      }
      return new Response("{}", { status: 200 });
    }));
    const r = await updateFileText("t", "o", "r", "p", (c) => c + " new", "m");
    expect(r).toBe("updated");
    expect(calls).toEqual(["GET", "PUT"]);
  });

  it("retries once on 409 conflict", async () => {
    let put = 0;
    vi.stubGlobal("fetch", vi.fn(async (url: string, init?: RequestInit) => {
      if ((init?.method ?? "GET") === "GET") {
        return new Response(JSON.stringify({ content: b64("x"), sha: "s" + (++put), encoding: "base64" }), { status: 200 });
      }
      return new Response("conflict", { status: put < 2 ? 409 : 200 });
    }));
    const r = await updateFileText("t", "o", "r", "p", (c) => (c ?? "") + "!", "m");
    expect(r).toBe("updated");
  });

  it("returns 'created' when file is absent (404)", async () => {
    vi.stubGlobal("fetch", vi.fn(async (url: string, init?: RequestInit) => {
      if ((init?.method ?? "GET") === "GET") return new Response("nf", { status: 404 });
      return new Response("{}", { status: 201 });
    }));
    const r = await updateFileText("t", "o", "r", "p", (c) => (c ?? "") + "seed", "m");
    expect(r).toBe("created");
  });
});
```

- [ ] **Step 2: 失敗を確認**

Run: `cd ~/開発/agent/rika-line-bot && npm test src/github.test.ts`
Expected: FAIL（`updateFileText` が export されていない）

- [ ] **Step 3: 最小実装**

`src/github.ts` の末尾に追加（既存の `utf8ToBase64` / `base64ToUtf8` / `authHeaders` / `API` を再利用）:

```typescript
export async function updateFileText(
  token: string,
  owner: string,
  repo: string,
  path: string,
  transform: (current: string | null) => string | null,
  commitMessage: string
): Promise<"updated" | "nochange" | "created"> {
  for (let attempt = 0; attempt < 2; attempt++) {
    const getRes = await fetch(`${API}/repos/${owner}/${repo}/contents/${path}`, {
      headers: authHeaders(token),
    });
    let sha: string | undefined;
    let current: string | null = null;
    if (getRes.ok) {
      const data = (await getRes.json()) as { content: string; sha: string };
      sha = data.sha;
      current = base64ToUtf8(data.content);
    } else if (getRes.status !== 404) {
      throw new Error(`GitHub fetch failed before update: ${getRes.status} ${path}`);
    }

    const next = transform(current);
    if (next === null || next === current) return "nochange";

    const putRes = await fetch(`${API}/repos/${owner}/${repo}/contents/${path}`, {
      method: "PUT",
      headers: { ...authHeaders(token), "Content-Type": "application/json" },
      body: JSON.stringify({ message: commitMessage, content: utf8ToBase64(next), sha }),
    });
    if (putRes.status === 409 && attempt === 0) continue; // sha 競合 → リトライ
    if (!putRes.ok) throw new Error(`GitHub update failed: ${putRes.status} ${await putRes.text()}`);
    return sha ? "updated" : "created";
  }
  throw new Error("GitHub update failed after retry");
}
```

- [ ] **Step 4: テストが通ることを確認**

Run: `cd ~/開発/agent/rika-line-bot && npm test src/github.test.ts && npm run typecheck`
Expected: PASS（4 tests）、型エラーなし

- [ ] **Step 5: コミット**

```bash
cd ~/開発/agent && git add rika-line-bot/ && git commit -m "rika-line-bot: github.tsにupdateFileText(read-modify-write)を追加

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

## Task 7: `/ingest` エンドポイント

**Files:**
- Modify: `~/開発/agent/rika-line-bot/src/types.ts`
- Create: `~/開発/agent/rika-line-bot/src/ingest-route.ts`
- Modify: `~/開発/agent/rika-line-bot/src/index.ts`

**Interfaces:**
- Consumes: `parseIngestBody`, `upsertAgendaReminders`, `AGENDA_PATH` from `./ingest`; `updateFileText` from `./github`; `todayJst` from `./datetime`
- Produces: `ingestRoute: Hono<{ Bindings: Bindings }>` にマウントされた `POST /ingest`
  - ヘッダー `X-Ingest-Secret` が `env.INGEST_SECRET` と一致しなければ 401
  - body を `parseIngestBody` で検証、不正なら 400
  - `updateFileText(AGENDA_PATH, current => upsertAgendaReminders(current, todayJst(), items), "iPhoneリマインダー取り込み (<日付>)")`
  - 成功で `{ ok: true, result }` を 200

- [ ] **Step 1: `Bindings` に `INGEST_SECRET` を追加**

`src/types.ts` の `Bindings` に `INGEST_SECRET: string;` を追加。

- [ ] **Step 2: ルートを実装**

`src/ingest-route.ts`:

```typescript
import { Hono } from "hono";
import type { Bindings } from "./types";
import { parseIngestBody, upsertAgendaReminders, AGENDA_PATH } from "./ingest";
import { updateFileText } from "./github";
import { todayJst } from "./datetime";

export const ingestRoute = new Hono<{ Bindings: Bindings }>();

ingestRoute.post("/ingest", async (c) => {
  if (c.req.header("x-ingest-secret") !== c.env.INGEST_SECRET) {
    return c.json({ ok: false, error: "unauthorized" }, 401);
  }
  let body: unknown;
  try {
    body = await c.req.json();
  } catch {
    return c.json({ ok: false, error: "invalid json" }, 400);
  }
  const parsed = parseIngestBody(body);
  if (!parsed) return c.json({ ok: false, error: "invalid body" }, 400);

  const today = todayJst();
  const { GITHUB_TOKEN, GITHUB_OWNER, GITHUB_REPO } = c.env;
  const result = await updateFileText(
    GITHUB_TOKEN, GITHUB_OWNER, GITHUB_REPO, AGENDA_PATH,
    (current) => upsertAgendaReminders(current, today, parsed.items),
    `iPhoneリマインダー取り込み (${today})`
  );
  return c.json({ ok: true, result });
});
```

- [ ] **Step 3: index.ts にマウント**

```typescript
import { ingestRoute } from "./ingest-route";
// ...
app.route("/", webhook);
app.route("/", ingestRoute);
```

- [ ] **Step 4: 型チェック**

Run: `cd ~/開発/agent/rika-line-bot && npm run typecheck`
Expected: 型エラーなし

- [ ] **Step 5: ローカルで手動確認**

`.dev.vars` に `INGEST_SECRET=testsecret` を追記（このファイルは gitignore 済み）。別ターミナルで `npm run dev`、`[wrangler:inf] Ready on http://localhost:8787` を待ってから:

```bash
curl -s -X POST http://localhost:8787/ingest -H "X-Ingest-Secret: wrong" -d '{}' ; echo
# → 401

curl -s -X POST http://localhost:8787/ingest -H "X-Ingest-Secret: testsecret" \
  -H "Content-Type: application/json" \
  -d '{"type":"reminders","items":["ゴミ出し","請求書チェック"]}' ; echo
# → {"ok":true,"result":"updated" or "created"}  ※実際に video-notes/_secretary/agenda.md にコミットが入る点に注意
```

ローカルテストで実リポジトリを汚したくない場合は、`.dev.vars` の `GITHUB_REPO` を一時的にテスト用の私物リポジトリに向けるか、この Step は wrangler dev のログで 200/401/400 の分岐だけ確認し、実書き込みは Task 11 のデプロイ後にショートカットから1回だけ行う。

停止: `pkill -f "wrangler dev" ; pkill -f workerd`

- [ ] **Step 6: コミット**

```bash
cd ~/開発/agent && git add rika-line-bot/ && git commit -m "rika-line-bot: POST /ingest エンドポイント(リマインダー→agenda.md)を追加

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

## Task 8: scheduled.ts に朝リレー・昼ping・夜リレーを追加、月次チェックインを削除

**Files:**
- Modify: `~/開発/agent/rika-line-bot/src/scheduled.ts`
- Modify: `~/開発/agent/rika-line-bot/src/claude.ts`
- Modify: `~/開発/agent/rika-line-bot/wrangler.toml`

**Interfaces:**
- Consumes: `buildMorningPush`, `buildMiddayPush`, `buildEveningPush`, `dailyPath` from `./daily`; `todayJst` from `./datetime`; `fetchFileText` from `./github`; `pushMessage` from `./line`
- Produces: `scheduled(event, env, ctx)` が以下の cron を処理する
  - `20 9 * * 5` → `sendWeeklyNotify`（既存・変更なし）
  - `20 22 * * *` → `sendMorningRelay`（07:20 JST）
  - `0 4 * * *` → `sendMiddayPing`（13:00 JST）
  - `50 12 * * *` → `sendEveningRelay`（21:50 JST）
  - それ以外 → 何もしない（`console.log` のみ。従来の月次フォールバックは廃止）

- [ ] **Step 1: cron 対応表を wrangler.toml に反映**

`wrangler.toml` の `[triggers]` を差し替え:

```toml
# JST→UTC:  07:20→22:20 / 13:00→04:00 / 21:50→12:50 / 金18:20→金09:20
[triggers]
crons = ["20 22 * * *", "0 4 * * *", "50 12 * * *", "20 9 * * 5"]
```

（`0 9 1 * *` を削除）

- [ ] **Step 2: リレー関数を実装**

`src/scheduled.ts`:
- 冒頭の cron 定数を更新: `const WEEKLY_NOTIFY_CRON = "20 9 * * 5";` に加え `const MORNING_RELAY_CRON = "20 22 * * *";` `const MIDDAY_PING_CRON = "0 4 * * *";` `const EVENING_RELAY_CRON = "50 12 * * *";`
- `askRikaCheckin` の import と `runMonthlyCheckin` 関数を削除
- 追加:

```typescript
import { buildMorningPush, buildMiddayPush, buildEveningPush, dailyPath } from "./daily";

async function readDaily(env: Bindings): Promise<string | null> {
  return fetchFileText(
    env.GITHUB_TOKEN, env.GITHUB_OWNER, env.GITHUB_REPO, dailyPath(todayJst())
  );
}

async function sendMorningRelay(env: Bindings): Promise<void> {
  const md = await readDaily(env);
  if (!md) { console.log("morning: no daily file yet"); return; }
  await pushMessage(env.LINE_CHANNEL_ACCESS_TOKEN, env.LINE_USER_ID, buildMorningPush(md));
}

async function sendMiddayPing(env: Bindings): Promise<void> {
  const md = await readDaily(env);
  if (!md) { console.log("midday: no daily file"); return; }
  const priority = buildMiddayPush(md);
  const msg = priority
    ? `☕ 午前どうだった？\n朝きめた「${priority}」、進んでる？\n詰まってたら教えて。無理に進めなくていいよ。`
    : "☕ 午前おつかれさま。午後の副業タイム、何か1つ進める？";
  await pushMessage(env.LINE_CHANNEL_ACCESS_TOKEN, env.LINE_USER_ID, msg);
}

async function sendEveningRelay(env: Bindings): Promise<void> {
  const md = await readDaily(env);
  if (!md) { console.log("evening: no daily file"); return; }
  await pushMessage(env.LINE_CHANNEL_ACCESS_TOKEN, env.LINE_USER_ID, buildEveningPush(md));
}
```

- `scheduled()` を書き換え:

```typescript
export async function scheduled(
  event: ScheduledController, env: Bindings, ctx: ExecutionContext
): Promise<void> {
  switch (event.cron) {
    case WEEKLY_NOTIFY_CRON: return sendWeeklyNotify(env);
    case MORNING_RELAY_CRON: return sendMorningRelay(env);
    case MIDDAY_PING_CRON: return sendMiddayPing(env);
    case EVENING_RELAY_CRON: return sendEveningRelay(env);
    default: console.log(`unknown cron: ${event.cron}`); return;
  }
}
```

- [ ] **Step 3: claude.ts から月次チェックインを削除**

`src/claude.ts` の `CHECKIN_SYSTEM_PROMPT` 定数と `askRikaCheckin` 関数を削除。`askRika` は Task 9 で改修するのでここでは触らない。

- [ ] **Step 4: 型チェック**

Run: `cd ~/開発/agent/rika-line-bot && npm run typecheck && npm test`
Expected: 型エラーなし（`askRikaCheckin` の参照が残っていれば消す）、既存テスト PASS

- [ ] **Step 5: wrangler dev で cron 分岐をローカル実行**

```bash
npm run dev &
# Ready を待つ
curl -s "http://localhost:8787/__scheduled?cron=0+4+*+*+*" ; echo   # 昼ping
curl -s "http://localhost:8787/__scheduled?cron=20+22+*+*+*" ; echo # 朝リレー
```

Expected: daily ファイルがまだ無ければログに `no daily file` が出て LINE 送信はされない（エラーにならない）。`_secretary/daily/<今日>.md` を手で1つ push してから再実行すると LINE に届く（本人のLINEに実際に届く点に注意。テスト送信して良いか事前に確認）。

停止: `pkill -f "wrangler dev" ; pkill -f workerd`

- [ ] **Step 6: コミット**

```bash
cd ~/開発/agent && git add rika-line-bot/ && git commit -m "rika-line-bot: 朝リレー・昼ping・夜リレーのcron分岐を追加、月次チェックインを廃止

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

## Task 9: webhook.ts の対話を日次コンテキスト対応にする

**Files:**
- Modify: `~/開発/agent/rika-line-bot/src/claude.ts`
- Modify: `~/開発/agent/rika-line-bot/src/webhook.ts`

**Interfaces:**
- Consumes: `parseDoneReply`, `applyDoneMarks`, `dailyPath`, `extractSection` from `./daily`; `updateFileText` from `./github`; `todayJst` from `./datetime`
- Produces:
  - `askRika(apiKey, stableFiles: {label,content}[], volatileFiles: {label,content}[], recentLog: string, userMessage: string): Promise<string>` — `stableFiles`（人格＋マスター）を `cache_control: ephemeral`、`volatileFiles`（当日 daily・kpi 当日分）とログを非キャッシュに分ける
  - webhook が「できた」返信を検知したら当日 daily のチェックを更新し、返信に「〈2/3〉記録したよ」を含める
  - `予定:` で始まるメッセージは agenda.md の当日ブロックに1行追記する

- [ ] **Step 1: askRika の署名を変更（失敗させる用の呼び出しを先に書く）**

`src/webhook.ts` の `handleEvent` で新しい呼び出しに書き換える（この時点で型エラー＝失敗）:

```typescript
const stableFiles = [
  { label: "りかちゃんの役割", content: "(SYSTEM_PROMPTに内包)" }, // 実体はclaude.ts側
  { label: "個人プロファイル", content: profile ?? "(未作成)" },
  { label: "本業 担当業務マスター", content: workDuties ?? "(未作成)" },
  { label: "副業ロードマップ", content: roadmap ?? "(未作成)" },
  { label: "プロジェクト目的シート", content: projects ?? "(未作成)" },
];
const volatileFiles = [
  { label: "今日のブリーフィング(daily)", content: daily ?? "(未生成)" },
  { label: "予定(agenda 当日周辺)", content: agenda ?? "(未作成)" },
  { label: "副業KPI", content: kpi ?? "(未作成)" },
  { label: "直近の週次レポート", content: latestReport ?? "(まだ無し)" },
];
const reply = await askRika(env.ANTHROPIC_API_KEY, stableFiles, volatileFiles, recentLog, userMessage);
```

- [ ] **Step 2: 型チェックで失敗を確認**

Run: `cd ~/開発/agent/rika-line-bot && npm run typecheck`
Expected: FAIL（`askRika` の引数不一致、`profile`/`workDuties`/`daily`/`agenda`/`kpi` 未定義）

- [ ] **Step 3: claude.ts の askRika を改修**

`SYSTEM_PROMPT` に日次マネージャーとしての姿勢を追記（決定を引き取る／土日は本業を出さない／詰めない）。署名を変更:

```typescript
export async function askRika(
  apiKey: string,
  stableFiles: { label: string; content: string }[],
  volatileFiles: { label: string; content: string }[],
  recentLog: string,
  userMessage: string
): Promise<string> {
  const stableText = stableFiles.map((f) => `## ${f.label}\n${f.content}`).join("\n\n");
  const volatileText = volatileFiles.map((f) => `## ${f.label}\n${f.content}`).join("\n\n");

  const response = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "x-api-key": apiKey,
      "anthropic-version": "2023-06-01",
    },
    body: JSON.stringify({
      model: "claude-sonnet-5",
      max_tokens: 1024,
      system: [
        { type: "text", text: SYSTEM_PROMPT, cache_control: { type: "ephemeral" } },
        { type: "text", text: stableText, cache_control: { type: "ephemeral" } },
      ],
      messages: [
        {
          role: "user",
          content:
            `${volatileText}\n\n---\n直近のLINEログ:\n${recentLog || "(なし)"}\n\n` +
            `今回のメッセージ:\n${userMessage}`,
        },
      ],
    }),
  });
  if (!response.ok) throw new Error(`Claude API error: ${response.status} ${await response.text()}`);
  const data = (await response.json()) as { content: Array<{ type: string; text?: string }> };
  return data.content.find((b) => b.type === "text")?.text ?? "うまく回答を作れませんでした。";
}
```

- [ ] **Step 4: webhook.ts のコンテキスト取得を拡張**

`handleEvent` の `Promise.all` を以下に置き換え（`agenda.md` は当日周辺で十分だが簡単のため全文取得。肥大化したら Task で `extractSection` 的に絞る）:

```typescript
const today = todayJst();
const [roadmap, projects, latestReport, inbox, profile, workDuties, daily, agenda, kpi] =
  await Promise.all([
    fetchFileText(GITHUB_TOKEN, GITHUB_OWNER, GITHUB_REPO, "_secretary/fukugyo-roadmap.md"),
    fetchFileText(GITHUB_TOKEN, GITHUB_OWNER, GITHUB_REPO, "_secretary/projects.md"),
    fetchLatestReport(GITHUB_TOKEN, GITHUB_OWNER, GITHUB_REPO),
    fetchFileText(GITHUB_TOKEN, GITHUB_OWNER, GITHUB_REPO, INBOX_PATH),
    fetchFileText(GITHUB_TOKEN, GITHUB_OWNER, GITHUB_REPO, "_secretary/profile.md"),
    fetchFileText(GITHUB_TOKEN, GITHUB_OWNER, GITHUB_REPO, "_secretary/work-duties.md"),
    fetchFileText(GITHUB_TOKEN, GITHUB_OWNER, GITHUB_REPO, `_secretary/daily/${today}.md`),
    fetchFileText(GITHUB_TOKEN, GITHUB_OWNER, GITHUB_REPO, "_secretary/agenda.md"),
    fetchFileText(GITHUB_TOKEN, GITHUB_OWNER, GITHUB_REPO, "_secretary/kpi.md"),
  ]);
```

- [ ] **Step 5: 「できた」返信・「予定:」追記のハンドリングを追加**

`handleEvent` 内、`askRika` を呼ぶ前に:

```typescript
import { parseDoneReply, applyDoneMarks } from "./daily";
import { updateFileText } from "./github";
import { upsertAgendaReminders } from "./ingest"; // work/private 追記は別途。予定:行は末尾追記でよい

let sideEffectNote = "";

const done = parseDoneReply(userMessage);
if (done && daily) {
  await updateFileText(GITHUB_TOKEN, GITHUB_OWNER, GITHUB_REPO, `_secretary/daily/${today}.md`,
    (cur) => (cur ? applyDoneMarks(cur, done) : null),
    `宣言タスクの消化を記録 (${today})`);
  sideEffectNote = "\n（宣言の消化、記録したよ）";
}

const yotei = userMessage.match(/^予定[:：]\s*(.+)/);
if (yotei) {
  await updateFileText(GITHUB_TOKEN, GITHUB_OWNER, GITHUB_REPO, "_secretary/agenda.md",
    (cur) => {
      const base = cur ?? "# 予定・単発タスク\n";
      const header = `## ${today}`;
      if (base.includes(header)) {
        return base.replace(header, `${header}\n- ${yotei[1].trim()}`);
      }
      const h = base.indexOf("# 予定・単発タスク");
      const insertAt = h === -1 ? 0 : base.indexOf("\n", h) + 1;
      return base.slice(0, insertAt) + `\n${header}\n- ${yotei[1].trim()}\n` + base.slice(insertAt);
    },
    `LINEから予定を追記 (${today})`);
  sideEffectNote += "\n（予定、agendaに入れたよ）";
}
```

`replyMessage` に渡すテキストを `reply + sideEffectNote` にする。

- [ ] **Step 6: 型チェック＋テスト＋dev 確認**

Run: `cd ~/開発/agent/rika-line-bot && npm run typecheck && npm test`
Expected: 型エラーなし、既存テスト PASS

`npm run dev` で、LINE 署名付きの擬似 POST（既存の README / memory `secretary-agent-build` にある `openssl dgst -sha256 -hmac` の手順）を使って `予定: 明日15時 会議` を送り、`agenda.md` に追記されること・返信に「予定、agendaに入れたよ」が付くことを確認。**本人のLINEに実際に返信が飛ぶ**ため、事前に一言確認する。

- [ ] **Step 7: コミット**

```bash
cd ~/開発/agent && git add rika-line-bot/ && git commit -m "rika-line-bot: 対話に日次コンテキスト(daily/agenda/kpi/work-duties/profile)を追加、できた返信と予定追記を処理

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

## Task 10: rika-line-bot をデプロイし、秘密を登録

**Files:**
- Modify: `~/開発/agent/rika-line-bot/`（デプロイのみ、コード変更なし）

**Interfaces:**
- Consumes: Task 3〜9 の全変更
- Produces: `https://rika-line-bot.9nago-nago9.workers.dev` に新 cron ＋ `/ingest` が反映された状態

- [ ] **Step 1: `INGEST_SECRET` を生成して登録**

```bash
cd ~/開発/agent/rika-line-bot
SECRET=$(openssl rand -hex 24)
echo "INGEST_SECRET=$SECRET  ← Task 12 のショートカット手順で使う。安全な場所に控える"
printf '%s' "$SECRET" | npx wrangler secret put INGEST_SECRET
```

`CLOUDFLARE_API_TOKEN` が必要（sandbox では OAuth 不可）。Cloudflare ダッシュボードで既存トークン「リカラインボット」をロールして取得し、環境変数で渡す（memory `secretary-agent-build` の手順）。ユーザーに `! npx wrangler login` を依頼する手もある。

- [ ] **Step 2: デプロイ**

```bash
cd ~/開発/agent/rika-line-bot && npm run deploy
```

Expected: `Deployed rika-line-bot ... crons: 20 22 * * *, 0 4 * * *, 50 12 * * *, 20 9 * * 5`

- [ ] **Step 3: `/ingest` を本番で疎通確認**

```bash
curl -s -X POST https://rika-line-bot.9nago-nago9.workers.dev/ingest \
  -H "X-Ingest-Secret: $SECRET" -H "Content-Type: application/json" \
  -d '{"type":"reminders","items":["(疎通テスト)"]}' ; echo
```

Expected: `{"ok":true,"result":"updated" or "created"}`。`video-notes/_secretary/agenda.md` に当日ブロックができる。確認後、テスト行は次の実運用で上書きされるので放置でよい（気になれば手で消してコミット）。

- [ ] **Step 4: cron を1つ手動発火して LINE 到達を確認**

Cloudflare ダッシュボード（Workers → rika-line-bot → Triggers → Cron の "Trigger" ボタン）か、`wrangler` の scheduled テスト機能で `0 4 * * *`（昼ping）を発火。daily ファイルが無ければ「no daily file」でスキップされる。Task 11 で daily を作ってから再確認でもよい。

- [ ] **Step 5: 変更をコミット（既にコミット済みなら skip）** — このタスクにコード変更なし。デプロイのみ。

---

## Task 11: クラウドルーティン（朝・夜）を作成

**Files:**
- なし（`RemoteTrigger` API 操作。プロンプト全文はこのタスク内に記載）

**Interfaces:**
- Consumes: `_secretary/*.md`（Task 1/2 で作成済みであること）
- Produces:
  - ルーティン「りかちゃん 朝ブリーフィング」cron `0 22 * * *`
  - ルーティン「りかちゃん 夜ふりかえり」cron `30 12 * * *`
  - 両方 `_secretary/daily/<今日>.md` を生成/追記して push

- [ ] **Step 1: 既存ルーティンから environment_id と source 形を確認**

```
RemoteTrigger action:list
```

`env_018JLnu98AphHR6nuD8Md58N` と `sources: [{ type: "git_repository", url: "https://github.com/mu-mumu-com/video-notes" }]` を確認。

- [ ] **Step 2: 朝ルーティンを enabled:false で作成**

`RemoteTrigger action:create` の body（`cron_expression: "0 22 * * *"`、`session_request.config` に `allowed_tools: ["Bash","Read","Write","Edit","Glob","Grep"]`、`model: "claude-sonnet-5"`、`sources` は video-notes のみ、`environment_id: "env_018JLnu98AphHR6nuD8Md58N"`、`enabled: false`）。プロンプト本文:

```
あなたは「りかちゃん」。ユーザーの朝の相棒兼マネージャーです。今日の朝ブリーフィングを作ります。

前提:
- 本業は月〜金のみ。副業・プライベートは毎日。
- 決めてあげる＋励ますトーン。詰問・ダメ出しはしない。できなかった日を責めず淡々と繰り越す。
- この環境はGitHub以外への外部通信不可。カレントにvideo-notesがチェックアウトされている。

手順:
1. `TZ=Asia/Tokyo date "+%Y-%m-%d %a"` で今日の日付・曜日(JST)を確認。土日か平日かを判定。
2. 次のファイルを読む: _secretary/work-duties.md, _secretary/agenda.md, _secretary/fukugyo-roadmap.md, _secretary/projects.md, _secretary/kpi.md, _secretary/profile.md, _secretary/daily/<昨日の日付>.md（無ければスキップ）
3. profile.md の「セルフマネジメントの傾向」を必ず踏まえる（優先順位と次の一手はりかちゃんが1つに決める。ユーザーに選ばせない）。
4. 【本業】ブロック（平日のみ。土日は「今日は本業休み。副業とプライベートに使える日」と書いてブロックごと省略）:
   - work-duties.md の行頭タグ [毎日]/[平日]/[月〜日]/[毎週]/[第N営業日]/[日付]/[月末] と今日の曜日・日付を照合し「今日該当」を列挙。
   - 今日/翌営業日が該当する週次業務、期日まで2〜3営業日以内の月次業務もここに含める。
   - agenda.md の当日ブロックの work: 行を「単発」に。
   - 「今日ここだけ守る」を本業から1点。
5. 【副業】ブロック（毎日）:
   - fukugyo-roadmap.md の「現在地」と未完チェックから、今日やる最優先を1つだけ決める。
   - 最初の30分でやる具体作業を1行。理由（ロードマップのどこに効くか）を1行。
6. 【プライベート】ブロック: agenda.md の当日ブロックの private: 行。
7. 昨日の daily に未消化（`## 宣言` の `- [ ]`）があれば、冒頭「繰り越し」として本業/副業の該当ブロックに再掲。
8. 【りかちゃんから】: 励まし＋今日の進め方を2〜3行。予定が薄い日は「本当にない？本業の締切は？リマインダー見た？昨日の積み残しは？」と具体的に聞く行を必ず入れる。
9. `## 宣言` セクションは、6/4/5で決めた「今日やること」を最大4件、`- [ ] ` のチェックボックスで書く。
10. `_secretary/daily/<今日の日付>.md` を、_secretary/daily/_TEMPLATE.md の構造（frontmatter, ## 朝, ## 宣言, ## 昼, ## 夜 の空見出し）に沿って作成する。## 昼 と ## 夜 は空見出しだけ置く（夜ルーティンが夜を埋める）。
11. `git add _secretary/daily/<今日>.md && git commit && git push`。通知はしない（LINEはbotが担当）。pushできなければレポート全文を最終回答に出す。
```

- [ ] **Step 3: 朝ルーティンを1回手動実行して生成物を確認**

```
RemoteTrigger action:run trigger_id:<朝のtrigger_id>
```

数分後 `RemoteTrigger action:list_runs` → `get_run_log` で成否確認。`video-notes` に `_secretary/daily/<今日>.md` が push されているか、3ブロックの体裁・トーン・チェックボックスを目視。おかしければ Step 2 のプロンプトを `RemoteTrigger action:update` で調整して再実行。

- [ ] **Step 4: 朝ルーティンを有効化**

```
RemoteTrigger action:update trigger_id:<朝> body:{"enabled": true}
```

- [ ] **Step 5: 夜ルーティンを enabled:false で作成**

`cron_expression: "30 12 * * *"`、他は朝と同じ。プロンプト本文:

```
あなたは「りかちゃん」。今日の夜のふりかえりを作ります。トーンは決めてあげる＋励ます。責めない。

手順:
1. `TZ=Asia/Tokyo date "+%Y-%m-%d %a"` で今日(JST)を確認。土日か平日か判定。
2. 読む: _secretary/daily/<今日>.md, _secretary/work-duties.md, _secretary/fukugyo-roadmap.md, _secretary/kpi.md, _secretary/profile.md
3. <今日>.md の ## 夜 セクションに、次を追記する（見出しは ### で）:
   - 「宣言タスクの消化」: ## 宣言 の `- [x]`/`- [ ]` を数えて「N/M 完了」。0件チェックなら「未確認（夜のLINEで聞く）」。
   - 「本業定期業務の消化確認」（平日のみ。土日は省略）: 今日該当した work-duties の定期業務を `- [ ] ` で列挙。botがLINEで「番号で返して」と聞く。
   - 「ロードマップ進捗」: fukugyo-roadmap.md のチェック差分・当日のvideo-notesコミットから1〜2行。
   - 「KPI」: kpi.md の最新「## 更新: <日付>」を見て、最終更新からの日数と数値の動きを1行。5日以上古ければ「そろそろ数字を教えて」。
   - 「明日の種」: 明日の副業で最初にやると良いことを1行。
   - 平日の夜のみ「翌営業日の予告」: 翌営業日に該当する週次業務、期日が近い月次業務を1行。金曜の夜は翌週分もまとめて。土日の夜は本業の予告を出さない。
4. `git add _secretary/daily/<今日>.md && git commit && git push`。通知しない。
```

- [ ] **Step 6: 夜ルーティンを手動実行して確認 → 有効化**

Step 3 と同じ手順。`## 夜` セクションが正しく追記されるか確認してから `enabled: true`。

- [ ] **Step 7: この計画・spec のリンクを memory 用に控える**

朝 trigger_id・夜 trigger_id・`INGEST_SECRET` の保管場所を、実装完了報告に含める（memory 更新は Task 13）。

---

## Task 12: iPhone ショートカットの手順書

**Files:**
- Create: `~/開発/agent/rika-line-bot/SHORTCUT.md`

**Interfaces:**
- Consumes: Task 10 でデプロイ済みの `/ingest` と `INGEST_SECRET`
- Produces: ユーザーが自分の iPhone で作るショートカットの手順（このリポジトリに記録）

- [ ] **Step 1: SHORTCUT.md を書く**

内容（spec の「9. iPhone ショートカット」を具体化）:

```markdown
# 朝のリマインダー取り込みショートカット

## 目的
毎朝6:50に「今日期限＋期限切れ」のリマインダーを rika-line-bot に送り、
りかちゃんの朝ブリーフィング(7:00生成)に含める。

## 事前準備
- リマインダーApp に本業用リスト（例『仕事』）を作り、本業タスクはそこに入れる
- rika-line-bot の INGEST_SECRET を手元に用意（デプロイ時に生成した48文字）

## 作成手順（ショートカットApp）
1. 「オートメーション」タブ → 「+」→「時刻」→ 毎日 6:50 →「すぐに実行」（実行時に尋ねない）
2. アクションを追加:
   a. 「リマインダーを探す」: 期限 が 今日 まで / 完了済み は 除外  → 変数「今日分」
   b. 「リマインダーを探す」: 期限 が 昨日 より前 / 完了済み は 除外 → 変数「延滞」
   c. 「リストを結合」(今日分, 延滞)
   d. 「それぞれと繰り返す」: 各リマインダーの「名前」を取り出し、テキストに改行区切りで追加
   e. 「テキスト」を「リストに分割」(改行) → 変数「items」
   f. 「辞書」を作る: type = reminders, items = 変数 items
   g. 「URLの内容を取得」:
      - URL: https://rika-line-bot.9nago-nago9.workers.dev/ingest
      - 方法: POST
      - ヘッダ: X-Ingest-Secret = <INGEST_SECRET>
      - 本文: JSON = 上の辞書
3. 一度手動実行して、`{"ok":true,...}` が返ることを確認

## メンテ
- 本文の items が空でもエラーにはならない（その日はリマインダー無しとして扱われる）
- URL や secret を変えたらこのショートカットも更新する
```

- [ ] **Step 2: コミット**

```bash
cd ~/開発/agent && git add rika-line-bot/SHORTCUT.md && git commit -m "rika-line-bot: iPhoneショートカット作成手順(SHORTCUT.md)を追加

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

- [ ] **Step 3: ユーザーに手順書を渡す**

`SHORTCUT.md` の内容と `INGEST_SECRET` をユーザーに提示し、iPhone 側で作ってもらう（この計画の実行者はここまで）。

---

## Task 13: agent/secretary/CLAUDE.md の拡張と memory 更新

**Files:**
- Modify: `~/開発/agent/secretary/CLAUDE.md`
- Modify: `~/.claude/projects/-Users-nagomutsuhiro/memory/rika-mentor-secretary-design.md`
- Modify: `~/.claude/projects/-Users-nagomutsuhiro/memory/MEMORY.md`（必要なら1行追加）

**Interfaces:**
- Consumes: 全タスクの成果
- Produces: ローカルでりかちゃんを呼んだ時に日次マネージャーとして振る舞えるペルソナ定義、次セッション用の記録

- [ ] **Step 1: secretary/CLAUDE.md に節を追加**

- 「朝夜ブリーフィングの枠組み」節: クラウドルーティンと同じ3ブロック構成・トーン。ローカルで呼ばれた時は追加で **Google カレンダー（`mcp__claude_ai_Google_Calendar__*`）と Mac のリマインダー**（`shortcuts run` か AppleScript、`reminders` CLI があればそれ）を読んで agenda.md に無い予定も反映する。
- 「マネージャーとして決定を引き取る」を基本姿勢に追加（profile.md の新節と対応）。
- 読み込みファイルに `work-duties.md` / `agenda.md` / `kpi.md` / `daily/<今日>.md` を追加。
- 「本業は月〜金、副業・プライベートは毎日」を明記。

- [ ] **Step 2: typecheck 相当（Markdown なので目視）＋コミット**

```bash
cd ~/開発/agent && git add secretary/CLAUDE.md && git commit -m "secretary: りかちゃんに日次マネージャーの枠組みを追加

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>" && git push
```

- [ ] **Step 3: memory を更新**

`rika-mentor-secretary-design.md` に「2026-09-09: 日次マネージャー化」節を追加。含める情報: 朝夜クラウドルーティンの trigger_id、朝7:00/夜21:30 JST、bot の新 cron（朝リレー7:20・昼ping13:00・夜リレー21:50）、`INGEST_SECRET` の保管場所、月次チェックイン廃止、`_secretary/` の新ファイル（work-duties/agenda/kpi/daily）、spec と plan のパス、稼働スケジュール前提（本業=平日、副業/プライベート=毎日）、iPhoneショートカットはユーザー作成待ちか完了か。

- [ ] **Step 4: video-notes に spec/plan の最終状態を push（未実施なら）**

```bash
cd ~/開発/video-notes && git add _secretary/ && git commit -m "りかちゃん日次マネージャー: 実装で追加したデータファイルとテンプレートを反映

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>" && git fetch origin && git rebase --autostash origin/main && git push origin main
```

- [ ] **Step 5: 実装完了レポート**

ユーザーに次を伝える: 稼働開始日、朝昼夜の時刻、iPhoneショートカットの残作業、work-duties.md/kpi.md の中身をヒアリングで埋める必要があること（Task 1 でプレースホルダのままなら）、2〜3日運用して時刻・トーン・情報量を調整する提案。

---

## Self-Review

**1. Spec coverage:**

| spec 要素 | 対応タスク |
|---|---|
| work-duties.md / agenda.md / kpi.md / daily/ | Task 1 |
| profile.md セルフマネジメント節 | Task 2 |
| 朝ルーティン（クラウド） | Task 11 Step 2-4 |
| 夜ルーティン（クラウド） | Task 11 Step 5-6 |
| bot 朝リレー / 昼ping / 夜リレー | Task 8 |
| /ingest エンドポイント | Task 7, Task 10 |
| webhook 双方向対話の日次コンテキスト化・プロンプトキャッシュ | Task 9 |
| 「できた」返信でチェック更新 / 「予定:」で agenda 追記 | Task 9 Step 5 |
| 月次チェックイン廃止 | Task 8 Step 3 |
| iPhone ショートカット | Task 12 |
| agent/secretary/CLAUDE.md 拡張（ローカル時のカレンダー/リマインダー参照含む） | Task 13 |
| 稼働スケジュール（本業=平日、副業/私=毎日、土日は本業省略） | Task 3(判定関数), Task 8(pingは毎日), Task 11(プロンプトで分岐) |
| 事前の作業ツリー整理 | Task 0 |
| コスト方針（定型pushはAPI呼ばない） | Task 8（buildX系は純関数、API呼び出しなし） |
| セキュリティ（INGEST_SECRET を secret 登録、機密を書かない） | Task 1, Task 7, Task 10 |

ギャップ: 「翌営業日の週次業務リマインドを朝/夜どちらに寄せるか（二重通知回避）」は spec の未確定点。→ Task 11 で夜ルーティンのプロンプトに「翌営業日の予告」を持たせ、朝ルーティンは「今日該当」のみ扱う形で分離済み（重複しない）。

**2. Placeholder scan:** `work-duties.md` / `kpi.md` の `〈例〉` は「テンプレートのプレースホルダを置き、Task 9 or 実運用でユーザーヒアリングして実データに差し替える」と明記済みで、プラン上の TODO ではなく成果物の仕様。コードステップはすべて実コードを記載。

**3. Type consistency:**
- `todayJst` — Task 3 で定義、Task 4/5/7/8/9 で使用。一致。
- `nowJstStamp` — Task 3 で定義、既存 `nowJst` エイリアスで scheduled/webhook が使用。
- `buildMorningPush` / `buildMiddayPush` / `buildEveningPush` / `dailyPath` — Task 4 定義、Task 8 使用。名前一致。
- `parseDoneReply` の戻り値 `number[] | "all" | null` — Task 4 定義、Task 9 で `applyDoneMarks(cur, done)` に渡す。`applyDoneMarks` の引数も `number[] | "all"`。一致。
- `updateFileText` の戻り値 `"updated" | "nochange" | "created"` — Task 6 定義、Task 7/9 で使用。
- `upsertAgendaReminders(current, dateStr, items)` — Task 5 定義、Task 7 で使用。Task 9 の「予定:」追記は別ロジック（agenda 末尾 upsert）でこの関数は使わない（import はするが未使用なら消す）。→ Task 9 Step 5 の import 行から `upsertAgendaReminders` を削除し、インラインの transform で処理する旨に修正済み。
- `parseIngestBody` — Task 5 定義、Task 7 使用。
- `AGENDA_PATH` — Task 5 定義、Task 7 使用。

修正: Task 9 Step 5 のコード内 `import { upsertAgendaReminders } from "./ingest";` はコメントで「予定:行は末尾追記でよい」としつつ未使用。実装時は import しない。

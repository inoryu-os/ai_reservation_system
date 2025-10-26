# config.js と timezone.js - 設定とタイムゾーン処理

## 概要
フロントエンド（ブラウザ側）の基本設定とタイムゾーン処理を担当する2つのユーティリティモジュールです。

## 1. config.js - 設定ファイル

### 役割
- 時間関連の設定を一元管理
- システム全体で使用する定数を定義

### コードの詳細

```javascript
export const TIME = {
  startHour: 7,      // 営業開始時刻
  endHour: 22,       // 営業終了時刻
  stepMinutes: 30,   // 時間刻み（30分単位）
};
```

**説明:**
- `startHour`: 予約可能な開始時刻（7時）
- `endHour`: 予約可能な終了時刻（22時）
- `stepMinutes`: 時間の刻み幅（30分）

**使用箇所:**
- `formUI.js`: 時刻セレクトボックスの選択肢生成
- `reservationTable.js`: 予約表の時間スロット生成

**初心者向けポイント:**
- `export`キーワードで他のファイルから使えるように公開
- ES6モジュールの機能を使用

### 使用例

```javascript
import { TIME } from "./config.js";

console.log(TIME.startHour);  // 7
console.log(TIME.stepMinutes); // 30

// 時刻の選択肢を生成
for (let hour = TIME.startHour; hour <= TIME.endHour; hour++) {
  for (let minute = 0; minute < 60; minute += TIME.stepMinutes) {
    console.log(`${hour}:${minute}`);
  }
}
```

---

## 2. timezone.js - タイムゾーン処理ユーティリティ

### 役割
- JST（日本標準時）での日時処理
- ブラウザのローカルタイムをJSTに変換
- 日時の文字列フォーマット

### なぜ必要？

ブラウザは、ユーザーのパソコンのタイムゾーンで時刻を扱います。
例えば、アメリカからアクセスすると、システムがおかしくなる可能性があります。
そのため、常にJST（日本時間）で統一して扱います。

### コードの詳細

#### 1. JST定数

```javascript
const JST_OFFSET = 9 * 60; // 分単位（9時間 = 540分）
```

**説明:**
- UTC（協定世界時）から+9時間がJST
- 分単位で計算するため`9 * 60 = 540`分

#### 2. 現在のJST時刻を取得

```javascript
export function getJSTNow() {
  const now = new Date();
  return convertToJST(now);
}
```

**使用例:**
```javascript
const jstNow = getJSTNow();
console.log(jstNow); // 2025-01-15 14:30:00 (JST)
```

#### 3. DateオブジェクトをJSTに変換

```javascript
export function convertToJST(date) {
  const utc = date.getTime() + (date.getTimezoneOffset() * 60000);
  return new Date(utc + (JST_OFFSET * 60000));
}
```

**処理の流れ:**
1. `date.getTime()`: ミリ秒のタイムスタンプ取得
2. `date.getTimezoneOffset()`: ローカルとUTCの時差（分）
3. UTCに変換してから、JSTオフセット（+9時間）を加算

**初心者向けポイント:**
- `getTimezoneOffset()`: 正の値の場合、UTCより遅れている
- 例: 日本は`-540`（UTCより540分進んでいる）
- `60000`: 1分 = 60秒 × 1000ミリ秒

**図解:**
```
ローカルタイム（例: アメリカ東部 UTC-5）
    ↓ getTime() + getTimezoneOffset()
UTC (協定世界時)
    ↓ + JST_OFFSET (9時間)
JST (日本標準時)
```

#### 4. 日付文字列へのフォーマット

```javascript
export function formatJSTDate(jstDate) {
  const year = jstDate.getFullYear();
  const month = String(jstDate.getMonth() + 1).padStart(2, '0');
  const day = String(jstDate.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}
```

**使用例:**
```javascript
const jstNow = getJSTNow();
const dateStr = formatJSTDate(jstNow);
console.log(dateStr); // "2025-01-15"
```

**初心者向けポイント:**
- `getMonth()`: 0-11なので+1が必要
- `padStart(2, '0')`: 1桁の場合は先頭に0を追加
  - 例: `"5"` → `"05"`
- テンプレートリテラル（`` `${変数}` ``）で文字列を結合

#### 5. 時刻文字列へのフォーマット

```javascript
export function formatJSTTime(jstDate) {
  const hours = String(jstDate.getHours()).padStart(2, '0');
  const minutes = String(jstDate.getMinutes()).padStart(2, '0');
  return `${hours}:${minutes}`;
}
```

**使用例:**
```javascript
const jstNow = getJSTNow();
const timeStr = formatJSTTime(jstNow);
console.log(timeStr); // "14:30"
```

#### 6. 今日の日付をJSTで取得

```javascript
export function getTodayJST() {
  return formatJSTDate(getJSTNow());
}
```

**使用例:**
```javascript
const today = getTodayJST();
console.log(today); // "2025-01-15"

// フォームの日付入力のデフォルト値に設定
document.getElementById('date-select').value = getTodayJST();
```

#### 7. 表示用の文字列を生成

```javascript
export function getJSTDisplayString() {
  const jstNow = getJSTNow();
  const year = jstNow.getFullYear();
  const month = jstNow.getMonth() + 1;
  const day = jstNow.getDate();
  const time = formatJSTTime(jstNow);
  return `${year}年${month}月${day}日 ${time} (JST)`;
}
```

**使用例:**
```javascript
const displayStr = getJSTDisplayString();
console.log(displayStr); // "2025年1月15日 14:30 (JST)"
```

## 関数一覧まとめ

| 関数名 | 引数 | 戻り値 | 用途 |
|-------|------|--------|------|
| getJSTNow() | なし | Date | 現在のJST時刻を取得 |
| convertToJST() | Date | Date | DateオブジェクトをJSTに変換 |
| formatJSTDate() | Date | string | 日付文字列に変換 (YYYY-MM-DD) |
| formatJSTTime() | Date | string | 時刻文字列に変換 (HH:MM) |
| getTodayJST() | なし | string | 今日の日付を取得 (YYYY-MM-DD) |
| getJSTDisplayString() | なし | string | 表示用の文字列を生成 |

## 実際の使用例

### 例1: フォームの日付初期化

```javascript
import { getTodayJST } from "./timezone.js";

// ページ読み込み時に今日の日付を設定
const dateInput = document.getElementById('date-select');
dateInput.value = getTodayJST();  // "2025-01-15"
```

### 例2: 予約表のタイトル表示

```javascript
import { getJSTNow, formatJSTTime } from "./timezone.js";

const jstNow = getJSTNow();
const year = jstNow.getFullYear();
const month = jstNow.getMonth() + 1;
const day = jstNow.getDate();

const titleEl = document.getElementById('booking-table-date');
titleEl.textContent = `今日 (${year}年${month}月${day}日)`;
```

### 例3: 時刻セレクトボックスの生成

```javascript
import { TIME } from "./config.js";

function generateTimeOptions() {
  const options = [];

  for (let hour = TIME.startHour; hour <= TIME.endHour; hour++) {
    for (let minute = 0; minute < 60; minute += TIME.stepMinutes) {
      if (hour === TIME.endHour) break; // 終了時刻では終了

      const h = String(hour).padStart(2, '0');
      const m = String(minute).padStart(2, '0');
      const timeStr = `${h}:${m}`;

      options.push({ value: timeStr, text: timeStr });
    }
  }

  return options;
}

// 結果: ["07:00", "07:30", "08:00", ..., "21:30"]
```

## JavaScriptのDateオブジェクトについて

### Dateオブジェクトの基本

```javascript
// 現在時刻
const now = new Date();

// 特定の日時
const specificDate = new Date(2025, 0, 15, 14, 30);
// 注意: 月は0-11 (0=1月, 11=12月)

// 日付の取得
now.getFullYear();   // 2025
now.getMonth();      // 0-11
now.getDate();       // 1-31
now.getHours();      // 0-23
now.getMinutes();    // 0-59
now.getSeconds();    // 0-59
```

### タイムスタンプ

```javascript
// 1970年1月1日からのミリ秒
const timestamp = now.getTime();
console.log(timestamp); // 1705303800000

// タイムスタンプからDate
const date = new Date(timestamp);
```

## ES6モジュールについて

### エクスポート（公開）

```javascript
// 名前付きエクスポート
export const TIME = { ... };
export function getJSTNow() { ... }

// または
const TIME = { ... };
function getJSTNow() { ... }
export { TIME, getJSTNow };
```

### インポート（使用）

```javascript
// 特定の関数をインポート
import { getJSTNow, formatJSTDate } from "./timezone.js";

// すべてをインポート
import * as Timezone from "./timezone.js";
// 使用: Timezone.getJSTNow()
```

## 学習のポイント

1. **タイムゾーンの重要性**
   - グローバルなシステムではタイムゾーン管理が必須
   - JSTで統一することで混乱を防ぐ

2. **Dateオブジェクトの扱い**
   - ミリ秒単位のタイムスタンプで計算
   - getTimezoneOffset()でローカルタイムゾーンを考慮

3. **文字列フォーマット**
   - padStart()で0埋め
   - テンプレートリテラルで読みやすく

4. **モジュール化**
   - 関連する機能をファイルにまとめる
   - export/importで再利用性を高める

5. **定数の外部化**
   - configファイルで設定を一元管理
   - 変更時の修正箇所を減らす

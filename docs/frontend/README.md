# フロントエンド解説ドキュメント

## はじめに

このディレクトリには、会議室予約システムのフロントエンド（ブラウザ側）の詳細な解説ドキュメントが含まれています。
JavaScriptモジュール、HTML、CSSの役割と実装を丁寧に説明しています。

## システム構成

### 全体アーキテクチャ

```
[ブラウザ]
    │
    ├─ index.html (HTMLテンプレート)
    │
    ├─ CSS (スタイル)
    │   ├─ layout.css (レイアウト)
    │   ├─ calendar.css (カレンダー)
    │   ├─ reservation.css (予約表)
    │   └─ chat.css (チャット)
    │
    └─ JavaScript (ロジック)
        ├─ main.js (エントリーポイント)
        ├─ config.js (設定)
        ├─ timezone.js (タイムゾーン処理)
        ├─ api.js (API通信)
        ├─ formUI.js (予約フォーム)
        ├─ calendar.js (カレンダー)
        ├─ reservationTable.js (予約表)
        └─ chat.js (AIチャット)
```

### モジュール構成図

```
main.js (初期化)
    │
    ├─ ReservationTable (予約表)
    │   └─ api.js (API通信)
    │
    ├─ ReservationFormUI (予約フォーム)
    │   ├─ api.js
    │   └─ timezone.js
    │
    ├─ CompactCalendar (カレンダー)
    │   ├─ api.js
    │   └─ timezone.js
    │
    └─ ChatManager (AIチャット)
        └─ (独立したモジュール)
```

## ドキュメント一覧

### 1. 基本ユーティリティ

| ファイル | 説明 | 難易度 |
|---------|------|-------|
| [01_config_timezone.md](01_config_timezone.md) | 設定とタイムゾーン処理 | ★☆☆ |
| [02_api.md](02_api.md) | API通信モジュール | ★★☆ |

**学べること:**
- ES6モジュールの基本
- タイムゾーン処理
- Fetch APIによるHTTP通信
- async/awaitの使い方

### 2. UI コンポーネント

| 機能 | 説明 | 主要ファイル |
|-----|------|------------|
| 予約フォーム | formUI.js | 予約作成フォームの制御 |
| カレンダー | calendar.js | 月表示カレンダー |
| 予約表 | reservationTable.js | 時間割形式の予約表示 |
| AIチャット | chat.js | チャットボットUI |

### 3. HTML/CSS

| ファイル | 説明 |
|---------|------|
| index.html | メインのHTMLテンプレート |
| layout.css | 全体レイアウト |
| calendar.css | カレンダーのスタイル |
| reservation.css | 予約表のスタイル |
| chat.css | チャットのスタイル |

## 主要な機能と技術

### 1. ES6モジュール

**export/import**
```javascript
// config.js
export const TIME = { startHour: 7, endHour: 22 };

// formUI.js
import { TIME } from "./config.js";
```

**メリット:**
- コードの分割と再利用
- 名前空間の分離
- 依存関係の明確化

### 2. クラスベースの設計

```javascript
class ReservationFormUI {
  constructor() {
    this.form = document.getElementById("reservation-form");
    this.init();
  }

  init() {
    // 初期化処理
  }

  handleSubmit(event) {
    // イベント処理
  }
}
```

**メリット:**
- 関連する機能をまとめられる
- 状態（プロパティ）と振る舞い（メソッド）を一体化
- オブジェクト指向プログラミング

### 3. イベント委譲

```javascript
// 個別にイベントリスナーを設定するのではなく
document.addEventListener("click", (e) => {
  if (e.target.classList.contains("cancel-btn")) {
    // キャンセルボタンのクリック処理
  }
});
```

**メリット:**
- 動的に追加された要素にも対応
- メモリ効率が良い

### 4. 非同期処理

```javascript
async function loadReservations() {
  const result = await getReservationsByDate(date);
  if (result.success) {
    displayReservations(result.reservations);
  }
}
```

### 5. DOM操作

```javascript
// 要素の取得
const element = document.getElementById('id');
const elements = document.querySelectorAll('.class');

// 要素の作成と追加
const div = document.createElement('div');
div.textContent = 'Hello';
parent.appendChild(div);

// クラスの操作
element.classList.add('active');
element.classList.remove('inactive');
element.classList.toggle('visible');
```

## データフロー例

### 予約作成の流れ

```
[ユーザー] フォーム入力
    ↓
[formUI.js] handleSubmit()
    │ フォームデータを取得
    ↓
[api.js] createReservation()
    │ POST /api/reservations
    ↓
[バックエンド] 予約を保存
    │
    ↓
[formUI.js] 結果を受信
    │
    ↓
[reservationTable.js] 予約表を更新
    ↓
[ユーザー] 予約が表示される
```

### カレンダー選択の流れ

```
[ユーザー] カレンダーの日付をクリック
    ↓
[calendar.js] selectDate()
    │ 選択状態を保存
    │ カレンダーを再描画
    ↓
[calendar.js] updateReservationTable()
    │
    ↓
[api.js] getReservationsByDate()
    │ GET /api/reservations/2025-01-15
    ↓
[バックエンド] 予約データを返す
    │
    ↓
[reservationTable.js] 予約を表示
    ↓
[formUI.js] 日付入力フォームを更新
    ↓
[ユーザー] 選択した日の予約が表示される
```

### AIチャットの流れ

```
[ユーザー] メッセージ入力
    ↓
[chat.js] handleSubmit()
    │ メッセージを表示
    ↓
[chat.js] fetch('/api/chat')
    │ POST { message, sessionId }
    ↓
[バックエンド] AI処理
    │
    ↓
[chat.js] AI応答を受信
    │ メッセージを表示
    ↓
[予約作成の場合]
    ├─ カレンダーを移動
    └─ 予約表を更新
    ↓
[ユーザー] AI応答と更新されたUIを確認
```

## 技術スタック

### ライブラリ・フレームワーク

| 技術 | バージョン | 用途 |
|-----|----------|------|
| Vanilla JavaScript | ES6+ | プログラミング言語 |
| Bootstrap 5 | 5.3.0 | CSSフレームワーク |
| Font Awesome | 6.4.0 | アイコン |

### ブラウザAPI

| API | 用途 |
|-----|------|
| Fetch API | HTTP通信 |
| DOM API | HTML要素の操作 |
| LocalStorage API | セッションID保存 |
| Crypto API | UUID生成 |

## コーディング規約

### 命名規則

```javascript
// クラス: PascalCase
class ReservationTable { }

// 関数: camelCase
function getTodayJST() { }

// 定数: UPPER_SNAKE_CASE
const API_ENDPOINTS = { };

// 変数: camelCase
const userName = 'guest';
```

### ファイル構成

```
static/
├── js/
│   ├── config.js         # 設定
│   ├── timezone.js       # ユーティリティ
│   ├── api.js            # API通信
│   ├── formUI.js         # UIコンポーネント
│   ├── calendar.js       # UIコンポーネント
│   ├── reservationTable.js # UIコンポーネント
│   ├── chat.js           # 独立機能
│   └── main.js           # エントリーポイント
└── css/
    ├── layout.css
    ├── calendar.css
    ├── reservation.css
    └── chat.css
```

## 主要な概念

### 1. Single Page Application (SPA)

ページ遷移なしで画面を更新するアプリケーション。

**実装:**
- `fetch()`でデータ取得
- JavaScriptでDOMを更新
- 高速で滑らかなUX

### 2. コンポーネント指向

機能ごとにクラスとして分離。

**例:**
- `ReservationFormUI`: フォーム関連
- `CompactCalendar`: カレンダー関連
- `ChatManager`: チャット関連

### 3. グローバル変数の最小化

```javascript
// main.js
window.ReservationTable = reservationTable;
window.CompactCalendar = compactCalendar;
// 必要最小限のみをグローバルに公開
```

### 4. イベントドリブン

ユーザーの操作に応じて処理を実行。

```javascript
button.addEventListener('click', handleClick);
form.addEventListener('submit', handleSubmit);
input.addEventListener('input', handleInput);
```

## Bootstrap 5について

このシステムでは、Bootstrap 5を使用しています。

**主な機能:**
- **グリッドシステム**: レスポンシブレイアウト
  ```html
  <div class="row">
    <div class="col-lg-8">左側</div>
    <div class="col-lg-4">右側</div>
  </div>
  ```

- **コンポーネント**: カード、ボタン、フォームなど
  ```html
  <div class="card">
    <div class="card-header">ヘッダー</div>
    <div class="card-body">本文</div>
  </div>
  ```

- **ユーティリティクラス**: 余白、文字色など
  ```html
  <div class="p-3 mb-2 text-primary">
    padding: 1rem, margin-bottom: 0.5rem, color: blue
  </div>
  ```

## 学習の順序

### 初心者向け（5日間コース）

**Day 1: 基礎**
- HTML/CSS/JavaScript基本
- DOM操作
- イベントリスナー

**Day 2: モジュールとAPI**
- ES6モジュール
- Fetch API
- async/await

**Day 3: UIコンポーネント**
- クラスの作成
- イベント処理
- フォーム操作

**Day 4: データ連携**
- API通信
- データ表示
- エラーハンドリング

**Day 5: 統合**
- モジュール間の連携
- グローバル変数
- デバッグ

### 中級者向け（2日集中）

**Day 1:**
- 全モジュールの構造理解
- データフローの把握
- Bootstrap 5の活用

**Day 2:**
- 実際のコード改造
- 機能追加
- デバッグとテスト

## デバッグのヒント

### 1. ブラウザの開発者ツール

```javascript
// コンソール出力
console.log('変数:', variable);
console.error('エラー:', error);

// ブレークポイント
debugger; // この行で実行が一時停止
```

### 2. ネットワークタブ

- APIリクエスト/レスポンスを確認
- ステータスコード、ヘッダー、ボディを見る

### 3. Elementsタブ

- DOM構造の確認
- CSS適用状況の確認
- 動的に変更して試す

## よくある問題と解決法

### Q1: モジュールが読み込めない
```
Uncaught SyntaxError: Cannot use import statement outside a module
```

**解決法:**
```html
<script type="module" src="main.js"></script>
```
`type="module"`を追加。

### Q2: CORSエラー
```
Access to fetch at '...' has been blocked by CORS policy
```

**解決法:**
- バックエンドでCORS設定を有効化
- または同じドメインでフロントとバックを動かす

### Q3: イベントが動かない

**確認事項:**
- 要素が存在するか？
- DOMContentLoadedの後か？
- イベント名は正しいか？

## 次のステップ

1. **コードを読む**: 実際のコードを確認
2. **動かしてみる**: ブラウザで動作確認
3. **改造する**: 機能追加や変更
4. **デバッグする**: 開発者ツールで調査

## 参考資料

- [MDN Web Docs](https://developer.mozilla.org/ja/)
- [Bootstrap 5公式](https://getbootstrap.jp/)
- [JavaScript.info](https://ja.javascript.info/)

## まとめ

このフロントエンドシステムの特徴:

1. **モダンなJavaScript**: ES6モジュール、クラス、async/await
2. **コンポーネント指向**: 機能ごとにクラスで分離
3. **API連携**: Fetch APIによる非同期通信
4. **レスポンシブ**: Bootstrap 5で様々な画面サイズに対応
5. **保守性**: モジュール化で変更に強い

各ドキュメントを読むことで、フロントエンド開発の基礎から実践まで学べます！

# HTML と CSS - UI構造とスタイル

## index.html - HTMLテンプレート

### 概要
会議室予約システムのメインHTMLファイルです。
Jinja2テンプレートエンジンを使用してFlaskから動的にデータを受け取ります。

### ページ構造

```
┌─────────────────────────────────────┐
│  ナビゲーションバー                    │
│  (XW0会議室予約 | guest)              │
├─────────────────────────────────────┤
│  ┌─────────────┬─────────────────┐  │
│  │ カレンダー   │  予約フォーム      │  │
│  │             │                 │  │
│  └─────────────┴─────────────────┘  │
│  ┌─────────────────────────────┐    │
│  │     予約表                   │    │
│  │  (時間割形式)                │    │
│  └─────────────────────────────┘    │
├─────────────────────────────────────┤
│  AIチャット                           │
│  (右側固定サイドバー)                  │
└─────────────────────────────────────┘
```

### 主要セクション

#### 1. ヘッダー（外部ライブラリ）

```html
<head>
  <!-- Bootstrap 5 CSS -->
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">

  <!-- Font Awesome (アイコン) -->
  <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">

  <!-- カスタムCSS -->
  <link href="{{ url_for('static', filename='css/calendar.css') }}" rel="stylesheet">
  <link href="{{ url_for('static', filename='css/reservation.css') }}" rel="stylesheet">
  <link href="{{ url_for('static', filename='css/layout.css') }}" rel="stylesheet">
</head>
```

**使用技術:**
- **Bootstrap 5**: CSSフレームワーク（レスポンシブ、コンポーネント）
- **Font Awesome**: アイコンフォント
- **Jinja2**: `{{ url_for() }}`でFlaskのURLを生成

#### 2. ナビゲーションバー

```html
<nav class="navbar navbar-expand-lg navbar-dark bg-primary">
  <div class="container-fluid">
    <a class="navbar-brand" href="/">
      <i class="fas fa-calendar-alt me-2"></i>
      XW0会議室予約
    </a>

    <div class="navbar-nav ms-auto">
      <div class="nav-item text-white">
        <i class="fas fa-user me-1"></i>
        <span>{{ user_name }}</span>
      </div>
    </div>
  </div>
</nav>
```

**Bootstrap クラス:**
- `navbar`: ナビゲーションバー
- `navbar-dark bg-primary`: 暗い背景に白文字
- `container-fluid`: 全幅のコンテナ
- `ms-auto`: 右寄せ（margin-start: auto）

**Jinja2テンプレート:**
- `{{ user_name }}`: Flaskから渡されたユーザー名を表示

#### 3. カレンダー

```html
<div class="card calendar-card">
  <div class="card-header d-flex justify-content-between align-items-center">
    <button class="btn btn-sm btn-outline-primary" id="prev-month">
      <i class="fas fa-chevron-left"></i>
    </button>
    <h2 class="mb-0 fw-bold h6" id="calendar-title">カレンダー</h2>
    <button class="btn btn-sm btn-outline-primary" id="next-month">
      <i class="fas fa-chevron-right"></i>
    </button>
  </div>

  <div class="card-body p-2">
    <table class="table table-sm calendar-table">
      <thead>
        <tr class="text-center">
          <th class="text-danger">日</th>
          <th>月</th>
          <th>火</th>
          <th>水</th>
          <th>木</th>
          <th>金</th>
          <th class="text-primary">土</th>
        </tr>
      </thead>
      <tbody></tbody>  <!-- JavaScriptで動的に生成 -->
    </table>
  </div>
</div>
```

**Bootstrapカード:**
- `card`: カード型コンポーネント
- `card-header`: ヘッダー部分
- `card-body`: 本文部分

**テーブル:**
- `<tbody></tbody>`: 空 → JavaScriptで日付ボタンを動的生成

#### 4. 予約フォーム

```html
<form id="reservation-form" autocomplete="off">
  <div class="row mb-3">
    <div class="col-md-6">
      <label for="room-select" class="form-label">会議室</label>
      <select id="room-select" name="room-id" class="form-select" required>
        <option value="">選択してください</option>
        {% for room in rooms %}
        <option value="{{ room.id }}">{{ room.name }} ({{ room.capacity }}名)</option>
        {% endfor %}
      </select>
    </div>
  </div>

  <div class="row g-3 mb-3">
    <div class="col-md-4">
      <label for="date-select" class="form-label">日付</label>
      <input type="date" id="date-select" name="date" class="form-control" required>
    </div>
    <div class="col-md-4">
      <label for="start-time" class="form-label">開始時刻</label>
      <select id="start-time" name="start-time" class="form-select" required>
        <!-- JavaScriptで動的に生成 -->
      </select>
    </div>
    <div class="col-md-4">
      <label for="end-time" class="form-label">終了時刻</label>
      <select id="end-time" name="end-time" class="form-select" required>
        <!-- JavaScriptで動的に生成 -->
      </select>
    </div>
  </div>

  <button type="submit" class="btn btn-primary" id="reserve-btn">
    <i class="fas fa-calendar-plus me-2"></i>
    予約する
  </button>
</form>
```

**Jinja2ループ:**
```html
{% for room in rooms %}
  <option value="{{ room.id }}">{{ room.name }} ({{ room.capacity }}名)</option>
{% endfor %}
```
→ Pythonのリストをループして選択肢を生成

**Bootstrapグリッド:**
- `row`: 行
- `col-md-4`: 中画面以上で12分の4（3列）
- `g-3`: gutter（列間の余白）

#### 5. 予約表

```html
<table class="table table-bordered booking-table">
  <thead class="table-info">
    <tr>
      <th style="width: 80px;">時間</th>
      {% for room in rooms %}
      <th class="text-center room-header" data-room-id="{{room.id}}">
        {{room.name}}<br><small>{{room.capacity}}名</small>
      </th>
      {% endfor %}
    </tr>
  </thead>
  <tbody id="booking-table-body">
    <!-- JavaScriptで動的に生成 -->
  </tbody>
</table>
```

**data属性:**
```html
data-room-id="{{room.id}}"
```
→ JavaScriptから `element.dataset.roomId` でアクセス可能

#### 6. AIチャット

```html
<div class="card chat-card">
  <div class="card-header">
    <h2 class="h6">
      <i class="fas fa-robot me-2"></i>
      AIアシスタント
    </h2>
    <button class="btn btn-sm btn-outline-primary" id="clear-chat">
      <i class="fas fa-trash-alt"></i>
    </button>
  </div>

  <div class="card-body p-0 chat-container">
    <!-- チャット履歴 -->
    <div class="chat-messages" id="chat-messages">
      <div class="message ai-message">
        <div class="message-content">
          <i class="fas fa-robot me-2"></i>
          開始時刻と利用時間を送ると、AIが空いている会議室を探します。
        </div>
      </div>
    </div>

    <!-- チャット入力 -->
    <div class="chat-input-container border-top p-2">
      <form id="chat-form">
        <div class="d-flex">
          <input type="text" id="chat-input" class="form-control" placeholder="メッセージを入力...">
          <button type="submit" class="btn btn-primary ms-2" id="chat-send-btn" disabled>
            <i class="fas fa-paper-plane"></i>
          </button>
        </div>
      </form>
    </div>
  </div>
</div>
```

**アクセシビリティ:**
```html
<label for="chat-input" class="visually-hidden">メッセージを入力</label>
```
→ スクリーンリーダー用のラベル（画面には表示されない）

#### 7. JavaScriptの読み込み

```html
<!-- ユーザー名をJavaScriptに渡す -->
<script>
  window.CURRENT_USER_NAME = "{{ user_name }}";
</script>

<!-- ES6モジュールとして読み込み -->
<script type="module" src="{{ url_for('static', filename='js/main.js') }}"></script>
```

**ポイント:**
- `type="module"`: ES6モジュールとして実行
- グローバル変数でPythonからJavaScriptにデータを渡す

---

## CSS - スタイリング

### layout.css - 全体レイアウト

#### ビューポート高さベースのレイアウト

```css
body, html {
  height: 100%;
  overflow: hidden;  /* スクロールバーを非表示 */
}

main.container-fluid {
  height: calc(100vh - 56px);  /* ナビゲーションバーの高さ分引く */
  overflow: hidden;
}
```

**calc()関数:**
- `100vh`: ビューポート高さの100%
- `56px`: ナビゲーションバーの高さ
- 残りの高さを計算

#### 左右分割レイアウト

```css
.left-main-column {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.right-chat-column {
  height: 100%;
  display: flex;
  flex-direction: column;
}
```

**Flexbox:**
- `display: flex`: フレキシブルボックスレイアウト
- `flex-direction: column`: 縦方向に配置

### calendar.css - カレンダースタイル

```css
.calendar-day {
  width: 100%;
  min-height: 32px;
  font-size: 0.875rem;
  border-radius: 4px;
}

.calendar-day:hover {
  transform: scale(1.05);  /* ホバー時に少し拡大 */
  transition: transform 0.1s;
}
```

**CSSトランジション:**
- `transition`: 変化をスムーズに
- `transform: scale()`: 拡大縮小

### reservation.css - 予約表スタイル

```css
.booking-cell {
  min-width: 80px;
  height: 40px;
  vertical-align: middle;
  padding: 2px;
}

.table-warning {
  background-color: #fff3cd;  /* 他人の予約: 黄色 */
}

.table-success {
  background-color: #d1e7dd;  /* 自分の予約: 緑色 */
}
```

### chat.css - チャットスタイル

```css
.chat-messages {
  flex: 1;
  overflow-y: auto;  /* 縦スクロール */
  max-height: 100%;
}

.user-message {
  background-color: #e3f2fd;  /* ユーザーメッセージ: 青 */
  align-self: flex-end;
}

.ai-message {
  background-color: #f5f5f5;  /* AIメッセージ: グレー */
  align-self: flex-start;
}
```

---

## Bootstrapの主要クラス

### グリッドシステム

```html
<div class="row">
  <div class="col-lg-8">左側（8/12）</div>
  <div class="col-lg-4">右側（4/12）</div>
</div>
```

**ブレークポイント:**
- `col-sm`: 576px以上
- `col-md`: 768px以上
- `col-lg`: 992px以上
- `col-xl`: 1200px以上

### ユーティリティクラス

```html
<!-- 余白 -->
<div class="p-3">padding: 1rem</div>
<div class="m-2">margin: 0.5rem</div>
<div class="mb-3">margin-bottom: 1rem</div>
<div class="ms-auto">margin-left: auto（右寄せ）</div>

<!-- 表示・非表示 -->
<div class="d-flex">display: flex</div>
<div class="d-none d-md-block">中画面以上で表示</div>

<!-- テキスト -->
<div class="text-center">中央揃え</div>
<div class="text-primary">青色</div>
<div class="fw-bold">太字</div>
```

### コンポーネント

```html
<!-- カード -->
<div class="card">
  <div class="card-header">ヘッダー</div>
  <div class="card-body">本文</div>
</div>

<!-- ボタン -->
<button class="btn btn-primary">メインボタン</button>
<button class="btn btn-sm btn-outline-secondary">小さい枠線ボタン</button>

<!-- フォーム -->
<input class="form-control" type="text">
<select class="form-select"></select>
<label class="form-label">ラベル</label>
```

---

## レスポンシブデザイン

### モバイル対応

```html
<meta name="viewport" content="width=device-width, initial-scale=1.0">
```

### Bootstrapのレスポンシブクラス

```html
<!-- 大画面: 左80% 右20% -->
<!-- 中画面: 左67% 右33% -->
<div class="row">
  <div class="col-xl-9 col-lg-8">予約システム</div>
  <div class="col-xl-3 col-lg-4">チャット</div>
</div>
```

---

## アクセシビリティ

### セマンティックHTML

```html
<nav role="navigation" aria-label="メインナビゲーション">
<main>
<section aria-labelledby="calendar-title">
```

### ARIAラベル

```html
<button aria-label="前の月">
  <i class="fas fa-chevron-left"></i>
</button>

<div role="log" aria-live="polite" aria-label="チャットメッセージ履歴">
```

---

## 学習のポイント

1. **Bootstrap 5の活用**
   - グリッドシステムでレスポンシブレイアウト
   - ユーティリティクラスで効率的なスタイリング

2. **Jinja2テンプレート**
   - サーバーサイドでHTMLを動的生成
   - ループや条件分岐

3. **data属性**
   - カスタムデータをHTML要素に格納
   - JavaScriptからアクセス

4. **セマンティックHTML**
   - 意味のあるタグを使用
   - アクセシビリティ向上

5. **Flexbox**
   - 柔軟なレイアウト
   - 高さを揃える

## まとめ

HTMLとCSSは、ユーザーが実際に見る部分を構成します:

- **HTML**: 構造（何を表示するか）
- **CSS**: スタイル（どう表示するか）
- **Bootstrap**: 効率的な開発
- **Jinja2**: 動的なコンテンツ

初心者でも、BootstrapとJinja2を使うことで、モダンなUIを短時間で構築できます！

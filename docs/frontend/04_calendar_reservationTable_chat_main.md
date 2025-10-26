# calendar.js / reservationTable.js / chat.js / main.js

## 1. calendar.js - コンパクトカレンダー

### 概要
月表示のカレンダーUIを提供し、日付選択と予約表示の連携を行います。

### 主要機能
- カレンダーの月表示
- 前月/次月への移動
- 日付選択
- 今日の日付ハイライト
- 予約表との連携

### クラス構造

```javascript
export class CompactCalendar {
  constructor() {
    this.currentYear = now.getFullYear();
    this.currentMonth = now.getMonth();  // 0-11
    this.today = { year, month, date };
    this.selectedDate = null;
  }
}
```

### 重要メソッド

#### renderCalendar() - カレンダー描画

```javascript
renderCalendar() {
  // 月の最初の日と最後の日
  const firstDay = new Date(this.currentYear, this.currentMonth, 1);
  const lastDay = new Date(this.currentYear, this.currentMonth + 1, 0);

  // 最初の日の曜日（0=日曜）
  const firstDayOfWeek = firstDay.getDay();

  // カレンダーを構築（最大6週）
  for (let week = 0; week < 6; week++) {
    for (let dayOfWeek = 0; dayOfWeek < 7; dayOfWeek++) {
      // 日付ボタンを作成
      const button = document.createElement('button');
      button.dataset.date = dateStr;  // "2025-01-15"
      button.textContent = day;

      // 今日の場合
      if (isToday) {
        button.classList.add('btn-primary');
      }
      // 選択中の場合
      else if (isSelected) {
        button.classList.add('btn-success');
      }
    }
  }
}
```

**ポイント:**
- 月の開始日の曜日を計算して空白セルを配置
- 日曜・土曜に色を付ける
- `data-date`属性に日付を格納

#### selectDate() - 日付選択

```javascript
async selectDate(dateStr, updateInput = true) {
  this.selectedDate = dateStr;

  // 選択した日付の年月を表示
  const [year, month, day] = dateStr.split('-').map(Number);
  this.currentYear = year;
  this.currentMonth = month - 1;

  // カレンダーを再描画
  this.renderCalendar();

  // 日付入力フォームに自動入力
  if (updateInput && this.dateInput) {
    this.dateInput.value = dateStr;
  }

  // 選択した日付の予約情報を取得
  await this.updateReservationTable(dateStr);
}
```

**処理の流れ:**
1. 選択日付を保存
2. カレンダーを移動
3. フォームの日付を更新
4. その日の予約を取得・表示

---

## 2. reservationTable.js - 予約表

### 概要
時間割形式で予約状況を表示するテーブルを管理します。

### テーブル構造

```
時間   | Room A | Room B | Room C | Room D |
-------|--------|--------|--------|--------|
07:00~ |        |  予約  |        |        |
07:30~ |        |  予約  |        |  予約  |
08:00~ |  予約  |        |        |  予約  |
...
```

### 主要機能
- 予約表の動的生成（7:00〜21:30、30分刻み）
- 予約データの表示
- キャンセルボタンの制御
- 自分の予約と他人の予約で色分け

### クラス構造

```javascript
export class ReservationTable {
  constructor() {
    this.tableBody = document.getElementById("booking-table-body");
    this.buildTableBody();  // テーブルを構築
    this.initEventDelegation();  // キャンセルボタンのイベント委譲
  }
}
```

### 重要メソッド

#### buildTableBody() - テーブル構築

```javascript
buildTableBody() {
  const slots = this.generateTimeSlots();  // 30個のスロット生成

  for (const slot of slots) {
    const tr = document.createElement('tr');

    // 時間列
    const th = document.createElement('th');
    th.textContent = `${slot.hour}:${slot.min}~`;

    // 各会議室の列
    for (let i = 0; i < roomCount; i++) {
      const td = document.createElement('td');
      td.className = 'booking-cell';
      tr.appendChild(td);
    }
  }
}
```

#### displayReservationInTable() - 予約表示

```javascript
displayReservationInTable(reservation) {
  const { room_id, start_time, end_time, user_name } = reservation;

  // 会議室の列を見つける
  const roomColumnIndex = this.findRoomColumnIndex(room_id);

  // 開始・終了時刻をパース
  const { startHour, startMin, endHour, endMin } =
    this.parseTimeRange(start_time, end_time);

  // 該当するセルを塗りつぶす
  timeSlots.forEach((slot, slotIndex) => {
    const slotTime = slot.hour * 60 + slot.min;
    const reservationStart = startHour * 60 + startMin;
    const reservationEnd = endHour * 60 + endMin;

    if (slotTime >= reservationStart && slotTime < reservationEnd) {
      const cell = bookingCells[cellIndex];
      cell.innerHTML = createReservationCellContent(user_name, id);

      // 自分の予約は緑、他人の予約は黄色
      if (isOwnReservation) {
        cell.classList.add('table-success');
      } else {
        cell.classList.add('table-warning');
      }
    }
  });
}
```

**ポイント:**
- 時刻を分単位に変換して範囲判定
- 予約時間に該当するセルをすべて塗りつぶす
- 例: 14:00〜15:30の予約 → 14:00, 14:30, 15:00のセル

#### イベント委譲でキャンセル処理

```javascript
initEventDelegation() {
  document.addEventListener("click", async (e) => {
    if (!e.target.classList.contains("cancel-btn")) return;

    const reservationId = e.target.getAttribute("data-reservation-id");

    if (!confirm("この予約をキャンセルしますか？")) return;

    const result = await cancelReservation(reservationId);
    if (result.success) {
      await this.refreshToday();
    }
  });
}
```

**イベント委譲のメリット:**
- 動的に追加されたボタンにも対応
- メモリ効率が良い

---

## 3. chat.js - AIチャット

### 概要
AIチャットボットのUI と処理を担当します。

### 主要機能
- メッセージ送受信
- チャット履歴表示
- セッションID管理（LocalStorage）
- 予約作成時の予約表更新
- 日本語入力対応（IME）

### クラス構造

```javascript
class ChatManager {
  constructor() {
    this.chatMessages = document.getElementById('chat-messages');
    this.chatInput = document.getElementById('chat-input');
    this.sessionId = this.ensureSessionId();  // セッションID発行
    this.initEventListeners();
  }
}
```

### セッションID管理

```javascript
ensureSessionId() {
  let sid = localStorage.getItem('chat_session_id');
  if (!sid) {
    sid = crypto.randomUUID();  // UUIDを生成
    localStorage.setItem('chat_session_id', sid);
  }
  return sid;
}
```

**LocalStorageとは？**
- ブラウザにデータを永続保存
- ページを閉じても消えない
- セッションIDを保持することで会話履歴を維持

### メッセージ送信

```javascript
async handleSubmit(event) {
  event.preventDefault();

  const message = this.chatInput.value.trim();

  // ユーザーメッセージを表示
  this.addMessage(message, 'user');

  // 入力フィールドをクリア
  this.chatInput.value = '';

  // APIに送信
  const response = await fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message: message,
      sessionId: this.sessionId
    })
  });

  const result = await response.json();

  // AIの応答を表示
  this.addMessage(result.response, 'ai');

  // 予約が作成された場合、予約表を更新
  if (result.action === 'reserve' && result.reservation) {
    this.updateReservationTable(result.reservation);
  }
}
```

### 日本語入力対応

```javascript
// Enterキーでの送信（日本語入力中は送信しない）
this.chatInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey && !e.isComposing) {
    if (!this.isComposing) {
      e.preventDefault();
      this.handleSubmit(e);
    }
  }
});

// 日本語入力の変換状態を追跡
this.isComposing = false;
this.chatInput.addEventListener('compositionstart', () => {
  this.isComposing = true;
});
this.chatInput.addEventListener('compositionend', () => {
  this.isComposing = false;
});
```

**なぜ必要？**
- 日本語入力中にEnterを押すと変換確定とメッセージ送信が同時に起こる
- `compositionstart/end`で変換中かを判定

### チャットクリア

```javascript
clearChat() {
  // 初期メッセージ以外を削除
  const messages = this.chatMessages.querySelectorAll('.message');
  messages.forEach((message, index) => {
    if (index > 0) {  // 最初のメッセージは残す
      message.remove();
    }
  });

  // セッションIDも再発行
  this.rotateSessionId();
}
```

---

## 4. main.js - エントリーポイント

### 概要
アプリケーション全体を初期化し、各モジュールを統合します。

### コード

```javascript
import { ReservationTable } from "./reservationTable.js";
import { ReservationFormUI } from "./formUI.js";
import { CompactCalendar } from "./calendar.js";
import "./chat.js";

let reservationTable;
let compactCalendar;

document.addEventListener("DOMContentLoaded", async () => {
  // 予約表の初期化
  reservationTable = new ReservationTable();

  // 予約フォームUIの初期化
  new ReservationFormUI();

  // コンパクトカレンダーの初期化
  compactCalendar = new CompactCalendar();

  // 今日の予約を読み込み
  await reservationTable.refreshToday();

  // グローバルに公開（他モジュールから使用）
  window.loadTodaysReservations = () => reservationTable.refreshToday();
  window.displayReservationInTable = (reservation, includeCancel) =>
    reservationTable.displayReservationInTable(reservation, includeCancel);
  window.ReservationTable = reservationTable;
  window.CompactCalendar = compactCalendar;
});
```

### 初期化の順序

1. **予約表** → テーブルを構築
2. **予約フォーム** → 時刻セレクトを生成、イベント登録
3. **カレンダー** → 今月のカレンダーを表示
4. **今日の予約読み込み** → 初期データ表示
5. **グローバル公開** → モジュール間連携のため

### DOMContentLoadedとは？

```javascript
document.addEventListener("DOMContentLoaded", () => {
  // HTMLの読み込みが完了してから実行
});
```

**なぜ必要？**
- JavaScriptがHTMLより先に実行されると、要素が見つからない
- DOMContentLoadedイベントでHTMLの読み込み完了を待つ

### グローバル変数の使用

```javascript
window.CompactCalendar = compactCalendar;
```

**理由:**
- モジュール間で直接importすると循環参照になる可能性
- グローバル変数で簡単に連携できる

**使用例:**
```javascript
// formUI.js から calendar.js のメソッドを呼び出す
window.CompactCalendar.selectDateFromExternal(date);

// chat.js から reservationTable.js のメソッドを呼び出す
window.ReservationTable.displayReservationInTable(reservation);
```

---

## モジュール間の連携図

```
main.js (初期化)
    │
    ├─ ReservationTable ←─┐
    │       ↓             │
    │   予約表示           │ グローバル変数経由
    │                     │
    ├─ ReservationFormUI ─┤
    │       ↓             │
    │   予約作成           │
    │       ↓             │
    │   CompactCalendar ←─┘
    │       ↓
    │   日付選択
    │       ↓
    └─ ChatManager
            ↓
        AI予約
```

## 学習のポイント

### 1. モジュール設計
- 機能ごとにクラスで分離
- 責任を明確に分担

### 2. イベント駆動
- ユーザーの操作に応じて処理
- イベント委譲で効率化

### 3. DOM操作
- createElement, appendChild
- classList.add/remove
- dataset属性

### 4. 非同期処理
- async/awaitで順序制御
- 複数のAPI呼び出しを連携

### 5. 状態管理
- LocalStorageでセッション管理
- クラスのプロパティで状態保持

## まとめ

これら4つのモジュールが連携して、会議室予約システムのフロントエンドを構成しています:

- **calendar.js**: 日付選択UI
- **reservationTable.js**: 予約状況の可視化
- **chat.js**: AIによる自然言語予約
- **main.js**: 全体の統合

初心者でも読みやすいコード構造で、実践的なWebアプリ開発のパターンが学べます！

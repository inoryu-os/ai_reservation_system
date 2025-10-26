# formUI.js - 予約フォームUI

## 概要
予約作成フォームのUIと処理を担当するクラスです。
フォームの初期化、送信処理、カレンダーとの連携を行います。

## 役割
- 時刻セレクトボックスの生成
- フォーム送信処理
- 日付選択とカレンダーの同期
- 送信中のUI状態管理

## クラス構造

```javascript
export class ReservationFormUI {
  constructor() {
    // DOM要素の取得
    this.form = document.getElementById("reservation-form");
    this.startSelect = document.getElementById("start-time");
    this.endSelect = document.getElementById("end-time");
    this.dateInput = document.getElementById("date-select");
    this.submitButton = document.getElementById("reserve-btn");

    this.init();
  }
}
```

## 主要メソッド

### 1. 初期化 (init)

```javascript
init() {
  // 時刻セレクトの初期化
  const timeOptions = generateTimeOptions();
  populateSelect(this.startSelect, timeOptions, "開始時刻");
  populateSelect(this.endSelect, timeOptions, "終了時刻");

  // 日付の初期値をJSTの今日に設定
  if (this.dateInput) {
    this.dateInput.value = getTodayJST();
  }

  // 送信イベント
  this.form.addEventListener("submit", (e) => this.handleSubmit(e));

  // 日付選択変更イベント
  if (this.dateInput) {
    this.dateInput.addEventListener("change", (e) => this.handleDateChange(e));
  }
}
```

**処理の流れ:**
1. 時刻セレクトボックスに選択肢を追加（7:00〜21:30）
2. 日付入力のデフォルト値を今日に設定
3. イベントリスナーを登録

### 2. 時刻選択肢の生成

```javascript
function generateTimeOptions() {
  const { startHour, endHour, stepMinutes } = TIME;
  const options = [];

  for (let hour = startHour; hour <= endHour; hour++) {
    for (let minute = 0; minute < 60; minute += stepMinutes) {
      if (hour === endHour) break;  // 終了時刻では終了

      const h = String(hour).padStart(2, '0');
      const m = String(minute).padStart(2, '0');
      const timeStr = `${h}:${m}`;

      options.push({ value: timeStr, text: timeStr });
    }
  }

  return options;
}
```

**生成される選択肢:**
```
07:00, 07:30, 08:00, 08:30, ..., 21:00, 21:30
```

**初心者向けポイント:**
- `TIME.endHour`（22時）では、ループを早期終了
- 理由: 終了時刻は22:00まで設定可能だが、開始時刻は21:30まで

### 3. セレクトボックスへの追加

```javascript
function populateSelect(selectElement, options, defaultText) {
  if (!selectElement) return;

  selectElement.innerHTML = "";

  // デフォルトオプション（"開始時刻"など）
  if (defaultText) {
    const def = document.createElement("option");
    def.value = "";
    def.textContent = defaultText;
    selectElement.appendChild(def);
  }

  // 各選択肢を追加
  for (const opt of options) {
    const el = document.createElement("option");
    el.value = opt.value;
    el.textContent = opt.text;
    if (opt.disabled) el.disabled = true;
    selectElement.appendChild(el);
  }
}
```

**HTML構造:**
```html
<select id="start-time">
  <option value="">開始時刻</option>
  <option value="07:00">07:00</option>
  <option value="07:30">07:30</option>
  ...
</select>
```

### 4. 日付変更時の処理

```javascript
async handleDateChange(event) {
  const selectedDate = event.target.value;
  if (!selectedDate) return;

  // カレンダーの選択を同期
  if (window.CompactCalendar) {
    window.CompactCalendar.selectDateFromExternal(selectedDate);
  }
}
```

**連携の流れ:**
```
[ユーザー] 日付入力で "2025-01-20" を選択
    ↓
[formUI] handleDateChange()
    ↓
[calendar] selectDateFromExternal()
    ↓ カレンダーが2025年1月に移動
    ↓ 20日が選択状態になる
    ↓ その日の予約を表示
```

### 5. フォーム送信処理

```javascript
async handleSubmit(event) {
  event.preventDefault();  // デフォルトのフォーム送信を防ぐ
  if (!this.form) return;

  const payload = getFormData(this.form);

  // 現在選択されている日付を保存
  const currentDate = this.dateInput ? this.dateInput.value : null;

  // 送信中のUI状態
  this.setSubmitting(true);

  try {
    const result = await createReservation(payload);

    if (result.success) {
      // 予約表に追加
      if (window.displayReservationInTable) {
        window.displayReservationInTable(result.reservation, true);
      }

      // フォームをリセット
      resetForm(this.form);

      // 選択されていた日付を維持
      if (this.dateInput && currentDate) {
        this.dateInput.value = currentDate;
      }
    } else {
      console.error("予約作成エラー:", result.error);
      alert(result.error || "予約の作成に失敗しました");
    }
  } catch (err) {
    console.error("予約送信中にエラー:", err);
    alert("通信エラーが発生しました");
  } finally {
    this.setSubmitting(false);
  }
}
```

**処理の流れ:**
1. デフォルトのフォーム送信を防ぐ
2. フォームデータを取得
3. 送信中の状態に変更（ボタン無効化）
4. API呼び出し
5. 成功時: 予約表に追加、フォームリセット
6. 失敗時: エラーメッセージ表示
7. 最終的に送信中状態を解除

**初心者向けポイント:**
- `event.preventDefault()`: ページリロードを防ぐ
- `try/catch/finally`: エラーハンドリング
- `finally`: 成功・失敗に関わらず必ず実行

### 6. フォームデータの取得

```javascript
function getFormData(form) {
  const formData = new FormData(form);
  return {
    'room-id': formData.get('room-id'),
    'date': formData.get('date'),
    'start-time': formData.get('start-time'),
    'end-time': formData.get('end-time')
  };
}
```

**FormDataとは？**
- フォームの値を簡単に取得できるAPI
- `name`属性の値をキーとして取得

**使用例:**
```html
<form id="reservation-form">
  <select name="room-id">...</select>
  <input name="date" type="date">
  <select name="start-time">...</select>
  <select name="end-time">...</select>
</form>
```

```javascript
const formData = new FormData(form);
formData.get('room-id');  // 選択された会議室ID
formData.get('date');     // 選択された日付
```

### 7. 送信中の状態管理

```javascript
setSubmitting(isSubmitting) {
  if (!this.submitButton) return;

  this.submitButton.disabled = isSubmitting;

  this.submitButton.innerHTML = isSubmitting
    ? '<i class="fas fa-spinner fa-spin me-2"></i>送信中'
    : '<i class="fas fa-calendar-plus me-2"></i>予約する';
}
```

**UI変化:**
```
通常時: [📅 予約する] ← クリック可能
送信中: [⏳ 送信中]   ← クリック不可（disabled）
```

**初心者向けポイント:**
- Font Awesomeのアイコンを使用
- `fa-spin`: アイコンを回転させるクラス
- 二重送信を防ぐ

### 8. フォームのリセット

```javascript
function resetForm(form) {
  form.reset();
}
```

**リセットの効果:**
- すべての入力フィールドが初期値に戻る
- セレクトボックスは最初のオプションに戻る
- ただし、日付は手動で再設定している（`currentDate`を保持）

## データフロー

### 予約作成の完全な流れ

```
[ユーザー]
    │ 1. 会議室を選択
    │ 2. 日付を選択（カレンダーと同期）
    │ 3. 開始・終了時刻を選択
    │ 4. 「予約する」ボタンをクリック
    ↓
[formUI.handleSubmit()]
    │ 5. event.preventDefault()
    │ 6. フォームデータを取得
    │ 7. setSubmitting(true) ← ボタン無効化
    ↓
[api.createReservation()]
    │ 8. POST /api/reservations
    ↓
[バックエンド]
    │ 9. バリデーション
    │ 10. 重複チェック
    │ 11. DB保存
    │ 12. 結果を返す
    ↓
[formUI.handleSubmit()]
    │ 13. 成功判定
    │ 14. displayReservationInTable() ← 予約表に追加
    │ 15. resetForm() ← フォームクリア
    │ 16. 日付を再設定
    │ 17. setSubmitting(false) ← ボタン復元
    ↓
[ユーザー]
    18. 予約表に新しい予約が表示される
```

## カレンダーとの連携

### 双方向同期

```
フォーム → カレンダー:
  日付入力を変更 → カレンダーが移動

カレンダー → フォーム:
  カレンダーで日付をクリック → 日付入力が更新
```

**実装:**
```javascript
// formUI.js
handleDateChange(event) {
  const selectedDate = event.target.value;
  window.CompactCalendar.selectDateFromExternal(selectedDate);
}

// calendar.js
async selectDate(dateStr, updateInput = true) {
  if (updateInput && this.dateInput) {
    this.dateInput.value = dateStr;  // フォームの日付を更新
  }
}
```

## グローバル変数との連携

```javascript
// main.js で公開
window.displayReservationInTable = (reservation, includeCancel) =>
  reservationTable.displayReservationInTable(reservation, includeCancel);

// formUI.js で使用
if (window.displayReservationInTable) {
  window.displayReservationInTable(result.reservation, true);
}
```

**なぜグローバル変数？**
- モジュール間の連携を簡単にするため
- 循環参照を避けるため

## エラーハンドリング

### 1. API エラー

```javascript
if (result.success) {
  // 成功処理
} else {
  alert(result.error || "予約の作成に失敗しました");
}
```

**表示されるエラー例:**
- "指定された時間帯は既に予約されています"
- "7時から22時の間で予約してください"
- "必須項目が不足しています"

### 2. ネットワークエラー

```javascript
catch (err) {
  console.error("予約送信中にエラー:", err);
  alert("通信エラーが発生しました");
}
```

### 3. finally で確実にボタンを復元

```javascript
finally {
  this.setSubmitting(false);  // 必ず実行される
}
```

## 学習のポイント

1. **クラスによるカプセル化**
   - フォーム関連の処理を1つのクラスにまとめる
   - プロパティとメソッドで状態と振る舞いを管理

2. **イベントハンドリング**
   - `addEventListener`でイベントを登録
   - `event.preventDefault()`でデフォルト動作を防ぐ

3. **FormData API**
   - フォームの値を簡単に取得
   - `name`属性が重要

4. **async/await**
   - 非同期処理を同期的に書ける
   - try/catch/finallyでエラーハンドリング

5. **UI状態管理**
   - 送信中はボタンを無効化
   - ユーザーに処理中であることを明示

6. **モジュール間連携**
   - グローバル変数での連携
   - カレンダーとの双方向同期

## よくある実装パターン

### パターン1: フォームリセット後も一部の値を維持

```javascript
const currentDate = this.dateInput.value;  // 保存
resetForm(this.form);                      // リセット
this.dateInput.value = currentDate;        // 復元
```

### パターン2: 存在チェック

```javascript
if (window.CompactCalendar) {
  // カレンダーが存在する場合のみ実行
}
```

### パターン3: アロー関数でthisを維持

```javascript
this.form.addEventListener("submit", (e) => this.handleSubmit(e));
// アロー関数なので、thisはReservationFormUIインスタンスを指す

// NG例:
this.form.addEventListener("submit", function(e) {
  this.handleSubmit(e);  // thisがformになってしまう
});
```

## まとめ

`ReservationFormUI`クラスは、予約フォームの中心的な役割を果たします:

- ✅ 時刻選択肢の動的生成
- ✅ フォーム送信とAPI連携
- ✅ カレンダーとの双方向同期
- ✅ エラーハンドリング
- ✅ UI状態管理

このクラスを理解することで、フォーム処理、API連携、モジュール間連携の実践的なパターンが学べます！

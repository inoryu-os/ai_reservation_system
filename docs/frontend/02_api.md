# api.js - API通信モジュール

## 概要
バックエンドとの通信を担当するモジュールです。
予約の作成・取得・キャンセルのAPIを呼び出します。

## 役割
- REST APIとの通信処理を一元化
- エラーハンドリング
- JSON形式でのデータ送受信

## コードの詳細

### 1. APIエンドポイント定義

```javascript
const API_ENDPOINTS = {
  RESERVATIONS: '/api/reservations',
};
```

**説明:**
- APIのURLを定数で管理
- 変更時に1箇所修正すればOK

### 2. 共通のfetch処理

```javascript
async function fetchAPI(url, options = {}) {
  try {
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      },
      ...options
    });

    const result = await response.json();
    return result;
  } catch (error) {
    console.error(`API通信エラー (${url}):`, error);
    return {
      success: false,
      error: 'ネットワークエラーが発生しました'
    };
  }
}
```

**処理の流れ:**
1. `fetch(url, options)`: HTTPリクエストを送信
2. `response.json()`: レスポンスをJSON形式で取得
3. エラー時は統一されたエラーオブジェクトを返す

**初心者向けポイント:**
- `async/await`: 非同期処理を同期的に書ける
- `try/catch`: エラーをキャッチして処理
- スプレッド構文(`...`): オブジェクトをマージ

**async/awaitとは？**
```javascript
// 従来の書き方（Promise）
fetch(url)
  .then(response => response.json())
  .then(data => console.log(data))
  .catch(error => console.error(error));

// async/awaitを使った書き方
async function getData() {
  try {
    const response = await fetch(url);
    const data = await response.json();
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}
```

### 3. 予約作成

```javascript
export async function createReservation(reservationData) {
  return await fetchAPI(API_ENDPOINTS.RESERVATIONS, {
    method: 'POST',
    body: JSON.stringify(reservationData)
  });
}
```

**使用例:**
```javascript
import { createReservation } from "./api.js";

const data = {
  'room-id': '1',
  'date': '2025-01-15',
  'start-time': '14:00',
  'end-time': '15:00'
};

const result = await createReservation(data);

if (result.success) {
  console.log('予約成功:', result.reservation);
} else {
  console.error('エラー:', result.error);
}
```

**HTTPメソッド:**
- `POST`: データを作成

### 4. 予約一覧取得

```javascript
export async function getReservationsByDate(date) {
  return await fetchAPI(`${API_ENDPOINTS.RESERVATIONS}/${date}`);
}
```

**使用例:**
```javascript
const result = await getReservationsByDate('2025-01-15');

if (result.success) {
  console.log('予約一覧:', result.reservations);
}
```

**HTTPメソッド:**
- `GET`: データを取得（デフォルト）

### 5. 予約キャンセル

```javascript
export async function cancelReservation(reservationId) {
  return await fetchAPI(`${API_ENDPOINTS.RESERVATIONS}/${reservationId}`, {
    method: 'DELETE'
  });
}
```

**使用例:**
```javascript
const result = await cancelReservation(5);

if (result.success) {
  console.log('キャンセル成功');
}
```

**HTTPメソッド:**
- `DELETE`: データを削除

## Fetch APIについて

### 基本的な使い方

```javascript
// GETリクエスト
fetch('/api/data')
  .then(response => response.json())
  .then(data => console.log(data));

// POSTリクエスト
fetch('/api/data', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({ key: 'value' })
})
  .then(response => response.json())
  .then(data => console.log(data));
```

### レスポンスの扱い

```javascript
const response = await fetch(url);

// ステータスコード
console.log(response.status); // 200, 404, 500 など

// JSONパース
const data = await response.json();

// テキストとして取得
const text = await response.text();
```

## エラーハンドリングのベストプラクティス

### 1. ネットワークエラー

```javascript
try {
  const response = await fetch(url);
  const data = await response.json();
} catch (error) {
  // ネットワークエラー、JSONパースエラーなど
  console.error('エラー:', error);
}
```

### 2. HTTPステータスコードのチェック

```javascript
const response = await fetch(url);

if (!response.ok) {
  // 400番台、500番台のエラー
  throw new Error(`HTTPエラー: ${response.status}`);
}

const data = await response.json();
```

### 3. アプリケーションレベルのエラー

```javascript
const result = await createReservation(data);

if (!result.success) {
  // アプリ固有のエラー
  alert(result.error);
}
```

## モジュールパターン

このファイルでは、API通信を抽象化しています。

**メリット:**
1. **再利用性**: 他のモジュールから簡単に呼び出せる
2. **保守性**: API仕様変更時、このファイルだけ修正すればOK
3. **テスト容易性**: モックに差し替えやすい

**悪い例:**
```javascript
// 各所でfetchを直接呼ぶ
fetch('/api/reservations', { method: 'POST', ... });
```

**良い例:**
```javascript
// api.jsにまとめる
import { createReservation } from "./api.js";
await createReservation(data);
```

## 関数一覧

| 関数名 | HTTPメソッド | エンドポイント | 用途 |
|-------|------------|--------------|------|
| createReservation() | POST | /api/reservations | 予約作成 |
| getReservationsByDate() | GET | /api/reservations/{date} | 予約一覧取得 |
| cancelReservation() | DELETE | /api/reservations/{id} | 予約キャンセル |

## 学習のポイント

1. **Fetch API**
   - ブラウザ標準のHTTP通信API
   - Promiseベースの非同期処理

2. **async/await**
   - Promiseを同期的に書ける構文
   - エラーハンドリングがtry/catchで可能

3. **モジュール化**
   - API通信を一箇所に集約
   - DRY原則（Don't Repeat Yourself）

4. **エラーハンドリング**
   - ネットワークエラーとアプリエラーを分離
   - ユーザーに分かりやすいメッセージ

5. **JSONの扱い**
   - `JSON.stringify()`: オブジェクト → JSON文字列
   - `response.json()`: JSON文字列 → オブジェクト

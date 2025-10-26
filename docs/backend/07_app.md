# app.py - Flaskアプリケーション

## 概要
このファイルは、**Flaskウェブアプリケーション**のメインファイルです。
REST APIエンドポイントを提供し、フロントエンドとバックエンドを繋ぐ役割を担います。

## 役割
- Flaskアプリケーションの初期化
- REST APIエンドポイントの定義
- リクエストのルーティング
- レスポンスの返却
- エラーハンドリング

## Flaskとは？

**Flask**は、PythonのウェブフレームワークでMinimal（最小限）で軽量なのが特徴です。

**特徴:**
- シンプルで学習しやすい
- REST APIの構築に最適
- 拡張性が高い

## コードの詳細

### 1. 初期化とセットアップ

```python
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

load_dotenv()

# タイムゾーンをJSTに設定
from timezone_utils import setup_timezone
setup_timezone()

import models
from reservation_service import ReservationService
from ai_service import AIService

app = Flask(__name__)

user_name = "guest"
```

**処理の流れ:**
1. 環境変数を読み込み（`.env`ファイル）
2. タイムゾーンをJSTに設定
3. モデルとサービスクラスをインポート
4. Flaskアプリケーションを作成
5. デフォルトユーザー名を設定

**初心者向けポイント:**
- `load_dotenv()`: .envファイルから環境変数を読み込み
- `app = Flask(__name__)`: Flaskアプリのインスタンス作成
- グローバル変数`user_name`: 全エンドポイントで使用

### 2. トップページ（ルートエンドポイント）

```python
@app.route('/')
def index():
    rooms = models.init_db()
    return render_template('index.html', rooms=rooms, user_name=user_name)
```

**説明:**
- URL: `http://localhost:5000/`
- HTTPメソッド: GET（デフォルト）
- 処理:
  1. データベースを初期化（会議室をROOMS_CONFIGと同期）
  2. `index.html`テンプレートをレンダリング
  3. 会議室リストとユーザー名をテンプレートに渡す

**初心者向けポイント:**
- `@app.route('/')`: デコレータでURLとビュー関数を紐付け
- `render_template()`: HTMLテンプレートを表示
- テンプレート内で`{{ rooms }}`や`{{ user_name }}`として使える

### 3. 予約作成API

```python
@app.route('/api/reservations', methods=['POST'])
def create_reservation():
    """予約作成API"""
    data = request.get_json(silent=False)

    room_id = data.get("room-id")
    date = data.get("date")
    start_time = data.get("start-time")
    end_time = data.get("end-time")

    result = ReservationService.create_reservation(
        room_id=int(room_id) if room_id else None,
        user_name=user_name,
        date=date,
        start_time=start_time,
        end_time=end_time
    )

    if result["success"]:
        return jsonify(result)
    else:
        status_code = 400 if "必須項目" in result["error"] or "形式" in result["error"] else 409
        if "見つかりません" in result["error"]:
            status_code = 404
        return jsonify(result), status_code
```

**エンドポイント情報:**
- URL: `POST /api/reservations`
- リクエストボディ（JSON）:
  ```json
  {
    "room-id": "1",
    "date": "2025-01-15",
    "start-time": "14:00",
    "end-time": "15:00"
  }
  ```

**レスポンス（成功時）:**
```json
{
  "success": true,
  "message": "予約が完了しました",
  "reservation": {
    "id": 1,
    "room_name": "Room A",
    "room_id": 1,
    "date": "2025-01-15",
    "start_time": "14:00",
    "end_time": "15:00",
    "user_name": "guest"
  }
}
```

**レスポンス（失敗時）:**
```json
{
  "success": false,
  "error": "指定された時間帯は既に予約されています"
}
```

**HTTPステータスコード:**
- 200: 成功
- 400: バリデーションエラー（必須項目不足、形式エラー）
- 404: リソースが見つからない
- 409: 競合（時間重複など）

**初心者向けポイント:**
- `request.get_json()`: リクエストボディのJSONを取得
- `data.get("key")`: キーがなければNone（エラーにならない）
- `jsonify()`: Python辞書をJSON形式で返す
- ステータスコードを明示的に返すことでエラーの種類を伝える

### 4. 予約一覧取得API

```python
@app.route('/api/reservations/<date>', methods=['GET'])
def get_reservations_by_date(date):
    """指定日の予約一覧取得API"""
    result = ReservationService.get_reservations_by_date(date)

    if result["success"]:
        return jsonify(result)
    else:
        status_code = 400 if "形式" in result["error"] else 500
        return jsonify(result), status_code
```

**エンドポイント情報:**
- URL: `GET /api/reservations/{date}`
- 例: `GET /api/reservations/2025-01-15`

**URLパラメータ:**
- `date`: 日付（YYYY-MM-DD形式）

**レスポンス:**
```json
{
  "success": true,
  "reservations": [
    {
      "id": 1,
      "room_id": 1,
      "room_name": "Room A",
      "user_name": "guest",
      "start_time": "14:00",
      "end_time": "15:00",
      "date": "2025-01-15"
    }
  ]
}
```

**初心者向けポイント:**
- `<date>`: URLパスの一部として変数を受け取る
- 関数の引数`date`に自動的に値が渡される

### 5. 予約キャンセルAPI

```python
@app.route('/api/reservations/<int:reservation_id>', methods=['DELETE'])
def cancel_reservation(reservation_id):
    """予約キャンセルAPI"""
    result = ReservationService.cancel_reservation(reservation_id)

    if result["success"]:
        return jsonify(result)
    else:
        status_code = 404 if "見つかりません" in result["error"] else 403
        if "他のユーザー" in result["error"]:
            status_code = 403
        elif "サーバーエラー" in result["error"]:
            status_code = 500
        return jsonify(result), status_code
```

**エンドポイント情報:**
- URL: `DELETE /api/reservations/{reservation_id}`
- 例: `DELETE /api/reservations/5`

**URLパラメータ:**
- `reservation_id`: 予約ID（整数）

**レスポンス（成功時）:**
```json
{
  "success": true,
  "message": "予約をキャンセルしました",
  "reservation_id": 5
}
```

**HTTPステータスコード:**
- 200: 成功
- 403: 権限エラー（他のユーザーの予約など）
- 404: 予約が見つからない
- 500: サーバーエラー

**初心者向けポイント:**
- `<int:reservation_id>`: 整数型として型変換
- DELETEメソッド: リソースの削除に使用

### 6. AIチャットAPI

```python
@app.route('/api/chat', methods=['POST'])
def chat_with_ai():
    """AIチャットAPI"""
    try:
        data = request.get_json()
        message = data.get('message', '').strip()
        session_id = data.get('sessionId', '')

        if not message:
            return jsonify({
                'success': False,
                'error': 'メッセージが入力されていません'
            }), 400

        if not session_id:
            return jsonify({
                'success': False,
                'error': 'セッションIDが指定されていません'
            }), 400

        ai_service = AIService()
        result = ai_service.process_chat_message(message, user_name, session_id)

        return jsonify(result)

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'チャット処理エラー: {str(e)}',
            'response': '申し訳ありませんが、システムエラーが発生しました。'
        }), 500
```

**エンドポイント情報:**
- URL: `POST /api/chat`
- リクエストボディ（JSON）:
  ```json
  {
    "message": "今日の予約を教えて",
    "sessionId": "session_001"
  }
  ```

**レスポンス:**
```json
{
  "success": true,
  "response": "本日の予約は以下の通りです:\n- Room A 14:00-15:00 (guest)",
  "action": "check"
}
```

**予約作成時のレスポンス:**
```json
{
  "success": true,
  "response": "予約が完了しました！Room Aを2025-01-15 14:00から15:00まで予約しました。",
  "action": "reserve",
  "reservation": {
    "id": 1,
    "room_name": "Room A",
    ...
  }
}
```

**初心者向けポイント:**
- `strip()`: 前後の空白を削除
- try-exceptでエラーハンドリング
- AIServiceのインスタンスを毎回作成（状態を持たないため）

### 7. アプリケーションの起動

```python
if __name__ == '__main__':
    app.run(debug=True, port=5000)
```

**説明:**
- スクリプトとして直接実行された場合のみ起動
- `debug=True`: デバッグモード（コード変更時に自動リロード）
- `port=5000`: ポート5000で起動

**起動方法:**
```bash
python app.py
```

**アクセスURL:**
```
http://localhost:5000/
```

**初心者向けポイント:**
- `if __name__ == '__main__'`: モジュールとしてインポートされた場合は実行されない
- 本番環境では`debug=False`にする

## REST APIの設計

### エンドポイント一覧

| メソッド | URL | 説明 | ステータスコード |
|---------|-----|------|-----------------|
| GET | / | トップページ | 200 |
| POST | /api/reservations | 予約作成 | 200, 400, 404, 409 |
| GET | /api/reservations/{date} | 指定日の予約一覧 | 200, 400, 500 |
| DELETE | /api/reservations/{id} | 予約キャンセル | 200, 403, 404, 500 |
| POST | /api/chat | AIチャット | 200, 400, 500 |

### HTTPメソッドの使い分け

| メソッド | 用途 | 例 |
|---------|------|---|
| GET | データの取得 | 予約一覧取得 |
| POST | データの作成 | 予約作成、チャット送信 |
| PUT | データの更新（全体） | （未実装） |
| PATCH | データの部分更新 | （未実装） |
| DELETE | データの削除 | 予約キャンセル |

## エラーハンドリングのベストプラクティス

### 1. 適切なHTTPステータスコードを返す

```python
# 成功
return jsonify(result), 200  # または省略

# バリデーションエラー
return jsonify(result), 400

# リソースが見つからない
return jsonify(result), 404

# 競合エラー（重複予約など）
return jsonify(result), 409

# サーバーエラー
return jsonify(result), 500
```

### 2. 統一されたエラーレスポンス

```json
{
  "success": false,
  "error": "エラーメッセージ"
}
```

### 3. 例外のキャッチ

```python
try:
    # ... 処理 ...
except Exception as e:
    return jsonify({
        'success': False,
        'error': f'エラー: {str(e)}'
    }), 500
```

## フロントエンドとの連携

### Fetchによるリクエスト例（JavaScript）

```javascript
// 予約作成
const response = await fetch('/api/reservations', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        'room-id': '1',
        'date': '2025-01-15',
        'start-time': '14:00',
        'end-time': '15:00'
    })
});

const result = await response.json();

if (result.success) {
    console.log('予約成功:', result.reservation);
} else {
    console.error('エラー:', result.error);
}
```

### AIチャット

```javascript
const response = await fetch('/api/chat', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        message: '今日の予約を教えて',
        sessionId: 'session_001'
    })
});

const result = await response.json();
console.log(result.response);  // AIの応答
```

## データフロー図

```
[ブラウザ]
    │
    │ HTTPリクエスト
    ↓
[Flask app.py]
    │
    ├─ /              → [models.init_db()] → [index.html]
    │
    ├─ POST /api/reservations → [ReservationService] → [Database]
    │
    ├─ GET /api/reservations/{date} → [ReservationService] → [Database]
    │
    ├─ DELETE /api/reservations/{id} → [ReservationService] → [Database]
    │
    └─ POST /api/chat → [AIService] → [OpenAI API]
                             │            [Redis]
                             ↓
                        [ReservationService] → [Database]
```

## まとめ

### 主要な役割

| 役割 | 説明 |
|------|------|
| ルーティング | URLとビュー関数を紐付け |
| リクエスト処理 | JSONデータの取得と検証 |
| ビジネスロジック呼び出し | ServiceクラスのメソッドをCo |
| レスポンス生成 | JSON形式でクライアントに返却 |
| エラーハンドリング | 適切なステータスコードとメッセージ |

### 学習のポイント

1. **RESTful API設計**
   - リソース指向のURL設計
   - HTTPメソッドの適切な使い分け
   - ステータスコードの正しい使用

2. **Flaskの基本**
   - デコレータによるルーティング
   - リクエストとレスポンスの処理
   - JSONifyによるJSON生成

3. **レイヤー分離**
   - app.py: API層（ルーティング）
   - *_service.py: ビジネスロジック層
   - models.py: データアクセス層

4. **エラーハンドリング**
   - 統一されたレスポンス形式
   - 適切なステータスコード
   - ユーザーフレンドリーなエラーメッセージ

5. **環境設定**
   - .envファイルによる環境変数管理
   - タイムゾーン設定
   - デバッグモード

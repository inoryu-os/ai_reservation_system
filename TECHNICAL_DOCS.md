# 技術仕様書

## システムアーキテクチャ

### アーキテクチャ図

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend        │    │   External      │
│   (Browser)     │    │   (Flask)        │    │   (OpenAI API)  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         │ HTTP Request          │ Function Calling      │
         ├──────────────────────►│──────────────────────►│
         │                       │                       │
         │ JSON Response         │ AI Response           │
         ◄──────────────────────┤◄──────────────────────┤
         │                       │                       │
         │                       │                       │
    ┌─────────────────┐    ┌──────────────────┐
    │   Static Files  │    │   Database       │
    │   (JS/CSS)      │    │   (SQLite)       │
    └─────────────────┘    └──────────────────┘
```

## コンポーネント詳細

### 1. AIService (ai_service.py)

#### 責任
- OpenAI API との統合
- Function Calling の管理
- 自然言語の意図解析

#### 主要メソッド

```python
class AIService:
    def process_chat_message(message, user_name):
        """メイン処理: ユーザーメッセージを解析しAPIを呼び出し"""

    def _call_create_reservation_api(args, user_name):
        """予約作成API呼び出し"""

    def _call_get_reservations_api(args):
        """予約一覧取得API呼び出し"""

    def _call_cancel_reservation_api(args, user_name):
        """予約キャンセルAPI呼び出し"""
```

#### Function Calling設定

```python
functions = [
    {
        "name": "create_reservation",
        "description": "会議室の予約を作成する",
        "parameters": {
            "type": "object",
            "properties": {
                "room_id": {"type": "integer"},
                "date": {"type": "string", "description": "YYYY-MM-DD"},
                "start_time": {"type": "string", "description": "HH:MM"},
                "end_time": {"type": "string", "description": "HH:MM"}
            },
            "required": ["room_id", "date", "start_time", "end_time"]
        }
    }
    # ... 他のfunction定義
]
```

### 2. ReservationService (reservation_service.py)

#### 責任
- 予約のビジネスロジック
- データ検証
- 重複チェック

#### 主要メソッド

```python
class ReservationService:
    @staticmethod
    def create_reservation(room_id, user_name, date, start_time, end_time):
        """予約作成（重複チェック付き）"""

    @staticmethod
    def get_reservations_by_date(date):
        """指定日の予約一覧取得"""

    @staticmethod
    def cancel_reservation(reservation_id, user_name):
        """予約キャンセル（権限チェック付き）"""

    @staticmethod
    def _check_conflict(session, room_id, start_datetime, end_datetime):
        """時間重複チェック"""
```

### 3. Models (models.py)

#### データベーススキーマ

```python
class Room(Base):
    __tablename__ = 'rooms'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True)
    capacity: Mapped[int] = mapped_column(Integer)

class Reservation(Base):
    __tablename__ = 'reservations'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    room_id: Mapped[int] = mapped_column(ForeignKey('rooms.id'))
    user_name: Mapped[str] = mapped_column(String)
    start_time: Mapped[datetime] = mapped_column(DateTime)
    end_time: Mapped[datetime] = mapped_column(DateTime)
```

### 4. Frontend Architecture

#### JavaScript モジュール構成

```javascript
// main.js - エントリーポイント
import { createReservation, getReservationsByDate } from "./api.js";
import { displayReservationInTable } from "./bookingTable.js";
import { getElements, generateTimeOptions } from "./ui.js";
import "./chat.js";

// chat.js - AIチャット機能
class ChatManager {
    constructor() { /* 初期化 */ }
    initEventListeners() { /* イベント設定 */ }
    handleSubmit(event) { /* メッセージ送信 */ }
    addMessage(content, type) { /* メッセージ表示 */ }
}
```

## API設計

### REST API仕様

#### 予約作成
```http
POST /api/reserve
Content-Type: application/json

{
    "room-id": "1",
    "date": "2025-09-29",
    "start-time": "14:00",
    "end-time": "15:00"
}

Response:
{
    "success": true,
    "reservation": {
        "id": 12,
        "room_name": "会議室A",
        "room_id": 1,
        "date": "2025-09-29",
        "start_time": "14:00",
        "end_time": "15:00",
        "user_name": "guest"
    }
}
```

#### 予約一覧取得
```http
GET /api/reservations/2025-09-29

Response:
{
    "success": true,
    "reservations": [
        {
            "id": 12,
            "room_id": 1,
            "room_name": "会議室A",
            "user_name": "guest",
            "start_time": "14:00",
            "end_time": "15:00",
            "date": "2025-09-29"
        }
    ]
}
```

#### AIチャット
```http
POST /api/chat
Content-Type: application/json

{
    "message": "明日14時から会議室Aを1時間予約してください"
}

Response:
{
    "success": true,
    "action": "reserve",
    "response": "予約が完了しました！",
    "reservation": { /* 予約データ */ }
}
```

## フロントエンド技術詳細

### 日本語入力対応

```javascript
// IME状態の追跡
this.isComposing = false;

this.chatInput.addEventListener('compositionstart', () => {
    this.isComposing = true;  // 変換開始
});

this.chatInput.addEventListener('compositionend', () => {
    this.isComposing = false; // 変換終了
});

// Enterキー処理
this.chatInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey && !e.isComposing) {
        if (!this.isComposing) {
            e.preventDefault();
            this.handleSubmit(e);
        }
    }
});
```

### リアルタイム文字カウンター

```javascript
updateSendButton() {
    const text = this.chatInput.value;
    const length = text.length;
    this.charCounter.textContent = `${length}/500`;

    // 段階的な警告表示
    if (length > 480) {
        this.charCounter.classList.add('text-danger');
    } else if (length > 400) {
        this.charCounter.classList.add('text-warning');
    } else {
        this.charCounter.classList.add('text-muted');
    }
}
```

## OpenAI Function Calling実装

### システムプロンプト例

```python
system_prompt = f"""
あなたは会議室予約システムのAIアシスタントです。
ユーザーのメッセージを解析して、適切な関数を呼び出してください。

利用可能な会議室:
- 会議室A (ID: 1, 定員: 4名)
- 会議室B (ID: 2, 定員: 6名)

現在の日時: {now.strftime("%Y年%m月%d日 %H:%M")}

日時の解析ルール:
- 「明日」= {(now + timedelta(days=1)).strftime("%Y-%m-%d")}
- 「今日」= {today}
"""
```

### Function Call処理フロー

```python
response = self.client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": message}
    ],
    functions=functions,
    function_call="auto",
    temperature=0.1
)

# Function Callingがある場合
if response.choices[0].message.function_call:
    function_name = response.choices[0].message.function_call.name
    function_args = json.loads(response.choices[0].message.function_call.arguments)

    # 対応する内部API呼び出し
    if function_name == "create_reservation":
        return self._call_create_reservation_api(function_args, user_name)
```

## エラーハンドリング

### フロントエンド

```javascript
try {
    const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: message })
    });

    const result = await response.json();

    if (result.success) {
        this.addMessage(result.response, 'ai');
    } else {
        this.addMessage(result.response || 'エラーが発生しました', 'ai');
    }
} catch (error) {
    console.error('チャットエラー:', error);
    this.addMessage('通信エラーが発生しました。', 'ai');
}
```

### バックエンド

```python
try:
    # OpenAI API呼び出し
    response = self.client.chat.completions.create(...)
    return {"success": True, "response": ...}

except Exception as e:
    return {
        "success": False,
        "error": f"AIサービスエラー: {str(e)}",
        "response": "申し訳ありませんが、システムエラーが発生しました。"
    }
```

## セキュリティ考慮事項

### 1. API キー管理
- `.env` ファイルでの環境変数管理
- 本番環境では環境変数で設定
- `.gitignore` で `.env` を除外

### 2. ユーザー権限
- 現在は `user_name = "guest"` 固定
- 将来的には認証システム統合を推奨

### 3. 入力検証
- フロントエンド: 500文字制限
- バックエンド: SQLAlchemy ORM使用でSQLインジェクション対策
- OpenAI API: システムプロンプトでの制約

## パフォーマンス最適化

### 1. データベース
- SQLite使用（小規模運用向け）
- インデックス: 外部キー自動作成
- 将来的にはPostgreSQLへの移行を推奨

### 2. フロントエンド
- モジュラーJavaScript設計
- Bootstrap CDN使用
- 必要最小限のDOMアクセス

### 3. API
- OpenAI API: `temperature=0.1` で一貫性向上
- Function Calling: 既存API再利用でロジック統一

## 監視・ログ

### 現在の実装
- Flask標準ログ
- コンソール出力

### 推奨改善
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
```

## 既知の制限事項

### 1. 同時アクセス
- SQLite + Flaskは同時接続数に制限あり
- 本格運用時はWSGI + PostgreSQL推奨

### 2. エラー回復
- OpenAI API障害時の代替処理なし
- タイムアウト設定なし

### 3. データ永続化
- ファイルベースSQLite
- バックアップ機能なし

## 今後の拡張案

### 1. 認証・認可
- Flask-Login統合
- ロールベースアクセス制御

### 2. 通知機能
- メール通知
- Slack統合

### 3. レポート機能
- 利用統計
- CSV エクスポート

### 4. 多言語対応
- Flask-Babel統合
- UI多言語化
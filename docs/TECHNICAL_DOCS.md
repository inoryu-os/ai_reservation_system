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
         │ (with SessionID)      │                       │
         ├──────────────────────►│──────────────────────►│
         │                       │                       │
         │ JSON Response         │ AI Response           │
         ◄──────────────────────┤◄──────────────────────┤
         │                       │                       │
         │                       │                       │
    ┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
    │   Static Files  │    │   Database       │    │   Redis         │
    │   (JS/CSS)      │    │   (SQLite)       │    │   (Chat History)│
    └─────────────────┘    └──────────────────┘    └─────────────────┘
                                                             ▲
                                                             │
                                                    ┌────────┴────────┐
                                                    │  redis_service  │
                                                    │  (Python)       │
                                                    └─────────────────┘
```

## コンポーネント詳細

### 1. AIService (ai_service.py)

#### 責任
- OpenAI API との統合
- Function Calling の管理
- 自然言語の意図解析
- チャット履歴の管理（RedisService経由）

#### 主要メソッド

```python
class AIService:
    def __init__(self):
        """OpenAI/Azure OpenAI クライアントとRedisサービスの初期化"""
        self.redis_service = RedisService()

    def process_chat_message(message, user_name, session_id):
        """
        メイン処理: ユーザーメッセージを解析しAPIを呼び出し
        - チャット履歴をRedisから取得
        - 履歴と共にLLMに送信
        - 応答をRedisに保存
        """

    def _call_create_reservation_api(args):
        """予約作成API呼び出し（/api/reservations）"""

    def _call_get_reservations_api(args):
        """予約一覧取得API呼び出し"""

    def _call_cancel_reservation_api(args):
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

### 3. RedisService (redis_service.py)

#### 責任
- Redisへの接続管理
- セッション毎のチャット履歴管理
- TTL（有効期限）管理

#### 主要メソッド

```python
class RedisService:
    def __init__(self):
        """Redis接続の初期化（環境変数から設定読み込み）"""

    def add_message(session_id, role, content):
        """
        チャット履歴にメッセージを追加
        - role: "user" | "assistant" | "system"
        - TTLをリフレッシュ
        """

    def get_history(session_id):
        """セッションのチャット履歴を取得（リスト形式）"""

    def clear_history(session_id):
        """セッションのチャット履歴をクリア"""

    def get_history_count(session_id):
        """チャット履歴件数を取得"""
```

#### Redisデータ構造

```
Key: chat_history:{session_id}
Type: List
Value: JSON文字列の配列
Example:
  [
    '{"role": "user", "content": "明日14時から会議室Aを予約"}',
    '{"role": "assistant", "content": "予約が完了しました！"}',
    ...
  ]
TTL: 86400秒（24時間、設定可能）
```

### 4. Models (models.py)

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

### 5. Frontend Architecture

#### JavaScript モジュール構成

```javascript
// main.js - エントリーポイント
import { createReservation, getReservationsByDate } from "./api.js";
import { ReservationTable } from "./reservationTable.js";
import { FormUI } from "./formUI.js";
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
POST /api/reservations
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
    "message": "明日14時から会議室Aを1時間予約してください",
    "sessionId": "550e8400-e29b-41d4-a716-446655440000"
}

Response:
{
    "success": true,
    "action": "reserve",
    "response": "予約が完了しました！",
    "reservation": { /* 予約データ */ }
}
```

#### チャット履歴の流れ

```
1. クライアント: セッションID生成（初回のみ）
2. クライアント → サーバー: メッセージ + セッションID送信
3. サーバー: Redisから履歴取得
4. サーバー: 履歴 + 新メッセージをLLMに送信
5. LLM: 文脈を考慮した応答生成
6. サーバー: ユーザーメッセージとAI応答をRedisに保存
7. サーバー → クライアント: 応答返却
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
    this.charCounter.classList.remove('text-danger', 'text-warning', 'text-muted');
    if (length > 480) {
        this.charCounter.classList.add('text-danger');
    } else if (length > 400) {
        this.charCounter.classList.add('text-warning');
    } else {
        this.charCounter.classList.add('text-muted');
    }
}
```

## OpenAI Tool Calling実装（OpenAI 2.x対応）

### 重要な変更点

OpenAI 1.x → 2.x での主な変更:
- `functions` → `tools` パラメータ
- `function_call` → `tool_choice` パラメータ
- Function Call オブジェクトが辞書からオブジェクトに変更
- アクセス方法: `call.get("type")` → `call.type`

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

### Tool Call処理フロー（OpenAI 2.x）

```python
# ツール定義
tools = [
    {
        "type": "function",
        "function": {
            "name": "create_reservation",
            "description": "会議室の予約を作成する",
            "parameters": { ... }
        }
    }
]

# API呼び出し
response = self.client.chat.completions.create(
    model=self.model,
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": message}
    ],
    tools=tools,
    tool_choice="auto",
    temperature=0.1
)

# Tool Callingがある場合（OpenAI 2.x形式）
msg = response.choices[0].message
tool_calls = getattr(msg, "tool_calls", None)

if tool_calls:
    call = tool_calls[0]
    if call.type == "function":  # オブジェクトアクセス
        function_name = call.function.name
        function_args = json.loads(call.function.arguments)

        # 対応する内部API呼び出し
        if function_name == "create_reservation":
            return self._call_create_reservation_api(function_args)
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

## タイムゾーン実装詳細

### アーキテクチャ

システム全体でJST（日本標準時）に統一：

```python
# timezone_utils.py
JST = timezone(timedelta(hours=9))

def get_jst_now() -> datetime:
    """現在のJST時刻を取得"""
    return datetime.now(JST)

def parse_datetime_jst(date_str: str, time_str: str) -> datetime:
    """日付文字列と時刻文字列をJSTのdatetimeに変換"""
    datetime_str = f"{date_str} {time_str}"
    return datetime.strptime(datetime_str, "%Y-%m-%d %H:%M").replace(tzinfo=JST)
```

### フロントエンド実装

```javascript
// timezone.js
const JST_OFFSET = 9 * 60; // 分単位

export function getJSTNow() {
  const now = new Date();
  return convertToJST(now);
}

export function getTodayJST() {
  return formatJSTDate(getJSTNow());
}
```

### 統一された処理フロー

1. **データ入力**: フロントエンドでJST日付入力
2. **API送信**: JST形式で送信
3. **バックエンド処理**: JSTで解析・保存
4. **データベース**: JST付きdatetimeで保存
5. **表示**: JST形式で表示

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
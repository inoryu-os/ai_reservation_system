# 技術仕様書

## システムアーキテクチャ

### アーキテクチャ図

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend        │    │   External      │
│   (Browser)     │    │   (Flask)        │    │   (OpenAI API)  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         │ HTTP Request          │ Tool Calling          │
         │ (with SessionID)      │                       │
         ├──────────────────────►│──────────────────────►│
         │                       │                       │
         │                       │ Tool Results          │
         │                       │◄──────────────────────┤
         │                       │                       │
         │                       │ Tool Results → LLM    │
         │                       │──────────────────────►│
         │                       │                       │
         │ JSON Response         │ AI Response           │
         ◄──────────────────────┤◄──────────────────────┤
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
- Tool Calling の管理
- **Tool実行結果をLLMに送信し、自然な応答を生成**
- 自然言語の意図解析
- 多言語対応（日本語・英語の自動検出）
- チャット履歴の管理（RedisService経由）

#### 主要メソッド

```python
class AIService:
    def __init__(self):
        """OpenAI/Azure OpenAI クライアントとRedisサービスの初期化"""
        self.redis_service = RedisService()
        # 自動切り替え: OpenAI または Azure OpenAI

    def _detect_language(self, text: str) -> str:
        """テキストの言語を検出（日本語 or 英語）"""
        # 日本語文字が3文字以上含まれていれば日本語と判定

    def process_chat_message(message, user_name, session_id):
        """
        メイン処理: ユーザーメッセージを解析しAPIを呼び出し
        - ユーザー言語を自動検出
        - チャット履歴をRedisから取得
        - 履歴と共にLLMに送信
        - Tool Calling実行
        - Tool実行結果をLLMに送信（★重要）
        - LLMが生成した応答をRedisに保存
        - 予約データを含めてレスポンス
        """

    def _execute_create_reservation(args):
        """予約作成を実行し、JSONで結果を返す"""
        # ★ バックエンドで固定レスポンスを返さず、JSONデータのみ返す

    def _execute_find_available_rooms(args):
        """空き部屋検索を実行し、JSONで結果を返す"""

    def _execute_get_reservations(args):
        """予約一覧取得を実行し、JSONで結果を返す"""

    def _execute_get_my_reservations(args, user_name):
        """ユーザーの予約取得を実行し、JSONで結果を返す"""

    def _execute_cancel_reservation(args):
        """予約キャンセルを実行し、JSONで結果を返す"""

    def _determine_action(function_name):
        """関数名からアクションタイプ（reserve/check/cancel）を判定"""
```

#### Tool Calling → LLM Response フロー

```python
# 1. ユーザーメッセージ送信
messages = [
    {"role": "system", "content": system_prompt},
    {"role": "user", "content": "明日14時から会議室Aを予約して"}
]

# 2. LLMがTool Callingを決定
response = self.client.chat.completions.create(
    model=self.model,
    messages=messages,
    tools=tools,
    tool_choice="auto"
)

# 3. Tool実行（例: create_reservation）
tool_result = self._execute_create_reservation(fn_args)
# → {"success": True, "reservation": {...}}

# 4. Tool実行結果をメッセージに追加
messages.append({
    "role": "assistant",
    "content": None,
    "tool_calls": [...]
})
messages.append({
    "role": "tool",
    "tool_call_id": call.id,
    "content": json.dumps(tool_result, ensure_ascii=False)
})

# 5. LLMに再度リクエスト（Tool実行結果を元に応答生成）
second_response = self.client.chat.completions.create(
    model=self.model,
    messages=messages
)

# 6. LLMが自然な応答を生成
ai_response = second_response.choices[0].message.content
# → "予約が完了しました！Room Aを2025-10-22 14:00から15:00まで予約しました。"

# 7. 予約データと共にフロントエンドに返却
return {
    "success": True,
    "response": ai_response,
    "action": "reserve",
    "reservation": tool_result["reservation"]
}
```

#### Tool定義

```python
tools = [
    {
        "type": "function",
        "function": {
            "name": "create_reservation",
            "description": "会議室の予約を作成する",
            "parameters": {
                "type": "object",
                "properties": {
                    "room_id": {"type": "integer"},
                    "date": {"type": "string"},
                    "start_time": {"type": "string"},
                    "end_time": {"type": "string"}
                },
                "required": ["room_id", "date", "start_time", "end_time"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "find_available_rooms",
            "description": "指定の開始時刻と利用時間で空いている会議室を検索する",
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {"type": "string"},
                    "start_time": {"type": "string"},
                    "duration_minutes": {"type": "integer"}
                },
                "required": ["date", "start_time", "duration_minutes"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_my_reservations",
            "description": "ユーザー自身の予約一覧を取得する",
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {"type": "string", "description": "省略時は全期間"}
                }
            }
        }
    }
    # ... get_reservations, cancel_reservation
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
    def get_reservations_by_username(user_name, date=None):
        """ユーザー名で予約を検索（日付フィルタ可能）"""

    @staticmethod
    def find_available_rooms_by_start_datetime_and_duration(date, start_time, duration_minutes):
        """指定時刻・時間で空いている部屋を検索"""

    @staticmethod
    def cancel_reservation(reservation_id):
        """予約キャンセル"""

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
import { ReservationTable } from "./reservationTable.js";
import { ReservationFormUI } from "./formUI.js";
import { CompactCalendar } from "./calendar.js";
import "./chat.js";

// 初期化
document.addEventListener("DOMContentLoaded", async () => {
  reservationTable = new ReservationTable();
  new ReservationFormUI();
  compactCalendar = new CompactCalendar();

  await reservationTable.refreshToday();

  // グローバルに公開
  window.loadTodaysReservations = () => reservationTable.refreshToday();
  window.displayReservationInTable = (reservation, includeCancel = true) =>
    reservationTable.displayReservationInTable(reservation, includeCancel);
  window.ReservationTable = reservationTable;
  window.CompactCalendar = compactCalendar;
  window.CURRENT_USER_NAME = "userA"; // ★ HTMLから受け取る
});
```

#### ReservationTable - 予約表管理

```javascript
class ReservationTable {
    isOwnReservation(userName) {
        // ★ 自分の予約かどうかを判定
        const currentUser = window.CURRENT_USER_NAME || '';
        return userName === currentUser;
    }

    displayReservationInTable(reservation, includeCancel = false) {
        const isOwnReservation = this.isOwnReservation(reservation.user_name);

        // ★ 自分の予約は緑色、他人の予約は黄色
        if (isOwnReservation) {
            cell.classList.add('table-success'); // 緑色
        } else {
            cell.classList.add('table-warning');  // 黄色
        }
    }
}
```

#### CompactCalendar - カレンダー機能

```javascript
class CompactCalendar {
    async selectDate(dateStr, updateInput = true) {
        this.selectedDate = dateStr;

        // カレンダーの年月を移動
        const [year, month, day] = dateStr.split('-').map(Number);
        this.currentYear = year;
        this.currentMonth = month - 1;

        // カレンダーを再描画
        this.renderCalendar();

        // フォームに日付を自動入力
        if (updateInput && this.dateInput) {
            this.dateInput.value = dateStr;
        }

        // ★ 予約表を自動更新
        await this.updateReservationTable(dateStr);
    }

    async updateReservationTable(dateStr) {
        const result = await getReservationsByDate(dateStr);
        if (result.success) {
            // タイトル更新
            titleEl.textContent = `${year}年${month}月${day}日`;

            // 予約表に表示
            window.ReservationTable.displayReservationsInTable(result.reservations, true);
        }
    }
}
```

#### ChatManager - AIチャット機能

```javascript
class ChatManager {
    async handleSubmit(event) {
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

        if (result.success) {
            this.addMessage(result.response, 'ai');

            // ★ 予約作成時、即座に予約表に反映
            if (result.action === 'reserve' && result.reservation) {
                this.updateReservationTable(result.reservation);
            }

            // キャンセル時、予約表を再読み込み
            if (result.action === 'cancel') {
                this.refreshReservationTable();
            }
        }
    }

    async updateReservationTable(reservation) {
        const reservationDate = reservation.date;

        // ★ カレンダーを予約日に移動（予約表も自動更新）
        if (window.CompactCalendar) {
            await window.CompactCalendar.selectDateFromExternal(reservationDate, true);
        }
    }
}
```

## API設計

### REST API仕様

#### AIチャット（★重要な変更）

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
    "response": "予約が完了しました！Room Aを2025-10-22 14:00から15:00まで予約しました。",
    "reservation": {
        "id": 12,
        "room_name": "Room A",
        "room_id": 1,
        "date": "2025-10-22",
        "start_time": "14:00",
        "end_time": "15:00",
        "user_name": "userA"
    }
}
```

#### チャット履歴の流れ

```
1. クライアント: セッションID生成（初回のみ、UUID）
2. クライアント → サーバー: メッセージ + セッションID送信
3. サーバー: Redisから履歴取得
4. サーバー: 履歴 + 新メッセージをLLMに送信
5. LLM: Tool Calling実行（必要に応じて）
6. サーバー: Tool実行結果をLLMに送信
7. LLM: 結果を元に自然な応答生成
8. サーバー: ユーザーメッセージとAI応答をRedisに保存
9. サーバー → クライアント: 応答 + 予約データ返却
10. クライアント: 予約表を即座に更新
```

## フロントエンド技術詳細

### 予約表の色分け機能

#### HTML側でユーザー名を渡す

```html
<!-- index.html -->
<script>
    window.CURRENT_USER_NAME = "{{ user_name }}";
</script>
```

#### CSS（reservation.css）

```css
/* 自分の予約 - 緑色 */
.booking-cell.table-success {
    background-color: #d1e7dd !important;
    border-color: #a3cfbb !important;
}

.booking-cell.table-success .booking-reserved {
    color: #0f5132;
    font-weight: 600; /* 太字で強調 */
}

/* 他人の予約 - 黄色 */
.booking-cell.table-warning {
    background-color: #fff3cd !important;
    border-color: #ffe69c !important;
}

.booking-cell.table-warning .booking-reserved {
    color: #664d03;
}
```

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

def round_down_to_30min(dt: datetime) -> datetime:
    """時刻を30分刻みで切り下げ"""
    minutes = dt.minute
    rounded_minutes = (minutes // 30) * 30
    return dt.replace(minute=rounded_minutes, second=0, microsecond=0)
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

## セキュリティ考慮事項

### 1. API キー管理
- `.env` ファイルでの環境変数管理
- 本番環境では環境変数で設定
- `.gitignore` で `.env` を除外

### 2. ユーザー権限
- 現在は `user_name = "userA"` 固定（HTMLテンプレートで渡す）
- 将来的には認証システム統合を推奨

### 3. 入力検証
- フロントエンド: 500文字制限
- バックエンド: SQLAlchemy ORM使用でSQLインジェクション対策
- OpenAI API: システムプロンプトでの制約

## エラーハンドリング

### フロントエンド

```javascript
try {
    const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: message, sessionId: this.sessionId })
    });

    const result = await response.json();

    if (result.success) {
        this.addMessage(result.response, 'ai');

        // 予約作成時の処理
        if (result.action === 'reserve' && result.reservation) {
            this.updateReservationTable(result.reservation);
        }
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
    # Tool実行
    tool_result = self._execute_create_reservation(fn_args)

    # LLMに送信して応答生成
    second_response = self.client.chat.completions.create(...)
    ai_response = second_response.choices[0].message.content

    # 予約データを含めて返す
    return {
        "success": True,
        "response": ai_response,
        "action": "reserve",
        "reservation": tool_result["reservation"]
    }

except Exception as e:
    return {
        "success": False,
        "error": f"AIサービスエラー: {str(e)}",
        "response": "申し訳ありませんが、システムエラーが発生しました。"
    }
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
- 複数ユーザー対応

### 2. 通知機能
- メール通知
- Slack統合

### 3. レポート機能
- 利用統計
- CSV エクスポート

### 4. UIの改善
- ダークモード対応
- カスタムテーマ
- モバイルアプリ化

# ai_service.py - AIチャットボットサービス

## 概要
このファイルは、**AIチャットボット機能**を提供します。
OpenAI/Azure OpenAIのFunction Calling機能を使って、自然言語での会議室予約を実現します。

## 役割
- ユーザーの自然言語メッセージを解析
- 適切なツール（関数）を自動選択・実行
- チャット履歴の管理（Redis連携）
- 多言語対応（日本語・英語）
- 予約システムとの連携

## Function Callingとは？

**Function Calling**は、OpenAI APIの機能で、AIが必要に応じて関数を呼び出せるようにする仕組みです。

**通常のチャットボット:**
```
ユーザー: 「今日の予約を教えて」
AI: 「申し訳ありませんが、予約情報にアクセスできません」
```

**Function Callingを使ったチャットボット:**
```
ユーザー: 「今日の予約を教えて」
AI: [get_reservations関数を呼び出し]
    ↓
    データベースから予約を取得
    ↓
AI: 「本日の予約は以下の通りです: Room A 14:00-15:00 (guest)」
```

## コードの詳細

### 1. クラスの初期化

```python
class AIService:
    def __init__(self):
        # OpenAI or Azure OpenAI を環境変数で自動切り替え
        azure_key = os.getenv("AZURE_OPENAI_KEY")
        azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        azure_api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
        azure_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")

        if azure_key and azure_endpoint:
            # Azure OpenAI クライアント
            self.client = AzureOpenAI(
                api_key=azure_key,
                azure_endpoint=azure_endpoint,
                api_version=azure_api_version,
            )
            self.model = azure_deployment
        else:
            # OpenAI クライアント
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                raise ValueError("OPENAI_API_KEY is not set")
            self.client = OpenAI(api_key=api_key)
            self.model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

        self.base_url = "http://127.0.0.1:5000"
        self.redis_service = RedisService()
```

**環境変数による自動切り替え:**
- Azure OpenAIの設定があればAzureを使用
- なければOpenAIを使用

**初心者向けポイント:**
- 環境変数で設定を外部化
- デプロイ環境に応じて柔軟に切り替え可能

### 2. 言語検出

```python
def _detect_language(self, text: str) -> str:
    """
    テキストの言語を検出（日本語 or 英語）

    Args:
        text: 検出対象のテキスト

    Returns:
        "ja" または "en"
    """
    # 日本語文字（ひらがな、カタカナ、漢字）が含まれているか確認
    japanese_chars = sum(1 for char in text if '\u3040' <= char <= '\u30ff' or '\u4e00' <= char <= '\u9fff')

    # 日本語文字が3文字以上含まれていれば日本語と判定
    if japanese_chars >= 3:
        return "ja"
    else:
        return "en"
```

**Unicode範囲:**
- `\u3040-\u30ff`: ひらがな・カタカナ
- `\u4e00-\u9fff`: 漢字（CJK統合漢字）

**使用例:**
```python
detect_language("今日の予約を教えて")  # "ja"
detect_language("Show me today's reservations")  # "en"
```

**初心者向けポイント:**
- リスト内包表記と`sum()`で日本語文字をカウント
- 簡易的な言語検出（本格的にはライブラリを使うことも可能）

### 3. Function Calling用のツール定義

```python
tools = [
    {
        "type": "function",
        "function": {
            "name": "create_reservation",
            "description": "会議室の予約を作成する。ユーザーから受け取った部屋名を利用可能な会議室リストから検索してroom_idに変換してください。",
            "parameters": {
                "type": "object",
                "properties": {
                    "room_id": {
                        "type": "integer",
                        "description": "会議室ID。ユーザーが指定した部屋名から該当するIDを見つけて設定してください。"
                    },
                    "date": {
                        "type": "string",
                        "description": "予約日 (YYYY-MM-DD形式)"
                    },
                    "start_time": {
                        "type": "string",
                        "description": "開始時刻 (HH:MM形式)"
                    },
                    "end_time": {
                        "type": "string",
                        "description": "終了時刻 (HH:MM形式)"
                    }
                },
                "required": ["room_id", "date", "start_time", "end_time"]
            }
        }
    },
    # ... 他のツール定義 ...
]
```

**ツール（関数）一覧:**

| 関数名 | 説明 | 必須パラメータ |
|-------|------|--------------|
| create_reservation | 予約作成 | room_id, date, start_time, end_time |
| find_available_rooms | 空き部屋検索 | date, start_time, duration_minutes |
| get_reservations | 指定日の予約一覧 | date |
| get_my_reservations | 自分の予約一覧 | なし（dateはオプション） |
| cancel_reservation | 予約キャンセル | reservation_id |

**初心者向けポイント:**
- `description`: AIがいつこの関数を呼ぶべきか判断するヒント
- `parameters`: 関数の引数の型と説明
- `required`: 必須パラメータのリスト

### 4. システムプロンプト

```python
system_prompt = f"""
あなたは会議室予約システムのAIアシスタントです。
ユーザーのメッセージを解析して、適切な関数を呼び出して予約関連の操作を実行してください。

現在のユーザー名: {user_name}

利用可能な会議室（名前とID）:
{room_info}

現在の日時: {now.strftime("%Y年%m月%d日 %H:%M")} (JST)
予約可能な開始時刻: {rounded_start_str} (現在時刻を30分刻みで切り下げた時刻)
次の30分区切り: {next_slot_str}

日時の解析ルール:
- 「明日」= {format_jst_date(now + timedelta(days=1))}
- 「今日」= {today}
- 時間は24時間形式で解析してください
...
"""
```

**システムプロンプトの役割:**
- AIの振る舞いを指示
- 現在の状態（日時、会議室リスト）を伝える
- ビジネスルール（30分刻み、営業時間など）を説明

**動的な情報:**
- 現在日時（リクエストごとに変わる）
- 会議室リスト（configから取得）
- 「今から」予約用の時刻情報

**初心者向けポイント:**
- f-string（`f"..."`）で変数を埋め込み
- プロンプトの品質がAIの精度を大きく左右する
- 詳細で具体的な指示が重要

### 5. チャット処理のメインフロー

```python
def process_chat_message(self, message, user_name="guest", session_id=None):
    """ユーザーのチャットメッセージを処理し、Function Callingで既存APIを呼び出し"""

    # 1. 言語検出
    user_language = self._detect_language(message)

    # 2. 会議室情報を取得
    rooms = models.get_rooms()
    room_info = "\n".join([f"- {room.name} (ID: {room.id}, 定員: {room.capacity}名)" for room in rooms])

    # 3. システムプロンプトを構築
    system_prompt = f"""..."""

    # 4. チャット履歴を取得
    messages = [{"role": "system", "content": system_prompt}]

    if session_id:
        history = self.redis_service.get_history(session_id)
        messages.extend(history)

    # 5. 現在のユーザーメッセージを追加
    messages.append({"role": "user", "content": message})

    # 6. OpenAI APIに送信
    response = self.client.chat.completions.create(
        model=self.model,
        messages=messages,
        tools=tools,
        tool_choice="auto",
        temperature=0.1
    )

    # 7. Tool呼び出しの処理
    msg = response.choices[0].message
    tool_calls = getattr(msg, "tool_calls", None)

    # 8. ユーザーメッセージを履歴に保存
    if session_id:
        self.redis_service.add_message(session_id, "user", message)

    # 9. Tool呼び出しがある場合
    if tool_calls:
        # ... Tool実行処理 ...
        return response_data

    # 10. 通常の応答（tool_calls がない場合）
    ai_response = msg.content
    if session_id:
        self.redis_service.add_message(session_id, "assistant", ai_response)

    return {"success": True, "response": ai_response, "action": "info"}
```

**処理フロー図:**
```
[ユーザーメッセージ]
    ↓
[言語検出]
    ↓
[システムプロンプト構築]
    ↓
[過去の履歴取得 (Redis)]
    ↓
[OpenAI APIに送信]
    ↓
[Tool呼び出しあり？]
    ├─ Yes → [Tool実行] → [結果をOpenAIに再送信] → [自然言語応答生成]
    └─ No  → [そのまま応答を返す]
    ↓
[履歴に保存 (Redis)]
    ↓
[ユーザーに応答]
```

**初心者向けポイント:**
- `tool_choice="auto"`: AIが必要に応じてツールを自動選択
- `temperature=0.1`: 低い値で応答を安定化（創造性を抑える）
- `getattr(msg, "tool_calls", None)`: 属性がなければNone

### 6. Tool実行処理

```python
if tool_calls:
    # アシスタントのメッセージ（tool_calls含む）を履歴に追加
    messages.append({
        "role": "assistant",
        "content": msg.content,
        "tool_calls": [
            {
                "id": call.id,
                "type": call.type,
                "function": {
                    "name": call.function.name,
                    "arguments": call.function.arguments
                }
            } for call in tool_calls
        ]
    })

    # 各tool_callの結果を取得してmessagesに追加
    for call in tool_calls:
        if call.type == "function":
            fn = call.function.name
            args_json = call.function.arguments or "{}"
            fn_args = json.loads(args_json)

            # 実際の関数を呼び出し
            tool_result = None
            if fn == "create_reservation":
                tool_result = self._execute_create_reservation(fn_args)
            elif fn == "find_available_rooms":
                tool_result = self._execute_find_available_rooms(fn_args)
            # ... 他の関数 ...

            # tool の実行結果をmessagesに追加
            messages.append({
                "role": "tool",
                "tool_call_id": call.id,
                "content": json.dumps(tool_result, ensure_ascii=False)
            })

    # LLMに再度リクエストしてレスポンスを生成させる
    second_response = self.client.chat.completions.create(
        model=self.model,
        messages=messages,
        temperature=0.1
    )

    final_message = second_response.choices[0].message
    ai_response = final_message.content
```

**Tool実行の流れ:**
1. AIが「この関数を呼んでください」と指示（tool_calls）
2. 指示された関数を実際に実行
3. 実行結果をmessagesに追加
4. 再度OpenAIに送信して、結果を自然言語に整形

**初心者向けポイント:**
- Function Callingは2段階のAPI呼び出し
  - 1回目: どの関数を呼ぶか決定
  - 2回目: 実行結果を元に応答生成
- `role: "tool"`: ツールの実行結果を表すロール

### 7. 各ツールの実装例

#### find_available_rooms - 空き部屋検索

```python
def _execute_find_available_rooms(self, args):
    """予約可能な部屋の検索を実行（結果をJSONで返す）"""
    try:
        date = args.get("date")
        start_time = args.get("start_time")
        duration = int(args.get("duration_minutes"))
        min_capacity = int(args.get("min_capacity")) if args.get("min_capacity") else None

        if not all([date, start_time, duration]):
            return {
                "success": False,
                "error": "検索に必要な情報が不足しています"
            }

        # ReservationServiceを呼び出し
        rooms = ReservationService.find_available_rooms_by_start_datetime_and_duration(
            date, start_time, duration
        )

        # min_capacityが指定されている場合、定員でフィルタリング
        if min_capacity is not None:
            rooms = [room for room in rooms if room.get("capacity", 0) >= min_capacity]

        return {
            "success": True,
            "rooms": rooms,
            "date": date,
            "start_time": start_time,
            "duration_minutes": duration,
            "min_capacity": min_capacity
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"空き状況の確認中にエラーが発生しました: {str(e)}"
        }
```

**定員フィルタリング:**
- AIがmin_capacityを設定すれば、定員条件で絞り込み
- 「10人以上入れる部屋」などの要求に対応

#### create_reservation - 予約作成

```python
def _execute_create_reservation(self, args):
    """予約を作成（結果をJSONで返す）"""
    url = f"{self.base_url}/api/reservations"

    data = {
        "room-id": str(args.get("room_id")),
        "date": args["date"],
        "start-time": args["start_time"],
        "end-time": args["end_time"]
    }

    try:
        response = requests.post(url, json=data, headers={"Content-Type": "application/json"})
        result = response.json()

        if response.status_code == 200 and result.get("success"):
            return {
                "success": True,
                "reservation": result["reservation"]
            }
        else:
            return {
                "success": False,
                "error": result.get('error', '不明なエラー')
            }

    except Exception as e:
        return {
            "success": False,
            "error": f"予約処理中にエラーが発生しました: {str(e)}"
        }
```

**HTTP経由でAPIを呼び出し:**
- 内部的には自分自身のAPIを呼び出し
- 統一されたエラーハンドリング

**初心者向けポイント:**
- `requests.post()`: HTTPリクエストを送信
- APIのレスポンスをそのままツールの結果として返す

#### get_my_reservations - 自分の予約一覧

```python
def _execute_get_my_reservations(self, args, user_name):
    """ユーザー自身の予約一覧を取得（結果をJSONで返す）"""
    try:
        date = args.get("date")
        result = ReservationService.get_reservations_by_username(user_name, date)

        if result.get("success"):
            return {
                "success": True,
                "reservations": result["reservations"],
                "date": date,
                "user_name": user_name
            }
        else:
            return {
                "success": False,
                "error": result.get("error", "予約状況の確認中にエラーが発生しました")
            }

    except Exception as e:
        return {
            "success": False,
            "error": f"確認処理中にエラーが発生しました: {str(e)}"
        }
```

**ユーザー名の自動設定:**
- AIは関数を呼ぶだけ、user_nameは自動的に設定
- ユーザーが他人の予約を見ることを防ぐ

### 8. アクション判定

```python
def _determine_action(self, function_name: str) -> str:
    """関数名からアクションタイプを判定"""
    action_map = {
        "create_reservation": "reserve",
        "find_available_rooms": "check",
        "get_reservations": "check",
        "get_my_reservations": "check",
        "cancel_reservation": "cancel"
    }
    return action_map.get(function_name, "info")
```

**アクションタイプ:**
- `reserve`: 予約作成
- `check`: 確認系
- `cancel`: キャンセル
- `info`: 情報提供のみ

**フロントエンドでの活用:**
- アクションに応じてUIを更新
- 例: reserve → 予約リストを再読み込み

## 会話例

### 例1: 空き部屋検索 → 予約

```
ユーザー: 「明日14時から1時間、空いてる部屋ある?」

AI: [find_available_rooms 実行]
    ↓
    date: "2025-01-16"
    start_time: "14:00"
    duration_minutes: 60
    ↓
    結果: [Room A, Room C]
    ↓
AI: 「空いている部屋:
     - Room A (定員: 4名)
     - Room C (定員: 15名)
     予約する部屋名を教えてください。」

ユーザー: 「Room A で」

AI: [create_reservation 実行]
    ↓
    room_id: 1  (AIが"Room A"から変換)
    date: "2025-01-16"
    start_time: "14:00"
    end_time: "15:00"
    ↓
AI: 「予約が完了しました！Room Aを2025-01-16 14:00から15:00まで予約しました。」
```

### 例2: 定員条件での検索

```
ユーザー: 「明日14時から1時間、10人以上入れる部屋ある?」

AI: [find_available_rooms 実行]
    ↓
    date: "2025-01-16"
    start_time: "14:00"
    duration_minutes: 60
    min_capacity: 10  ← AIが自動設定
    ↓
    結果: [Room C (15名), Room D (20名)]
    ↓
AI: 「空いている部屋:
     - Room C (定員: 15名)
     - Room D (定員: 20名)」
```

### 例3: 英語での会話

```
User: "Show me today's reservations"

AI: [get_reservations 実行]
    ↓
    date: "2025-01-15"
    ↓
AI: "Today's reservations:
     - Room A 14:00-15:00 (guest)"
```

## まとめ

### 主要な機能

| 機能 | 説明 |
|------|------|
| Function Calling | AIが自動的に関数を選択・実行 |
| 言語検出 | 日本語・英語を自動判定 |
| チャット履歴 | Redis経由で会話の文脈を保持 |
| 多段階処理 | 空き部屋検索 → 予約のフロー |
| 定員条件 | 「○人以上」などの条件に対応 |

### 学習のポイント

1. **Function Callingの仕組み**
   - ツール定義（名前、説明、パラメータ）
   - 2段階のAPI呼び出し
   - ツール実行結果の整形

2. **プロンプトエンジニアリング**
   - 詳細で具体的な指示が重要
   - 動的な情報（現在時刻など）の埋め込み
   - ビジネスルールの明示

3. **状態管理**
   - Redisでセッションごとに履歴を分離
   - 会話の文脈を保持

4. **エラーハンドリング**
   - 各ツールで統一されたエラー形式
   - ユーザーに分かりやすいメッセージ

5. **多言語対応**
   - 言語検出で自動切り替え
   - システムプロンプトで応答言語を指示

6. **ReservationServiceとの連携**
   - ビジネスロジックは分離
   - AIServiceは「橋渡し」の役割

# redis_service.py - Redisチャット履歴管理

## 概要
このファイルは、**Redisを使ったチャット履歴の管理**を担当します。
AIチャットボットが会話の文脈を理解するために、過去のやり取りをRedisに保存・取得します。

## 役割
- チャット履歴の保存（セッションごと）
- 過去の会話履歴の取得
- 履歴のクリア
- 自動的な有効期限管理（TTL）

## Redisとは？

**Redis**は、高速なインメモリデータストア（Key-Valueストア）です。

**特徴:**
- メモリ上で動作するため、非常に高速
- データに有効期限（TTL: Time To Live）を設定できる
- リスト、セット、ハッシュなど、豊富なデータ構造

**なぜチャット履歴にRedisを使う？**
1. **高速**: 毎回のチャットで過去履歴を読み込むため、速度が重要
2. **TTL**: 古い履歴を自動的に削除できる（24時間後など）
3. **セッション管理**: ユーザーごと・セッションごとに履歴を分離できる

## コードの詳細

### 1. クラスの初期化

```python
class RedisService:
    def __init__(self):
        # 環境変数から設定を取得
        redis_host = os.getenv('REDIS_HOST', 'localhost')
        redis_port = int(os.getenv('REDIS_PORT', 6379))
        redis_db = int(os.getenv('REDIS_DB', 0))
        redis_password = os.getenv('REDIS_PASSWORD')

        # Redis接続パラメータ
        redis_params = {
            'host': redis_host,
            'port': redis_port,
            'db': redis_db,
            'decode_responses': True
        }

        # パスワードが設定されている場合のみ追加
        if redis_password:
            redis_params['password'] = redis_password

        self.client = redis.Redis(**redis_params)

        # チャット履歴のTTL（デフォルト24時間）
        self.ttl = int(os.getenv('CHAT_HISTORY_TTL', 86400))
```

**環境変数:**
| 変数名 | デフォルト値 | 説明 |
|-------|------------|------|
| REDIS_HOST | localhost | Redisサーバーのホスト |
| REDIS_PORT | 6379 | Redisサーバーのポート |
| REDIS_DB | 0 | 使用するDB番号（0〜15） |
| REDIS_PASSWORD | なし | Redis認証パスワード |
| CHAT_HISTORY_TTL | 86400 | 履歴の有効期限（秒） |

**初心者向けポイント:**
- `os.getenv('KEY', 'default')`: 環境変数KEYが設定されていなければdefaultを使用
- `decode_responses=True`: Redisから取得したデータを自動的に文字列にデコード
- `**redis_params`: 辞書をキーワード引数として展開（アンパック）

**TTLの計算:**
- 86400秒 = 60秒 × 60分 × 24時間 = 24時間

### 2. Redisキーの生成

```python
def _get_key(self, session_id: str) -> str:
    """セッションIDからRedisキーを生成"""
    return f"chat_history:{session_id}"
```

**説明:**
- セッションIDを使って、Redisのキーを生成
- プレフィックス`chat_history:`を付けることで、他のデータと区別

**例:**
```python
session_id = "user123_20250115"
key = self._get_key(session_id)
print(key)  # "chat_history:user123_20250115"
```

**初心者向けポイント:**
- `_get_key()`の先頭のアンダースコアは、「内部使用の関数」を意味する慣習
- 外部からは呼ばれない、クラス内部でのみ使う関数

### 3. メッセージの追加

```python
def add_message(self, session_id: str, role: str, content: str) -> None:
    """
    チャット履歴にメッセージを追加

    Args:
        session_id: セッションID
        role: メッセージのロール（user, assistant, systemなど）
        content: メッセージ内容
    """
    key = self._get_key(session_id)
    message = {
        "role": role,
        "content": content
    }

    # リストに追加
    self.client.rpush(key, json.dumps(message, ensure_ascii=False))

    # TTLを設定（既存のTTLをリフレッシュ）
    self.client.expire(key, self.ttl)
```

**処理の流れ:**
1. セッションIDからRedisキーを生成
2. メッセージを辞書形式で作成
3. JSON文字列に変換してRedisのリストに追加（`rpush`: 右端に追加）
4. TTL（有効期限）をリフレッシュ

**使用例:**
```python
redis_service = RedisService()

# ユーザーメッセージを追加
redis_service.add_message("session_001", "user", "今日の予約を教えて")

# アシスタントメッセージを追加
redis_service.add_message("session_001", "assistant", "本日の予約はありません")
```

**Redisでのデータ構造:**
```
Key: "chat_history:session_001"
Value: [
    '{"role": "user", "content": "今日の予約を教えて"}',
    '{"role": "assistant", "content": "本日の予約はありません"}'
]
TTL: 86400秒
```

**初心者向けポイント:**
- `json.dumps()`: Python辞書をJSON文字列に変換
- `ensure_ascii=False`: 日本語をそのまま保存（エスケープしない）
- `rpush`: Redis Listの右端（末尾）に追加するコマンド
- `expire`: キーに有効期限を設定（秒単位）

### 4. 履歴の取得

```python
def get_history(self, session_id: str) -> List[Dict[str, str]]:
    """
    セッションのチャット履歴を取得

    Args:
        session_id: セッションID

    Returns:
        チャット履歴のリスト（role, contentを含む辞書のリスト）
    """
    key = self._get_key(session_id)
    messages = self.client.lrange(key, 0, -1)

    return [json.loads(msg) for msg in messages]
```

**処理の流れ:**
1. セッションIDからRedisキーを生成
2. Redisリストの全要素を取得（`lrange 0 -1`）
3. 各JSON文字列をPython辞書に変換して返す

**使用例:**
```python
history = redis_service.get_history("session_001")
print(history)
# [
#     {"role": "user", "content": "今日の予約を教えて"},
#     {"role": "assistant", "content": "本日の予約はありません"}
# ]
```

**初心者向けポイント:**
- `lrange(key, 0, -1)`: Redisリストの全要素を取得
  - `0`: 先頭から
  - `-1`: 末尾まで
- `json.loads()`: JSON文字列をPython辞書に変換
- リスト内包表記: `[json.loads(msg) for msg in messages]`

### 5. 履歴のクリア

```python
def clear_history(self, session_id: str) -> None:
    """
    セッションのチャット履歴をクリア

    Args:
        session_id: セッションID
    """
    key = self._get_key(session_id)
    self.client.delete(key)
```

**使用例:**
```python
redis_service.clear_history("session_001")
# これ以降、session_001の履歴は空になる
```

**初心者向けポイント:**
- `delete`: Redisからキーを削除
- 削除後は、get_history()で空のリストが返る

### 6. 履歴件数の取得

```python
def get_history_count(self, session_id: str) -> int:
    """
    セッションのチャット履歴件数を取得

    Args:
        session_id: セッションID

    Returns:
        メッセージ数
    """
    key = self._get_key(session_id)
    return self.client.llen(key)
```

**使用例:**
```python
count = redis_service.get_history_count("session_001")
print(f"会話数: {count}")  # 会話数: 10
```

**初心者向けポイント:**
- `llen`: Redisリストの長さを取得
- 履歴が多すぎる場合の制御などに使える

## AIServiceでの使用例

```python
# ai_service.pyでの実際の使用例

class AIService:
    def __init__(self):
        self.redis_service = RedisService()

    def process_chat_message(self, message, user_name, session_id):
        # 過去の履歴を取得
        history = self.redis_service.get_history(session_id)
        messages.extend(history)

        # 現在のユーザーメッセージを追加
        messages.append({"role": "user", "content": message})

        # OpenAI APIに送信
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            ...
        )

        # ユーザーメッセージを履歴に保存
        self.redis_service.add_message(session_id, "user", message)

        # アシスタントの応答を履歴に保存
        ai_response = response.choices[0].message.content
        self.redis_service.add_message(session_id, "assistant", ai_response)

        return {"success": True, "response": ai_response}
```

**会話の流れ:**
1. ユーザー: 「今日の予約を教えて」
2. Redis: 過去の履歴を取得（もしあれば）
3. OpenAI: 履歴 + 新規メッセージで応答生成
4. Redis: ユーザーメッセージとAI応答を保存
5. 次回の会話で、この履歴が使われる

## データフロー図

```
[ユーザー] ──①メッセージ──> [AIService]
                                  │
                                  ├──②履歴取得──> [Redis]
                                  │                 │
                                  │<───③過去履歴────┘
                                  │
                                  ├──④履歴+新規──> [OpenAI API]
                                  │                 │
                                  │<───⑤AI応答──────┘
                                  │
                                  ├──⑥履歴保存──> [Redis]
                                  │
[ユーザー] <──⑦応答返却────────┘
```

## TTL（有効期限）の動作

```
時刻 0:00  - ユーザーがチャット → TTL: 24時間
時刻 12:00 - ユーザーがチャット → TTL: 24時間（リフレッシュ）
時刻 13:00 - ユーザーがチャット → TTL: 24時間（リフレッシュ）
...
最後のチャットから24時間後 - 自動的に履歴が削除される
```

**メリット:**
- 使われていない古い履歴が自動削除される
- Redisのメモリ使用量を抑えられる
- プライバシー保護（古い会話は自動消去）

## まとめ

### 主要メソッド

| メソッド | 引数 | 戻り値 | 用途 |
|---------|------|--------|------|
| add_message() | session_id, role, content | なし | メッセージを履歴に追加 |
| get_history() | session_id | List[Dict] | 履歴を取得 |
| clear_history() | session_id | なし | 履歴をクリア |
| get_history_count() | session_id | int | 履歴件数を取得 |

### 学習のポイント

1. **Redisはインメモリデータストア**
   - 高速だが、再起動すると消える（永続化設定可能）

2. **セッション管理**
   - session_idで履歴を分離
   - 複数ユーザーが同時に使っても混ざらない

3. **TTLの活用**
   - 自動的にデータを削除できる
   - メモリ節約とプライバシー保護

4. **JSONでの保存**
   - RedisにはPython辞書を直接保存できない
   - JSON文字列に変換して保存、取得時に辞書に戻す

5. **AIとの連携**
   - 過去の会話を含めてAIに送ることで、文脈を理解した応答が可能
   - 「その部屋を予約して」などの指示語が理解できる

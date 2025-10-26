# reservation_service.py - 予約ビジネスロジック

## 概要
このファイルは、**予約関連のビジネスロジック**を担当します。
データベース操作と業務ルールを組み合わせて、予約の作成・取得・キャンセル・空き部屋検索などの機能を提供します。

## 役割
- 予約の作成（重複チェック、時間帯検証）
- 予約一覧の取得（日付別、ユーザー別）
- 予約のキャンセル
- 空き部屋の検索（時間帯・定員条件）
- 入力データのバリデーション

## ビジネスロジックとは？

**ビジネスロジック**は、業務のルールや処理を実装したコードです。

**例: 予約システムのビジネスルール**
- 同じ時間に同じ部屋を2人が予約できない
- 営業時間外の予約はできない
- 開始時刻は終了時刻より前でなければならない

このようなルールを実装したのが`ReservationService`クラスです。

## コードの詳細

### クラス構造

```python
class ReservationService:
    """予約管理サービス"""
```

**初心者向けポイント:**
- `@staticmethod`デコレータを使った静的メソッド
- インスタンスを作らずに、`ReservationService.create_reservation()`のように呼び出せる
- 状態を持たないため、どこからでも安全に使える

### 1. 予約の作成

```python
@staticmethod
def create_reservation(room_id: int, user_name: str, date: str,
                     start_time: str, end_time: str) -> Dict[str, Any]:
```

**引数:**
| 引数名 | 型 | 説明 | 例 |
|-------|---|------|---|
| room_id | int | 会議室ID | 1 |
| user_name | str | ユーザー名 | "guest" |
| date | str | 日付 | "2025-01-15" |
| start_time | str | 開始時刻 | "14:00" |
| end_time | str | 終了時刻 | "15:00" |

**戻り値（成功時）:**
```python
{
    "success": True,
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

**戻り値（失敗時）:**
```python
{
    "success": False,
    "error": "指定された時間帯は既に予約されています"
}
```

**処理の流れ:**

```python
# 1. 入力検証
validation_result = ReservationService._validate_reservation_data(
    room_id, date, start_time, end_time
)
if not validation_result["valid"]:
    return {"success": False, "error": validation_result["error"]}

# 2. 日時変換（文字列 → datetime）
start_datetime = parse_datetime_jst(date, start_time)
end_datetime = parse_datetime_jst(date, end_time)

# 3. 重複チェック
with models.get_session() as session:
    if ReservationService._check_conflict(session, room_id, start_datetime, end_datetime):
        return {"success": False, "error": "指定された時間帯は既に予約されています"}

    # 4. 予約作成
    reservation = models.Reservation(
        room_id=room_id,
        user_name=user_name,
        start_time=start_datetime,
        end_time=end_datetime
    )

    session.add(reservation)
    session.commit()

    # 5. 結果を返す
    return {"success": True, ...}
```

**初心者向けポイント:**
- `with models.get_session() as session:`: セッションを自動的に閉じる
- トランザクション管理: `commit()`で確定、エラー時は自動的にロールバック

### 2. バリデーション（検証）

```python
@staticmethod
def _validate_reservation_data(room_id: int, date: str, start_time: str, end_time: str) -> Dict[str, Any]:
    """予約データの基本検証"""
    # 必須項目チェック
    if not all([room_id, date, start_time, end_time]):
        return {"valid": False, "error": "必須項目が不足しています"}

    # 時刻文字列をtimeオブジェクトに変換
    start_time = datetime.strptime(start_time, "%H:%M").time()
    end_time = datetime.strptime(end_time, "%H:%M").time()

    # 営業時間チェック
    earliest = time(STARTHOUR, 0)  # 7:00
    latest = time(ENDHOUR, 0)      # 22:00

    if start_time < earliest or end_time > latest:
        return {"valid": False, "error": "7時から22時の間で予約してください"}

    # 開始時刻が終了時刻より前かチェック
    if start_time >= end_time:
        return {"valid": False, "error": "終了時刻は開始時刻より後に設定してください"}

    return {"valid": True}
```

**検証内容:**
1. 必須項目が全て入力されているか
2. 開始・終了時刻が営業時間内か
3. 開始時刻が終了時刻より前か

**初心者向けポイント:**
- `all([...])`: リスト内の全てがTrueなら True
- 早期リターン: 問題があれば即座にエラーを返す

### 3. 重複チェック

```python
@staticmethod
def _check_conflict(session, room_id: int, new_start_time: datetime, new_end_time: datetime) -> bool:
    """時間重複をチェック"""
    existing = session.scalars(
        select(models.Reservation).where(
            models.Reservation.room_id == room_id,
            models.Reservation.start_time < new_end_time,
            models.Reservation.end_time > new_start_time
        )
    ).first()

    return existing is not None
```

**重複判定のロジック:**
既存の予約と重複する = 以下の条件を**両方**満たす場合

```
既存の開始時刻 < 新規の終了時刻
AND
既存の終了時刻 > 新規の開始時刻
```

**図解:**
```
【ケース1: 重複する】
既存: |====|
新規:    |====|
      ↑重複部分あり

【ケース2: 重複しない】
既存: |====|
新規:        |====|
      ↑重複なし
```

**初心者向けポイント:**
- `.first()`: 最初の1件を取得（なければNone）
- `existing is not None`: 重複する予約が存在すればTrue

### 4. 予約一覧の取得（日付別）

```python
@staticmethod
def get_reservations_by_date(date: str) -> Dict[str, Any]:
    """指定日の予約一覧を取得する"""
    # JSTで日付処理
    target_date_jst = parse_datetime_jst(date, "00:00")
    next_day_jst = target_date_jst + timedelta(days=1)

    with models.get_session() as session:
        stmt = select(models.Reservation).join(models.Room).where(
            models.Reservation.start_time >= target_date_jst,
            models.Reservation.start_time < next_day_jst
        )
        reservations = session.scalars(stmt).all()

        result = []
        for reservation in reservations:
            start_time_jst = convert_to_jst(reservation.start_time)
            end_time_jst = convert_to_jst(reservation.end_time)

            result.append({
                "id": reservation.id,
                "room_id": reservation.room_id,
                "room_name": reservation.room.name,
                "user_name": reservation.user_name,
                "start_time": format_jst_time(start_time_jst),
                "end_time": format_jst_time(end_time_jst),
                "date": date
            })

        return {"success": True, "reservations": result}
```

**検索条件:**
- 開始時刻が指定日の00:00以降
- 開始時刻が翌日の00:00より前

**図解:**
```
2025-01-15 の予約を検索

target_date_jst: 2025-01-15 00:00:00
next_day_jst:    2025-01-16 00:00:00

検索範囲: 00:00:00 <= start_time < 翌日00:00:00
```

**初心者向けポイント:**
- `.join(models.Room)`: 会議室情報も一緒に取得
- `reservation.room.name`: リレーションシップでアクセス可能
- タイムゾーン変換を忘れずに行う

### 5. 予約一覧の取得（ユーザー別）

```python
@staticmethod
def get_reservations_by_username(user_name: str, date: Optional[str] = None) -> Dict[str, Any]:
    """指定されたユーザー名の予約一覧を取得する"""
    with models.get_session() as session:
        # 基本クエリ
        stmt = (
            select(models.Reservation)
            .where(models.Reservation.user_name == user_name)
            .options(selectinload(models.Reservation.room))
            .order_by(models.Reservation.start_time)
        )

        # 日付が指定されている場合はフィルタを追加
        if date:
            target_date_jst = parse_datetime_jst(date, "00:00")
            next_day_jst = target_date_jst + timedelta(days=1)
            stmt = stmt.where(
                models.Reservation.start_time >= target_date_jst,
                models.Reservation.start_time < next_day_jst
            )

        reservations = session.scalars(stmt).all()
        # ... 結果を整形して返す
```

**機能:**
- `date`を指定すれば、特定日のユーザー予約のみ
- `date`を省略すれば、全期間のユーザー予約

**初心者向けポイント:**
- `Optional[str] = None`: 引数が省略可能
- `selectinload()`: N+1問題を防ぐための最適化
- 条件付きクエリ: `if date:`で動的にフィルタを追加

### 6. 空き部屋の検索

```python
@staticmethod
def find_available_rooms_by_start_datetime_and_duration(
    date: str, start_time: str, duration_minutes: int
) -> List[Dict[str, Any]]:
    """指定した開始日時と利用時間で空いている部屋の情報を返す"""

    # 入力検証
    if duration_minutes <= 0:
        raise ValueError("利用時間は0分より大きくなければなりません")

    # 日時計算
    start_datetime = parse_datetime_jst(date, start_time)
    end_datetime = start_datetime + timedelta(minutes=duration_minutes)

    # 営業時間チェック
    if start_datetime.time() < time(STARTHOUR,0) or end_datetime.time() > time(ENDHOUR,0):
        raise ValueError("開始時刻もしくは終了時刻が業務時間外です")

    # 重複のない部屋を検索
    with models.get_session() as session:
        overlap = and_(
            models.Reservation.room_id == models.Room.id,
            models.Reservation.start_time < end_datetime,
            models.Reservation.end_time > start_datetime,
        )

        subq = select(models.Reservation.id).where(overlap)
        stmt = (
            select(models.Room)
            .where(~exists(subq).correlate(models.Room))
            .order_by(models.Room.id)
        )

        rooms = session.scalars(stmt).all()

        return [{"id": room.id, "name": room.name, "capacity": room.capacity} for room in rooms]
```

**検索ロジック:**
1. 指定時間帯と重複する予約がある部屋を見つける（サブクエリ）
2. その部屋を除外した部屋を返す（NOT EXISTS）

**SQL的な考え方:**
```sql
SELECT * FROM rooms
WHERE NOT EXISTS (
    SELECT 1 FROM reservations
    WHERE reservations.room_id = rooms.id
    AND reservations.start_time < '新規終了時刻'
    AND reservations.end_time > '新規開始時刻'
)
```

**初心者向けポイント:**
- `~exists()`: NOT EXISTS（存在しない）
- `.correlate()`: サブクエリと外側のクエリを相関させる
- `and_()`: 複数の条件をANDで結合

**戻り値例:**
```python
[
    {"id": 1, "name": "Room A", "capacity": 4},
    {"id": 3, "name": "Room C", "capacity": 15}
]
```

### 7. 予約のキャンセル

```python
@staticmethod
def cancel_reservation(reservation_id: int) -> Dict[str, Any]:
    """予約をキャンセルする"""
    with models.get_session() as session:
        reservation = session.scalars(
            select(models.Reservation).where(models.Reservation.id == reservation_id)
        ).first()

        if not reservation:
            return {"success": False, "error": "予約が見つかりません"}

        session.delete(reservation)
        session.commit()

        return {
            "success": True,
            "message": "予約をキャンセルしました",
            "reservation_id": reservation_id
        }
```

**処理の流れ:**
1. 予約IDで予約を検索
2. 見つからなければエラー
3. 見つかれば削除して確定

**初心者向けポイント:**
- `session.delete()`: レコードを削除
- `commit()`で削除が確定

## 使用例

### AIServiceからの呼び出し

```python
# 予約作成
result = ReservationService.create_reservation(
    room_id=1,
    user_name="guest",
    date="2025-01-15",
    start_time="14:00",
    end_time="15:00"
)

if result["success"]:
    print(f"予約完了: {result['reservation']}")
else:
    print(f"エラー: {result['error']}")

# 空き部屋検索
rooms = ReservationService.find_available_rooms_by_start_datetime_and_duration(
    date="2025-01-15",
    start_time="14:00",
    duration_minutes=60
)

for room in rooms:
    print(f"{room['name']} (定員: {room['capacity']}名)")
```

## エラーハンドリング

各メソッドは、例外をキャッチして辞書形式で結果を返します。

```python
try:
    # ... 処理 ...
    return {"success": True, ...}

except ValueError:
    return {"success": False, "error": "日時の形式が正しくありません"}
except Exception as e:
    return {"success": False, "error": f"サーバーエラーが発生しました: {str(e)}"}
```

**メリット:**
- 呼び出し側でエラー処理が簡単
- 統一されたレスポンス形式

## まとめ

### 主要メソッド

| メソッド | 用途 | 戻り値 |
|---------|------|--------|
| create_reservation() | 予約作成 | {"success": bool, ...} |
| get_reservations_by_date() | 日付別予約一覧 | {"success": bool, "reservations": [...]} |
| get_reservations_by_username() | ユーザー別予約一覧 | {"success": bool, "reservations": [...]} |
| find_available_rooms_by_start_datetime_and_duration() | 空き部屋検索 | [{"id": int, "name": str, "capacity": int}] |
| cancel_reservation() | 予約キャンセル | {"success": bool, ...} |

### 学習のポイント

1. **ビジネスロジックの分離**
   - データベース操作とビジネスルールを1つのクラスにまとめる
   - API層（app.py）から呼び出しやすくする

2. **バリデーション**
   - データを保存する前に必ず検証
   - エラーメッセージをユーザーに分かりやすく

3. **トランザクション管理**
   - `with session:`で安全にDB操作
   - エラー時は自動的にロールバック

4. **重複チェックの重要性**
   - 同じ部屋の二重予約を防ぐ
   - データの整合性を保つ

5. **統一されたレスポンス形式**
   - 成功/失敗を`success`キーで判定
   - エラー時は`error`キーにメッセージ

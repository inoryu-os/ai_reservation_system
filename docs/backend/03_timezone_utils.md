# timezone_utils.py - タイムゾーン処理ユーティリティ

## 概要
このファイルは、**日本標準時（JST）での日時処理**を担当します。
会議室予約システムでは、すべての時刻をJSTで統一して扱う必要があるため、このユーティリティが重要な役割を果たします。

## 役割
- JST（日本時間）での日時取得・変換
- 日時文字列のパース（解析）とフォーマット
- 30分刻みの時刻処理（予約システム特有の要件）
- 「今から予約」機能の時刻計算

## なぜタイムゾーン処理が必要？

サーバーが海外にある場合や、国際的なサービスでは、時刻のタイムゾーンを意識する必要があります。

**例:**
- サーバー時刻: UTC 2025-01-15 05:00
- 日本時刻: JST 2025-01-15 14:00（UTC + 9時間）

このシステムでは、すべてJSTで統一することで混乱を防ぎます。

## コードの詳細

### 1. JST定義

```python
JST = timezone(timedelta(hours=9))
```

**説明:**
- UTC（協定世界時）から+9時間のタイムゾーンを定義
- 日本はUTC+9なので、`timedelta(hours=9)`

**初心者向けポイント:**
- `timedelta`: 時間の差分を表すオブジェクト
- `timezone`: タイムゾーン情報を持つオブジェクト

### 2. 現在時刻の取得

```python
def get_jst_now() -> datetime:
    """現在のJST時刻を取得"""
    return datetime.now(JST)
```

**使用例:**
```python
now = get_jst_now()
print(now)  # 2025-01-15 14:30:45+09:00
```

**初心者向けポイント:**
- 通常の`datetime.now()`はサーバーのローカル時刻
- この関数は必ずJSTで時刻を返す

### 3. 日付文字列のパース（解析）

#### parse_date_jst() - 日付のみ

```python
def parse_date_jst(date_str: str) -> datetime:
    """日付文字列(YYYY-MM-DD)をJSTのdatetimeに変換"""
    return datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=JST)
```

**使用例:**
```python
date = parse_date_jst("2025-01-15")
print(date)  # 2025-01-15 00:00:00+09:00
```

**フォーマット記号:**
- `%Y`: 4桁の年（2025）
- `%m`: 2桁の月（01）
- `%d`: 2桁の日（15）

#### parse_datetime_jst() - 日付と時刻

```python
def parse_datetime_jst(date_str: str, time_str: str) -> datetime:
    """日付文字列と時刻文字列をJSTのdatetimeに変換"""
    datetime_str = f"{date_str} {time_str}"
    return datetime.strptime(datetime_str, "%Y-%m-%d %H:%M").replace(tzinfo=JST)
```

**使用例:**
```python
dt = parse_datetime_jst("2025-01-15", "14:30")
print(dt)  # 2025-01-15 14:30:00+09:00
```

**フォーマット記号:**
- `%H`: 24時間形式の時（14）
- `%M`: 分（30）

### 4. datetime → 文字列変換

#### format_jst_date() - 日付文字列

```python
def format_jst_date(dt: datetime) -> str:
    """JSTのdatetimeを日付文字列(YYYY-MM-DD)に変換"""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=JST)
    return dt.strftime("%Y-%m-%d")
```

**使用例:**
```python
now = get_jst_now()
date_str = format_jst_date(now)
print(date_str)  # "2025-01-15"
```

#### format_jst_time() - 時刻文字列

```python
def format_jst_time(dt: datetime) -> str:
    """JSTのdatetimeを時刻文字列(HH:MM)に変換"""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=JST)
    return dt.strftime("%H:%M")
```

**使用例:**
```python
now = get_jst_now()
time_str = format_jst_time(now)
print(time_str)  # "14:30"
```

### 5. タイムゾーン変換

```python
def convert_to_jst(dt: Optional[datetime]) -> Optional[datetime]:
    """任意のdatetimeをJSTに変換"""
    if dt is None:
        return None

    if dt.tzinfo is None:
        # ナイーブなdatetimeはJSTとして扱う
        return dt.replace(tzinfo=JST)
    else:
        # タイムゾーン情報がある場合はJSTに変換
        return dt.astimezone(JST)
```

**ナイーブなdatetimeとは？**
- タイムゾーン情報がないdatetimeオブジェクト
- 例: `datetime(2025, 1, 15, 14, 30)` ← tzinfoがない

**使用例:**
```python
# ナイーブなdatetime
naive_dt = datetime(2025, 1, 15, 14, 30)
jst_dt = convert_to_jst(naive_dt)
print(jst_dt)  # 2025-01-15 14:30:00+09:00

# UTC時刻
utc_dt = datetime(2025, 1, 15, 5, 30, tzinfo=timezone.utc)
jst_dt = convert_to_jst(utc_dt)
print(jst_dt)  # 2025-01-15 14:30:00+09:00
```

### 6. システムタイムゾーン設定

```python
def setup_timezone():
    """アプリケーション全体のタイムゾーンをJSTに設定"""
    os.environ['TZ'] = 'Asia/Tokyo'

    try:
        import time
        time.tzset()
    except AttributeError:
        # Windows環境では tzset が利用できない場合がある
        pass
```

**説明:**
- アプリ起動時に一度だけ実行
- システム全体のタイムゾーンをJSTに設定

**使用箇所:**
- app.py の冒頭で`setup_timezone()`を呼び出し

### 7. 30分刻み処理（予約システム特有）

このシステムでは、予約時刻を30分刻み（00分 or 30分）に制限しています。

#### round_down_to_30min() - 30分単位で切り下げ

```python
def round_down_to_30min(dt: datetime) -> datetime:
    """
    時刻を30分刻みで切り下げ

    例:
        14:04 → 14:00
        14:35 → 14:30
        14:00 → 14:00
        14:30 → 14:30
    """
    minutes = dt.minute
    rounded_minutes = (minutes // 30) * 30  # 0 or 30
    return dt.replace(minute=rounded_minutes, second=0, microsecond=0)
```

**ロジック解説:**
- `//`は整数除算（切り捨て除算）
- `14:04` → `minutes = 4` → `(4 // 30) * 30 = 0 * 30 = 0`
- `14:35` → `minutes = 35` → `(35 // 30) * 30 = 1 * 30 = 30`

**使用例:**
```python
dt = parse_datetime_jst("2025-01-15", "14:04")
rounded = round_down_to_30min(dt)
print(format_jst_time(rounded))  # "14:00"
```

#### get_next_30min_slot() - 次の30分区切り

```python
def get_next_30min_slot(dt: datetime) -> datetime:
    """
    次の30分区切りを取得

    例:
        14:04 → 14:30
        14:30 → 15:00
        14:00 → 14:30
        14:35 → 15:00
    """
    rounded_down = round_down_to_30min(dt)
    return rounded_down + timedelta(minutes=30)
```

**使用例:**
```python
dt = parse_datetime_jst("2025-01-15", "14:04")
next_slot = get_next_30min_slot(dt)
print(format_jst_time(next_slot))  # "14:30"

dt = parse_datetime_jst("2025-01-15", "14:30")
next_slot = get_next_30min_slot(dt)
print(format_jst_time(next_slot))  # "15:00"
```

### 8. 「今から予約」の時刻計算

```python
def calculate_reservation_time_for_now(current_time: datetime, duration_minutes: int) -> tuple[str, str]:
    """
    「今から」の予約時刻を計算

    ロジック:
        - 開始時刻 = 現在時刻を30分刻みで切り下げ
        - 終了時刻 = 次の30分区切り + 利用時間

    例:
        14:04に「今から30分」 → ("14:00", "15:00")
            - 開始: 14:00 (切り下げ)
            - 終了: 14:30 (次の区切り) + 30分 = 15:00

        14:04に「今から60分」 → ("14:00", "15:30")
            - 開始: 14:00 (切り下げ)
            - 終了: 14:30 (次の区切り) + 60分 = 15:30
    """
    start_dt = round_down_to_30min(current_time)
    next_slot_dt = get_next_30min_slot(current_time)
    end_dt = next_slot_dt + timedelta(minutes=duration_minutes)

    return (format_jst_time(start_dt), format_jst_time(end_dt))
```

**なぜこのロジック？**
- ユーザーが「今から30分」と言った場合、既に進行中の30分区切りは使わない
- 次の区切りから利用開始する設計

**使用例:**
```python
# 現在14:04の場合
now = parse_datetime_jst("2025-01-15", "14:04")

# 今から30分利用
start, end = calculate_reservation_time_for_now(now, 30)
print(f"開始: {start}, 終了: {end}")  # 開始: 14:00, 終了: 15:00

# 今から60分利用
start, end = calculate_reservation_time_for_now(now, 60)
print(f"開始: {start}, 終了: {end}")  # 開始: 14:00, 終了: 15:30
```

**実際のユースケース:**
- AIServiceのシステムプロンプトで使用
- ユーザーが「今から30分予約したい」と言った際の時刻計算

## 関数一覧まとめ

| 関数名 | 入力 | 出力 | 用途 |
|-------|------|------|------|
| get_jst_now() | なし | datetime | 現在のJST時刻を取得 |
| parse_date_jst() | "2025-01-15" | datetime | 日付文字列をJSTに変換 |
| parse_datetime_jst() | "2025-01-15", "14:30" | datetime | 日時文字列をJSTに変換 |
| format_jst_date() | datetime | "2025-01-15" | datetimeを日付文字列に |
| format_jst_time() | datetime | "14:30" | datetimeを時刻文字列に |
| convert_to_jst() | datetime | datetime | 任意のdatetimeをJSTに |
| setup_timezone() | なし | なし | システム全体をJSTに設定 |
| round_down_to_30min() | datetime | datetime | 30分単位で切り下げ |
| get_next_30min_slot() | datetime | datetime | 次の30分区切りを取得 |
| calculate_reservation_time_for_now() | datetime, int | (str, str) | 「今から」の予約時刻計算 |

## 学習のポイント

1. **タイムゾーン付きdatetimeを使う**
   - `tzinfo`を常に設定することで、時刻の曖昧さを排除

2. **文字列とdatetimeの相互変換**
   - パース: `strptime()` （文字列 → datetime）
   - フォーマット: `strftime()` （datetime → 文字列）

3. **時間計算はtimedeltaを使う**
   - 加算: `dt + timedelta(hours=1)`
   - 減算: `dt - timedelta(days=1)`

4. **業務ロジックに合わせたユーティリティ**
   - 30分刻み処理は、このシステム特有の要件
   - 業務要件に合わせて、便利な関数を作る

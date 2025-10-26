# config.py - 設定ファイル

## 概要
このファイルは、会議室予約システムの**基本設定**を管理します。
会議室の情報や営業時間など、システム全体で使用される定数を定義しています。

## 役割
- 会議室の名前、定員の設定
- 予約可能な営業時間の設定

## コードの詳細

### 1. 会議室の設定 (ROOMS_CONFIG)

```python
ROOMS_CONFIG = [
    {"name": "Room A", "capacity": 4},
    {"name": "Room B", "capacity": 6},
    {"name": "Room C", "capacity": 15},
    {"name": "Room D", "capacity": 20},
]
```

**説明:**
- `ROOMS_CONFIG`は会議室の情報を保持するリストです
- 各会議室は辞書型で定義されます
  - `name`: 会議室の名前（文字列）
  - `capacity`: 収容可能人数（整数）

**初心者向けポイント:**
- リスト内の辞書は、データベースの初期化時に使われます
- 会議室を追加したい場合は、この配列に新しい辞書を追加するだけです

**例: 新しい会議室を追加する場合**
```python
ROOMS_CONFIG = [
    {"name": "Room A", "capacity": 4},
    {"name": "Room B", "capacity": 6},
    {"name": "Room C", "capacity": 15},
    {"name": "Room D", "capacity": 20},
    {"name": "Room E", "capacity": 30},  # ← 新しく追加
]
```

### 2. 営業時間の設定 (STARTHOUR, ENDHOUR)

```python
STARTHOUR = 7   # 営業開始時刻（7時）
ENDHOUR = 22    # 営業終了時刻（22時）
```

**説明:**
- `STARTHOUR`: 予約可能な開始時刻（24時間形式）
- `ENDHOUR`: 予約可能な終了時刻（24時間形式）
- この例では、7:00〜22:00の間のみ予約が可能です

**初心者向けポイント:**
- これらの値は、予約のバリデーション（検証）で使われます
- 例: ユーザーが23:00に予約しようとすると、エラーが返されます

**使用例:**
```python
# models.pyでの使用例
if not (earliest <= value.time() <= latest):
    raise ValueError(f"{key} must be between 07:00 and 22:00")
```

## このファイルが使われる場所

1. **models.py**: データベースの初期化、時刻のバリデーション
2. **reservation_service.py**: 予約作成時の時刻チェック
3. **ai_service.py**: AIがシステムプロンプトで営業時間を理解する

## まとめ

| 設定項目 | 内容 | デフォルト値 |
|---------|------|------------|
| ROOMS_CONFIG | 会議室の名前と定員 | Room A〜D (4〜20人) |
| STARTHOUR | 営業開始時刻 | 7時 |
| ENDHOUR | 営業終了時刻 | 22時 |

**変更のヒント:**
- 営業時間を9:00〜18:00に変更したい場合 → `STARTHOUR = 9`, `ENDHOUR = 18`
- 会議室を増やしたい場合 → `ROOMS_CONFIG`にエントリを追加

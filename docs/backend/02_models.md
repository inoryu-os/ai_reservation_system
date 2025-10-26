# models.py - データベースモデル

## 概要
このファイルは、会議室予約システムの**データベース構造**を定義します。
SQLAlchemyというORM（Object-Relational Mapping）ライブラリを使って、Pythonのクラスとデータベースのテーブルを紐付けます。

## 役割
- データベースのテーブル定義（Room, Reservation）
- データベースの初期化と会議室の同期
- セッション管理

## 主要な技術

### ORM（Object-Relational Mapping）とは？
通常、データベースを操作するにはSQLという言語を書く必要がありますが、ORMを使うとPythonのコードだけでデータベース操作ができます。

**例: ORMを使わない場合（SQL）**
```sql
SELECT * FROM rooms WHERE capacity > 10;
```

**例: ORMを使う場合（Python）**
```python
rooms = session.query(Room).filter(Room.capacity > 10).all()
```

## コードの詳細

### 1. データベース接続設定

```python
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///meeting_rooms.db')
```

**説明:**
- 環境変数`DATABASE_URL`が設定されていればそれを使用
- 設定されていなければ、デフォルトでSQLiteデータベース（meeting_rooms.db）を使用

**初心者向けポイント:**
- SQLiteはファイルベースの軽量データベースで、インストール不要
- 本番環境ではPostgreSQLやMySQLなどに切り替え可能

### 2. Baseクラス

```python
class Base(DeclarativeBase):
    pass
```

**説明:**
- すべてのモデルクラスの親クラス
- SQLAlchemyが自動的にテーブルを作成するための基盤

### 3. Roomモデル（会議室テーブル）

```python
class Room(Base):
    __tablename__ = 'rooms'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)

    reservations: Mapped[List["Reservation"]] = relationship(
        "Reservation", back_populates="room", cascade="all, delete-orphan"
    )
```

**テーブル構造:**
| カラム名 | 型 | 説明 | 制約 |
|---------|---|------|-----|
| id | Integer | 会議室のID | 主キー、自動採番 |
| name | String | 会議室名 | 一意（重複不可）、必須 |
| capacity | Integer | 収容人数 | 必須 |

**リレーションシップ:**
- `reservations`: この会議室に紐づく予約のリスト
- `cascade="all, delete-orphan"`: 会議室を削除すると、その予約も自動的に削除される

**初心者向けポイント:**
- `primary_key=True`: このカラムが主キー（一意の識別子）
- `autoincrement=True`: IDが自動的に1, 2, 3...と増えていく
- `unique=True`: 同じ名前の会議室は作れない
- `nullable=False`: 必須項目（空白不可）

### 4. Reservationモデル（予約テーブル）

```python
class Reservation(Base):
    __tablename__ = 'reservations'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    room_id: Mapped[int] = mapped_column(ForeignKey('rooms.id'), nullable=False)
    user_name: Mapped[str] = mapped_column(String, nullable=False)
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    room: Mapped["Room"] = relationship("Room", back_populates="reservations")
```

**テーブル構造:**
| カラム名 | 型 | 説明 | 制約 |
|---------|---|------|-----|
| id | Integer | 予約ID | 主キー、自動採番 |
| room_id | Integer | 会議室ID | 外部キー（rooms.id）、必須 |
| user_name | String | ユーザー名 | 必須 |
| start_time | DateTime | 開始時刻 | 必須 |
| end_time | DateTime | 終了時刻 | 必須 |

**リレーションシップ:**
- `room`: この予約が紐づく会議室オブジェクト

**初心者向けポイント:**
- `ForeignKey('rooms.id')`: Roomテーブルのidと紐づく外部キー
- 外部キーによって、予約がどの会議室のものか分かる

### 5. バリデーション（検証）

```python
@validates("start_time", "end_time")
def validate_time(self, key, value):
    earliest = time(STARTHOUR, 0)  # 7:00
    latest = time(ENDHOUR, 0)      # 22:00
    if not (earliest <= value.time() <= latest):
        raise ValueError(f"{key} must be between 07:00 and 22:00")
    return value
```

**説明:**
- `@validates`デコレータで、データ保存前に自動的にチェック
- 開始・終了時刻が営業時間内（7:00〜22:00）かを検証
- 範囲外の場合はエラーを発生させる

**初心者向けポイント:**
- デコレータ（@validates）は、関数に機能を追加する仕組み
- この関数は自動的に呼ばれるので、手動で呼ぶ必要はない

### 6. データベースエンジンとセッション

```python
engine = create_engine(DATABASE_URL, echo=False)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)

def get_session() -> Session:
    return SessionLocal()
```

**説明:**
- `engine`: データベースへの接続エンジン
- `SessionLocal`: データベース操作のためのセッションファクトリ
- `get_session()`: 新しいセッションを取得する関数

**セッションとは？**
- データベースとのやり取りを管理するオブジェクト
- トランザクション（一連の操作）を制御する

**使用例:**
```python
with get_session() as session:
    room = session.get(Room, 1)  # IDが1の会議室を取得
    print(room.name)
```

### 7. init_db() - データベース初期化関数

```python
def init_db() -> List[Room]:
    """ROOMS_CONFIG と DB を同期（追加・削除）"""
    Base.metadata.create_all(bind=engine)

    with get_session() as session:
        # 既存の部屋名セット
        names_db = set(session.execute(select(Room.name)).scalars())

        # 追加：config の並び順で追加
        to_add_rooms: List[Room] = [
            Room(name=room["name"], capacity=room["capacity"])
            for room in ROOMS_CONFIG
            if room["name"] not in names_db
        ]
        if to_add_rooms:
            session.add_all(to_add_rooms)

        # 削除：DBにあるがconfigにない部屋
        names_cfg = {room["name"] for room in ROOMS_CONFIG}
        to_delete_name_set = names_db - names_cfg
        if to_delete_name_set:
            to_delete_rooms = session.scalars(
                select(Room).where(Room.name.in_(to_delete_name_set))
            ).all()
            for to_delete in to_delete_rooms:
                session.delete(to_delete)

        session.commit()
        return session.scalars(select(Room).order_by(Room.id)).all()
```

**処理の流れ:**
1. テーブルを作成（存在しない場合）
2. データベースにある会議室名を取得
3. `ROOMS_CONFIG`にあってDBにない部屋を追加
4. DBにあって`ROOMS_CONFIG`にない部屋を削除
5. 変更をコミット（確定）
6. すべての会議室をID順で返す

**初心者向けポイント:**
- この関数により、config.pyを変更するだけで会議室の追加・削除が可能
- データベースとconfig.pyが常に同期される

**実行例:**
```python
# アプリ起動時に実行
rooms = init_db()
print(f"{len(rooms)}個の会議室が登録されました")
```

### 8. get_rooms() - 全会議室取得関数

```python
def get_rooms() -> List[Room]:
    """全ての会議室を取得（id 昇順）"""
    with get_session() as session:
        return session.scalars(select(Room).order_by(Room.id)).all()
```

**説明:**
- すべての会議室をID順で取得
- AIServiceなどで会議室リストを表示する際に使用

## まとめ

### データベース構造
```
┌─────────────────┐
│     rooms       │
├─────────────────┤
│ id (PK)         │──┐
│ name (UNIQUE)   │  │
│ capacity        │  │
└─────────────────┘  │
                     │ 1対多
                     │
┌─────────────────┐  │
│  reservations   │  │
├─────────────────┤  │
│ id (PK)         │  │
│ room_id (FK)    │──┘
│ user_name       │
│ start_time      │
│ end_time        │
└─────────────────┘
```

### 主要な関数

| 関数名 | 説明 | 使用例 |
|-------|------|--------|
| get_session() | DBセッションを取得 | `with get_session() as session:` |
| init_db() | DBを初期化・同期 | アプリ起動時 |
| get_rooms() | 全会議室を取得 | AI応答時の会議室リスト表示 |

### 学習のポイント
- ORMを使うと、SQLを書かずにPythonだけでDB操作できる
- リレーションシップで、テーブル間の関係を定義できる
- バリデーションで、データの整合性を保証できる

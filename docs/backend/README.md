# バックエンド解説ドキュメント

## はじめに

このディレクトリには、会議室予約システムのバックエンド（サーバー側）の詳細な解説ドキュメントが含まれています。
初心者エンジニアでも理解できるように、各モジュールの役割、コードの詳細、使用例を丁寧に説明しています。

## システムアーキテクチャ

### 全体構成図

```
┌─────────────────────────────────────────────────────────────┐
│                       フロントエンド                          │
│                    (HTML/CSS/JavaScript)                    │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTP/JSON
                     ↓
┌─────────────────────────────────────────────────────────────┐
│                       Flask (app.py)                        │
│                     REST APIエンドポイント                    │
└─────┬───────────────┬───────────────┬──────────────────────┘
      │               │               │
      ↓               ↓               ↓
┌──────────┐  ┌──────────────┐  ┌──────────────┐
│ models.py│  │reservation_  │  │ ai_service.py│
│          │  │service.py    │  │              │
│ データベース│←─│              │←─│ AIチャット    │
│ モデル    │  │ ビジネス      │  │ 機能         │
│          │  │ ロジック      │  │              │
└──────────┘  └──────────────┘  └───┬──────────┘
      │                              │
      ↓                              ↓
┌──────────┐                   ┌──────────────┐
│ SQLite   │                   │ Redis        │
│ Database │                   │ (チャット履歴) │
└──────────┘                   └──────────────┘
                                      │
                                      ↓
                               ┌──────────────┐
                               │ OpenAI API   │
                               │ (GPT)        │
                               └──────────────┘
```

### レイヤー構成

```
┌─────────────────────────────────────────┐
│     Presentation Layer (API層)          │
│     - app.py (Flask)                    │
│     - ルーティング、リクエスト/レスポンス   │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────┴───────────────────────┐
│     Business Logic Layer (サービス層)    │
│     - reservation_service.py            │
│     - ai_service.py                     │
│     - ビジネスルール、処理フロー           │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────┴───────────────────────┐
│     Data Access Layer (データ層)         │
│     - models.py (ORM)                   │
│     - redis_service.py                  │
│     - データベース操作                    │
└─────────────────────────────────────────┘
```

## ドキュメント一覧

各ファイルの解説ドキュメントは、以下の順序で読むことをお勧めします。

### 1. 基本設定

| ファイル | 説明 | 難易度 |
|---------|------|-------|
| [01_config.md](01_config.md) | 設定ファイル（会議室、営業時間） | ★☆☆ |

**学べること:**
- 設定の外部化
- 定数の定義
- システム全体で使う値の管理

### 2. データベース

| ファイル | 説明 | 難易度 |
|---------|------|-------|
| [02_models.md](02_models.md) | データベースモデル（Room, Reservation） | ★★☆ |

**学べること:**
- ORM（SQLAlchemy）の基本
- テーブル定義とリレーション
- バリデーション
- データベース初期化

### 3. ユーティリティ

| ファイル | 説明 | 難易度 |
|---------|------|-------|
| [03_timezone_utils.md](03_timezone_utils.md) | タイムゾーン処理ユーティリティ | ★★☆ |
| [04_redis_service.md](04_redis_service.md) | Redisチャット履歴管理 | ★★☆ |

**学べること:**
- タイムゾーン処理（JST）
- 日時の変換・フォーマット
- 30分刻み処理
- Redisによるキャッシュ管理
- セッション管理

### 4. ビジネスロジック

| ファイル | 説明 | 難易度 |
|---------|------|-------|
| [05_reservation_service.md](05_reservation_service.md) | 予約ビジネスロジック | ★★★ |
| [06_ai_service.md](06_ai_service.md) | AIチャットボット | ★★★ |

**学べること:**
- ビジネスロジックの実装
- 重複チェック
- 空き部屋検索アルゴリズム
- Function Calling（OpenAI）
- 自然言語処理
- プロンプトエンジニアリング

### 5. Webアプリケーション

| ファイル | 説明 | 難易度 |
|---------|------|-------|
| [07_app.md](07_app.md) | Flaskアプリケーション（REST API） | ★★☆ |

**学べること:**
- Flask基本
- RESTful API設計
- ルーティング
- エラーハンドリング
- HTTPステータスコード

## 推奨学習パス

### 初心者向け（3日間コース）

**Day 1: 基礎理解**
1. config.py を読む（設定の理解）
2. models.py を読む（データベース基礎）
3. app.py を読む（REST API基礎）

**Day 2: ビジネスロジック**
1. timezone_utils.py を読む（日時処理）
2. reservation_service.py を読む（予約ロジック）

**Day 3: 応用機能**
1. redis_service.py を読む（キャッシュ）
2. ai_service.py を読む（AIチャット）

### 中級者向け（1日集中コース）

1. システムアーキテクチャを理解
2. 各ドキュメントを流し読み
3. 興味のある部分を深掘り
4. 実際にコードを動かしてみる

## 技術スタック

### バックエンドフレームワーク

| 技術 | バージョン | 用途 |
|-----|----------|------|
| Python | 3.13+ | プログラミング言語 |
| Flask | 3.1+ | Webフレームワーク |
| SQLAlchemy | 2.0+ | ORM（データベース操作） |

### データベース・キャッシュ

| 技術 | 用途 |
|-----|------|
| SQLite | 会議室・予約データ保存 |
| Redis | チャット履歴キャッシュ |

### AI・外部サービス

| 技術 | 用途 |
|-----|------|
| OpenAI API | AIチャットボット（GPT-3.5/GPT-4） |
| Azure OpenAI | OpenAIの代替（企業向け） |

### 主要ライブラリ

| ライブラリ | 用途 |
|-----------|------|
| python-dotenv | 環境変数管理 |
| redis-py | Redis操作 |
| openai | OpenAI API |
| requests | HTTPリクエスト |

## 主要な概念と用語

### 1. ORM（Object-Relational Mapping）
- SQLを書かずにPythonコードでデータベース操作
- `models.py`で使用

### 2. REST API
- HTTPメソッド（GET, POST, DELETE）でリソースを操作
- `app.py`で実装

### 3. Function Calling
- AIが必要に応じて関数を呼び出す仕組み
- `ai_service.py`で使用

### 4. ビジネスロジック
- 業務のルールを実装したコード
- `reservation_service.py`で実装

### 5. レイヤー分離
- プレゼンテーション層、ビジネスロジック層、データアクセス層を分離
- メンテナンス性向上

## データフロー例

### 予約作成の流れ

```
[ユーザー]
    │ 1. フォーム送信
    ↓
[フロントエンド]
    │ 2. POST /api/reservations
    ↓
[app.py]
    │ 3. JSONパース
    ↓
[ReservationService.create_reservation()]
    │ 4. バリデーション
    │ 5. 重複チェック
    │ 6. DB保存
    ↓
[models.Reservation]
    │ 7. SQLite INSERT
    ↓
[app.py]
    │ 8. JSON応答
    ↓
[フロントエンド]
    │ 9. UI更新
    ↓
[ユーザー]
    10. 成功メッセージ表示
```

### AIチャットの流れ

```
[ユーザー]
    │ 「今日の予約を教えて」
    ↓
[フロントエンド]
    │ POST /api/chat
    ↓
[app.py]
    ↓
[AIService.process_chat_message()]
    │ 1. 言語検出
    │ 2. チャット履歴取得（Redis）
    │ 3. システムプロンプト構築
    │ 4. OpenAI APIに送信
    ↓
[OpenAI API]
    │ 5. 意図解析
    │ 6. get_reservations関数を選択
    ↓
[AIService._execute_get_reservations()]
    ↓
[ReservationService.get_reservations_by_date()]
    ↓
[models.py]
    │ 7. DB検索
    ↓
[AIService]
    │ 8. 結果をOpenAIに再送信
    ↓
[OpenAI API]
    │ 9. 自然言語で整形
    ↓
[AIService]
    │ 10. チャット履歴に保存（Redis）
    ↓
[app.py]
    │ 11. JSON応答
    ↓
[フロントエンド]
    │ 12. チャット画面に表示
    ↓
[ユーザー]
    「本日の予約は...」を確認
```

## 環境変数

システムで使用する環境変数（.envファイル）:

```bash
# データベース
DATABASE_URL=sqlite:///meeting_rooms.db

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
CHAT_HISTORY_TTL=86400

# OpenAI
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-3.5-turbo

# または Azure OpenAI
AZURE_OPENAI_KEY=...
AZURE_OPENAI_ENDPOINT=https://...
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-35-turbo
```

## よくある質問（FAQ）

### Q1: なぜレイヤー分離が必要？
**A:** コードの保守性・再利用性・テスト容易性を向上させるため。例えば、API層を変更してもビジネスロジックは影響を受けません。

### Q2: なぜRedisを使う？
**A:** チャット履歴は高速アクセスが必要で、TTL（自動削除）機能が便利。SQLiteでも可能ですが、Redisの方が適しています。

### Q3: Function Callingとは何？
**A:** OpenAI APIの機能で、AIが必要に応じて関数を呼び出せる仕組み。これにより、データベース検索など実際のアクションを実行できます。

### Q4: なぜ30分刻み？
**A:** 会議室予約システムの一般的な慣習。時刻を統一することで、管理がしやすくなります。

### Q5: SQLAlchemyとは？
**A:** PythonのORM。SQLを書かずに、Pythonのクラスとメソッドでデータベース操作ができます。

## 次のステップ

1. **コードを読む**: 各ドキュメントを読みながら、実際のコードを確認
2. **動かしてみる**: システムを起動して、実際に動作を確認
3. **改造してみる**: 機能追加や変更にチャレンジ
   - 会議室を追加
   - 営業時間を変更
   - 新しいAPI追加
4. **テストを書く**: pytestなどでユニットテスト作成

## 参考資料

### 公式ドキュメント
- [Flask公式](https://flask.palletsprojects.com/)
- [SQLAlchemy公式](https://www.sqlalchemy.org/)
- [OpenAI API](https://platform.openai.com/docs/)
- [Redis公式](https://redis.io/)

### 学習リソース
- Flask入門: Flaskの基本を学ぶ
- SQLAlchemy入門: ORMの基礎
- REST API設計: APIの設計原則
- OpenAI Function Calling: AI連携の実装

## まとめ

このバックエンドシステムは、以下の特徴があります:

1. **モダンなアーキテクチャ**: レイヤー分離、REST API設計
2. **AI連携**: Function Callingによる自然言語インターフェース
3. **堅牢性**: バリデーション、エラーハンドリング、トランザクション管理
4. **拡張性**: モジュール化、設定の外部化
5. **学習に最適**: コードが読みやすく、コメントも充実

各ドキュメントを読むことで、バックエンド開発の基礎から応用まで、実践的に学べます。

頑張って学習してください！

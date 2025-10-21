# 会議室予約システム

## 概要

XW0会議室予約システムは、FlaskとOpenAI APIを使用したAI対話機能付きの会議室予約管理システムです。

## 特徴

- 🤖 **AIチャット機能**: 自然言語での予約・キャンセル・確認
- 📅 **リアルタイム予約管理**: 重複チェック機能付き
- 🎯 **Tool Calling**: AIが既存REST APIを直接呼び出し、LLMがレスポンスを生成
- 🎨 **予約色分け表示**: 自分の予約は緑色、他人の予約は黄色で一目で区別可能
- 📆 **コンパクトカレンダー**: 日付選択で予約表が自動更新
- ⚡ **即座の予約反映**: AIチャットからの予約が即座に予約表に表示
- 🇯🇵 **日本語対応**: IME入力問題を解決した快適なUI
- 🌏 **多言語対応**: 日本語・英語自動検出
- 📱 **レスポンシブデザイン**: Bootstrap 5使用

## システム構成

```
zerobase_AI/
├── app.py                 # Flaskメインアプリケーション
├── ai_service.py          # OpenAI API統合サービス
├── reservation_service.py # 予約管理ビジネスロジック
├── redis_service.py       # Redisチャット履歴管理サービス
├── models.py              # データベースモデル
├── timezone_utils.py      # タイムゾーン処理ユーティリティ
├── config.py              # 会議室設定・営業時間設定
├── requirements.txt       # Python依存関係
├── .env                   # 環境変数設定
├── templates/
│   └── index.html         # メインUI
├── static/
│   ├── css/
│   │   ├── chat.css           # チャット機能スタイル
│   │   ├── calendar.css       # カレンダースタイル
│   │   └── reservation.css    # 予約表スタイル（色分け）
│   └── js/
│       ├── main.js            # メイン JavaScript（エントリーポイント）
│       ├── chat.js            # AIチャット機能
│       ├── calendar.js        # コンパクトカレンダー機能
│       ├── api.js             # API通信モジュール
│       ├── formUI.js          # フォームUI操作
│       ├── timezone.js        # フロントエンド用JST処理
│       ├── reservationTable.js # 予約表管理
│       └── config.js          # 設定定数
├── docs/
│   ├── README.md          # プロジェクト概要
│   ├── TECHNICAL_DOCS.md  # 技術仕様書
│   └── DEPLOYMENT.md      # デプロイメント・運用ガイド
└── README.md              # メインドキュメント
```

## 必要な依存関係

```txt
Flask==2.3.3
python-dotenv==1.0.0
requests==2.31.0
SQLAlchemy==2.0.32
openai>=1.50.0
redis==5.0.1
```

## 外部サービス

- **OpenAI API**: AI対話機能（またはAzure OpenAI）
- **Redis**: チャット履歴管理（セッション毎、TTL: 24時間）

## 環境設定

### 1. Redisサーバーの起動（Docker推奨）

```bash
# Dockerを使ってRedisサーバーを起動
docker run -d \
  --name meeting-redis \
  -p 6379:6379 \
  redis:7-alpine

# Redisの動作確認
docker exec -it meeting-redis redis-cli ping
# => PONG が返ってくればOK
```

### 2. 環境変数設定 (.env)

```bash
# データベース
DATABASE_URL=sqlite:///meeting_rooms.db

# OpenAI API（どちらか一方を設定）
OPENAI_API_KEY=your_openai_api_key_here

# または Azure OpenAI
AZURE_OPENAI_KEY=your_azure_key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_DEPLOYMENT_NAME=your-gpt-35-turbo-deployment

# Redis設定
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
CHAT_HISTORY_TTL=86400  # チャット履歴保持期間（秒）
```

### 3. インストール

```bash
# 仮想環境作成
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存関係インストール
pip install -r requirements.txt
```

### 4. データベース初期化

```bash
python models.py
```

## 起動方法

```bash
# 1. Redisサーバーが起動していることを確認
docker ps | grep meeting-redis

# 2. Flaskアプリケーションを起動
python app.py
```

アプリケーションは http://127.0.0.1:5000 で起動します。

## API エンドポイント

### 予約管理 API

- `POST /api/reservations` - 新規予約作成
- `GET /api/reservations/<date>` - 指定日の予約一覧取得
- `DELETE /api/reservations/<id>` - 予約キャンセル

### AIチャット API

- `POST /api/chat` - AI対話処理（セッションID必須）

## AIチャット機能

### セッション管理

- **セッションID**: クライアント側で生成（UUID）
- **チャット履歴**: Redisに保存（セッション毎）
- **文脈保持**: 同一セッション内で過去の会話を参照
- **有効期限**: デフォルト24時間（設定可能）

### Tool Calling対応

AIが以下の操作を自動実行できます：

1. **予約作成** (`create_reservation`)
   - 会議室ID、日付、開始時刻、終了時刻を解析
   - REST API `/api/reservations` を呼び出し
   - **LLMが結果を自然な文章で返答**

2. **空き部屋検索** (`find_available_rooms`)
   - 指定日時と利用時間で空き部屋を検索
   - **LLMが検索結果を分かりやすく提示**

3. **予約確認** (`get_reservations`)
   - 指定日付を解析
   - REST API `/api/reservations/<date>` を呼び出し
   - **LLMが予約状況を整形して表示**

4. **自分の予約確認** (`get_my_reservations`)
   - 現在のユーザーの予約のみ取得
   - **LLMが自分の予約を分かりやすく提示**

5. **予約キャンセル** (`cancel_reservation`)
   - 予約IDを解析
   - REST API `/api/reservations/<id>` を呼び出し
   - **LLMがキャンセル結果を通知**

### Tool Calling → LLM Response フロー

```
1. ユーザー入力 → AIが意図を解析
2. Tool Calling実行 → 実際のAPI呼び出し
3. Tool実行結果をLLMに送信
4. LLMが結果を元に自然な応答を生成
5. ユーザーにフレンドリーなメッセージとして返答
```

### 使用例

```
ユーザー: "明日14時から会議室Aを1時間予約してください"
AI: 予約が完了しました！Room Aを2025-10-22 14:00から15:00まで予約しました。

ユーザー: "今日の予約状況を教えてください"
AI: 2025-10-21の予約状況:
- Room A 14:00~15:00 (userA)
- Room B 10:00~11:30 (userB)

ユーザー: "I want to book a room tomorrow at 2 PM"
AI: Reservation completed! Room A has been booked from 14:00 to 15:00 on 2025-10-22.
```

### 多言語対応

- **自動言語検出**: ユーザーのメッセージ言語を自動判定
- **日本語**: 日本語で入力すると日本語で応答
- **英語**: 英語で入力すると英語で応答

## UIの特徴

### 日本語入力対応

- **compositionstart/end** イベントでIME状態を監視
- 変換確定のEnterでは送信されない
- Shift+Enterで改行対応

### コンパクトカレンダー

- **月移動**: 前月/次月ボタンで簡単に移動
- **日付選択**: クリックで日付を選択 → 予約表が自動更新
- **今日の強調**: 今日の日付は青色で表示
- **選択中の強調**: 選択中の日付は緑色で表示

### 予約表の色分け

- **自分の予約**: 緑色（`table-success`）で表示、太字で強調
- **他人の予約**: 黄色（`table-warning`）で表示
- **即座の判別**: 一目で自分の予約が分かる

### AIチャットからの予約反映

- **即座の更新**: AIチャットで予約するとすぐに予約表に反映
- **カレンダー自動移動**: 予約日が異なる場合、カレンダーが自動的に移動
- **リアルタイム表示**: 予約完了と同時に緑色セルで表示

### ユーザビリティ

- リアルタイムボタン状態管理（入力有無で送信ボタン有効/無効）
- キーボードショートカット対応（Enter送信、Shift+Enter改行）
- アクセシビリティ対応（ARIA属性、セマンティックHTML）
- レスポンシブデザイン（モバイル・タブレット対応）

## 会議室設定

`config.py` で会議室と営業時間を設定：

```python
ROOMS_CONFIG = [
    {"name": "Room A", "capacity": 4},
    {"name": "Room B", "capacity": 6},
    {"name": "Room C", "capacity": 15},
    {"name": "Room D", "capacity": 20},
]

# 予約できる時間の範囲
STARTHOUR = 7   # 7時から
ENDHOUR = 22    # 22時まで
```

## データベーススキーマ

### Room (会議室)
- `id`: 主キー
- `name`: 会議室名（ユニーク）
- `capacity`: 定員

### Reservation (予約)
- `id`: 主キー
- `room_id`: 会議室ID (外部キー)
- `user_name`: ユーザー名
- `start_time`: 開始時刻（JST、datetime型）
- `end_time`: 終了時刻（JST、datetime型）

## タイムゾーン対応

### JST統一実装済み

システム全体でJST（日本標準時）に統一されています：

1. **バックエンド**: `timezone_utils.py` でJST処理を統一
2. **フロントエンド**: `timezone.js` でJST時刻取得・表示
3. **データベース**: JSTタイムゾーン付きdatetimeで保存

### 主要機能

- **自動JST変換**: UTC時刻をJSTに自動変換
- **統一表示**: 全ての時刻表示がJST基準
- **日付処理**: 今日・明日の判定がJST基準
- **30分刻み**: 予約時刻は必ず30分刻み（00分または30分）

## トラブルシューティング

### よくある問題

1. **OpenAI API エラー**
   - `.env` ファイルでAPIキーを確認
   - API利用制限の確認

2. **データベースエラー**
   - `python models.py` でDB再初期化

3. **Redis接続エラー**
   - `docker ps` でRedisコンテナ起動確認
   - `docker exec -it meeting-redis redis-cli ping` で接続確認

4. **日本語入力問題**
   - ブラウザのJavaScript有効化を確認
   - モダンブラウザの使用を推奨（Chrome, Firefox, Edge最新版）

5. **予約が表示されない**
   - ブラウザコンソールでJavaScriptエラー確認
   - カレンダーで正しい日付を選択しているか確認

## 開発者向け情報

### コード品質

- エラーハンドリング実装済み
- Tool Calling による既存API活用
- LLMによる柔軟なレスポンス生成
- モジュラー設計でメンテナンス性向上

### アーキテクチャの特徴

- **バックエンド**: Tool実行 → JSONデータをLLMに送信 → LLMが応答生成
- **フロントエンド**: モジュール化されたES6 JavaScript
- **リアルタイム連携**: カレンダー ⇔ 予約表 ⇔ フォーム ⇔ AIチャット

### 拡張性

- 新しいToolを追加するだけでAI機能自動拡張
- 会議室設定の動的変更対応
- 多言語対応準備済み（日本語・英語実装済み）

## ライセンス

このプロジェクトは開発用途での使用を想定しています。

## 更新履歴

### v1.4.0 (2025-10-21)
- **Tool Calling結果のLLM処理**: toolの実行結果をLLMに送り、自然な応答を生成
- **予約色分け機能**: 自分の予約（緑色）と他人の予約（黄色）を区別
- **即座の予約反映**: AIチャットからの予約が即座に予約表に反映
- **コンパクトカレンダー**: 日付選択で予約表が自動更新される機能追加
- **多言語自動対応**: 日本語・英語を自動検出して応答
- **空き部屋検索機能**: 指定時刻・時間で利用可能な部屋を検索
- **自分の予約確認機能**: ユーザー自身の予約のみを取得

### v1.3.1 (2025-10-05)
- OpenAI 2.x対応完了（1.12.0 → 2.1.0）
- Tool Calling API更新（functions → tools）
- chat.jsのセッションID送信キー修正（session_id → sessionId）
- Redis接続パラメータ処理改善

### v1.3.0 (2025-10-05)
- Redisによるチャット履歴管理機能追加
- セッション毎の文脈保持機能実装
- redis_service.pyモジュール追加
- Docker Redisセットアップ手順追加

### v1.2.0 (2025-09-28)
- JST統一タイムゾーン対応実装
- 予約フォーム・AIチャット双方のエラーハンドリング強化
- フロントエンド・バックエンド全体でのタイムゾーン統一

### v1.1.0 (2025-09-28)
- 日本語入力IME対応改善（compositionstart/end対応）
- 予約表の自動更新機能修正
- HTTPステータスコード処理強化

### v1.0.0 (2025-09-28)
- 初回リリース
- AIチャット機能実装
- Function Calling対応
- 日本語入力UI改善

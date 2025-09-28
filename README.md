# 会議室予約システム

## 概要

XW0会議室予約システムは、FlaskとOpenAI APIを使用したAI対話機能付きの会議室予約管理システムです。

## 特徴

- 🤖 **AIチャット機能**: 自然言語での予約・キャンセル・確認
- 📅 **リアルタイム予約管理**: 重複チェック機能付き
- 🎯 **Function Calling**: AIが既存REST APIを直接呼び出し
- 🇯🇵 **日本語対応**: IME入力問題を解決した快適なUI
- 📱 **レスポンシブデザイン**: Bootstrap 5使用

## システム構成

```
zerobase_AI/
├── app.py                 # Flaskメインアプリケーション
├── ai_service.py          # OpenAI API統合サービス
├── reservation_service.py # 予約管理ビジネスロジック
├── models.py              # データベースモデル
├── timezone_utils.py      # タイムゾーン処理ユーティリティ
├── requirements.txt       # Python依存関係
├── .env                   # 環境変数設定
├── config/
│   └── rooms.py          # 会議室設定
├── templates/
│   └── index.html        # メインUI
├── static/
│   └── js/
│       ├── main.js       # メイン JavaScript
│       ├── chat.js       # AIチャット機能
│       ├── api.js        # API通信
│       ├── ui.js         # UI操作
│       ├── timezone.js   # フロントエンド用タイムゾーン処理
│       ├── bookingTable.js # 予約表管理
│       └── config.js     # 設定定数
├── README.md             # プロジェクト概要
├── TECHNICAL_DOCS.md     # 技術仕様書
└── DEPLOYMENT.md         # デプロイメント・運用ガイド
```

## 必要な依存関係

```txt
Flask==2.3.3
python-dotenv==1.0.0
requests==2.31.0
SQLAlchemy==2.0.32
openai==1.109.1
```

## 環境設定

### 1. 環境変数設定 (.env)

```bash
DATABASE_URL=sqlite:///meeting_rooms.db
OPENAI_API_KEY=your_openai_api_key_here
```

### 2. インストール

```bash
# 仮想環境作成
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存関係インストール
pip install -r requirements.txt
```

### 3. データベース初期化

```bash
python models.py
```

## 起動方法

```bash
python app.py
```

アプリケーションは http://127.0.0.1:5000 で起動します。

## API エンドポイント

### 予約管理 API

- `POST /api/reserve` - 新規予約作成
- `GET /api/reservations/<date>` - 指定日の予約一覧取得
- `DELETE /api/reservations/<id>` - 予約キャンセル

### AIチャット API

- `POST /api/chat` - AI対話処理

## AIチャット機能

### Function Calling対応

AIが以下の操作を自動実行できます：

1. **予約作成** (`create_reservation`)
   - 会議室ID、日付、開始時刻、終了時刻を解析
   - REST API `/api/reserve` を呼び出し

2. **予約確認** (`get_reservations`)
   - 指定日付を解析
   - REST API `/api/reservations/<date>` を呼び出し

3. **予約キャンセル** (`cancel_reservation`)
   - 予約IDを解析
   - REST API `/api/reservations/<id>` を呼び出し

### 使用例

```
ユーザー: "明日14時から会議室Aを1時間予約してください"
AI: 予約が完了しました！会議室Aを2025-09-29 14:00から15:00まで予約しました。

ユーザー: "明日の予約状況を教えてください"
AI: 2025-09-29の予約状況:
- 会議室A 14:00~15:00 (guest)
```

## UIの特徴

### 日本語入力対応

- **compositionstart/end** イベントでIME状態を監視
- 変換確定のEnterでは送信されない
- Shift+Enterで改行対応

### ユーザビリティ

- リアルタイム文字数カウンター (0/500)
- 段階的警告表示 (400文字でオレンジ、480文字で赤)
- キーボードショートカットヒント表示
- アクセシビリティ対応

## 会議室設定

`config/rooms.py` で会議室を設定：

```python
ROOMS_CONFIG = [
    {"name": "会議室A", "capacity": 4},
    {"name": "会議室B", "capacity": 6},
    {"name": "会議室C", "capacity": 15},
    {"name": "会議室D", "capacity": 20},
]
```

## データベーススキーマ

### Room (会議室)
- `id`: 主キー
- `name`: 会議室名
- `capacity`: 定員

### Reservation (予約)
- `id`: 主キー
- `room_id`: 会議室ID (外部キー)
- `user_name`: ユーザー名
- `start_time`: 開始時刻
- `end_time`: 終了時刻

## Azure OpenAI への移行

### 必要な環境変数変更

```bash
# OpenAI API用
OPENAI_API_KEY=sk-proj-xxx

# Azure OpenAI用
AZURE_OPENAI_KEY=your_azure_key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_DEPLOYMENT_NAME=your-gpt-35-turbo-deployment
```

### コード変更箇所

`ai_service.py` の初期化部分：

```python
# OpenAI → Azure OpenAI
from openai import AzureOpenAI

self.client = AzureOpenAI(
    azure_endpoint=azure_endpoint,
    api_key=azure_key,
    api_version=api_version
)

# モデル名をデプロイメント名に変更
model=self.deployment_name  # "gpt-3.5-turbo" → デプロイメント名
```

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

## トラブルシューティング

### よくある問題

1. **OpenAI API エラー**
   - `.env` ファイルでAPIキーを確認
   - API利用制限の確認

2. **データベースエラー**
   - `python models.py` でDB再初期化

3. **日本語入力問題**
   - ブラウザのJavaScript有効化を確認
   - モダンブラウザの使用を推奨

## 開発者向け情報

### コード品質

- エラーハンドリング実装済み
- Function Calling による既存API活用
- モジュラー設計でメンテナンス性向上

### 拡張性

- 新しいAPIエンドポイント追加でAI機能自動拡張
- 会議室設定の動的変更対応
- 多言語対応準備済み

## ライセンス

このプロジェクトは開発用途での使用を想定しています。

## 更新履歴

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
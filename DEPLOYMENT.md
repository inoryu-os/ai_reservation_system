# デプロイメント・運用ガイド

## 本番環境デプロイ

### 環境要件

#### 最小要件
- Python 3.8+
- メモリ: 512MB以上
- ストレージ: 1GB以上
- OS: Linux/Windows/macOS

#### 推奨環境
- Python 3.11+
- メモリ: 2GB以上
- ストレージ: 10GB以上
- OS: Ubuntu 22.04 LTS

### 本番環境設定

#### 1. システム準備

```bash
# Ubuntu の場合
sudo apt update
sudo apt install python3 python3-pip python3-venv nginx

# Python仮想環境作成
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 2. 環境変数設定

```bash
# 本番用 .env
DATABASE_URL=postgresql://user:password@localhost/meeting_rooms
OPENAI_API_KEY=your_production_api_key
FLASK_ENV=production
SECRET_KEY=your_secret_key_here
TZ=Asia/Tokyo  # JST タイムゾーン設定
```

#### 3. WSGI サーバー設定 (Gunicorn)

```bash
# requirements.txt に追加
echo "gunicorn==21.2.0" >> requirements.txt
echo "psycopg2-binary==2.9.7" >> requirements.txt
pip install gunicorn

# Gunicorn設定ファイル (gunicorn.conf.py)
cat > gunicorn.conf.py << EOF
bind = "127.0.0.1:8000"
workers = 4
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2
max_requests = 1000
max_requests_jitter = 100
preload_app = True
EOF
```

#### 4. Systemd サービス設定

```bash
# /etc/systemd/system/meeting-room.service
sudo tee /etc/systemd/system/meeting-room.service << EOF
[Unit]
Description=Meeting Room Reservation System
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/meeting-room
Environment=PATH=/var/www/meeting-room/venv/bin
Environment=TZ=Asia/Tokyo
ExecStart=/var/www/meeting-room/venv/bin/gunicorn --config gunicorn.conf.py app:app
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# サービス有効化
sudo systemctl daemon-reload
sudo systemctl enable meeting-room
sudo systemctl start meeting-room
```

#### 5. Nginx リバースプロキシ設定

```nginx
# /etc/nginx/sites-available/meeting-room
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /var/www/meeting-room/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}

# サイト有効化
sudo ln -s /etc/nginx/sites-available/meeting-room /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### SSL/TLS 設定 (Let's Encrypt)

```bash
# Certbot インストール
sudo apt install certbot python3-certbot-nginx

# SSL証明書取得
sudo certbot --nginx -d your-domain.com

# 自動更新設定確認
sudo systemctl status certbot.timer
```

## データベース設定

### PostgreSQL セットアップ

```bash
# PostgreSQL インストール
sudo apt install postgresql postgresql-contrib

# データベース作成
sudo -u postgres createdb meeting_rooms
sudo -u postgres createuser meeting_user
sudo -u postgres psql -c "ALTER USER meeting_user WITH PASSWORD 'secure_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE meeting_rooms TO meeting_user;"

# Python PostgreSQL ドライバ
pip install psycopg2-binary
```

### データベース移行

```python
# models.py を PostgreSQL用に調整
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://meeting_user:secure_password@localhost/meeting_rooms')
```

## 監視・ログ設定

### ログ設定

```python
# app.py にログ設定追加
import logging
from logging.handlers import RotatingFileHandler

if not app.debug:
    file_handler = RotatingFileHandler('logs/app.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('Meeting Room System startup')
```

### システム監視

```bash
# ヘルスチェックエンドポイント追加
# app.py
@app.route('/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.2.0',
        'timezone': 'JST'
    })
```

## バックアップ戦略

### データベースバックアップ

```bash
# 日次バックアップスクリプト (backup.sh)
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/var/backups/meeting-room"
DB_NAME="meeting_rooms"

mkdir -p $BACKUP_DIR

# PostgreSQL バックアップ
pg_dump -h localhost -U meeting_user $DB_NAME > $BACKUP_DIR/db_backup_$DATE.sql

# 古いバックアップ削除 (30日より古い)
find $BACKUP_DIR -name "db_backup_*.sql" -mtime +30 -delete

# crontab設定
# 0 2 * * * /path/to/backup.sh
```

### ファイルバックアップ

```bash
# アプリケーションファイルバックアップ
tar -czf "/var/backups/meeting-room/app_backup_$(date +%Y%m%d).tar.gz" \
    -C /var/www/meeting-room \
    --exclude=venv \
    --exclude=__pycache__ \
    --exclude=*.pyc \
    .
```

## セキュリティ設定

### ファイアウォール設定

```bash
# UFW設定
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw status
```

### アプリケーションセキュリティ

```python
# app.py セキュリティヘッダー
from flask_talisman import Talisman

# HTTPS強制、CSP設定
Talisman(app, force_https=True)

# セッション設定
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
```

## 運用手順

### 定期メンテナンス

#### 週次タスク
```bash
# ログローテーション確認
sudo logrotate -f /etc/logrotate.d/nginx
sudo logrotate -f /etc/logrotate.d/meeting-room

# システム更新
sudo apt update && sudo apt upgrade -y

# SSL証明書確認
sudo certbot certificates
```

#### 月次タスク
```bash
# データベース最適化
sudo -u postgres psql meeting_rooms -c "VACUUM ANALYZE;"

# バックアップ確認
ls -la /var/backups/meeting-room/

# ディスク使用量確認
df -h
du -sh /var/www/meeting-room
```

### アプリケーション更新

```bash
# 更新手順
cd /var/www/meeting-room

# バックアップ作成
sudo systemctl stop meeting-room
cp -r . ../meeting-room-backup-$(date +%Y%m%d)

# 新しいコードデプロイ
git pull origin main  # または新しいファイルコピー

# 依存関係更新
source venv/bin/activate
pip install -r requirements.txt

# データベース移行（必要に応じて）
python models.py

# サービス再起動
sudo systemctl start meeting-room
sudo systemctl status meeting-room

# 動作確認
curl http://localhost:8000/health
```

## トラブルシューティング

### よくある問題と解決法

#### 1. アプリケーションが起動しない

```bash
# ログ確認
sudo journalctl -u meeting-room -f

# プロセス確認
ps aux | grep gunicorn

# ポート確認
sudo netstat -tlnp | grep 8000
```

#### 2. データベース接続エラー

```bash
# PostgreSQL 状態確認
sudo systemctl status postgresql

# 接続テスト
sudo -u postgres psql meeting_rooms -c "SELECT 1;"

# 設定確認
cat /etc/postgresql/*/main/pg_hba.conf
```

#### 3. OpenAI API エラー

```bash
# API キー確認
grep OPENAI_API_KEY /var/www/meeting-room/.env

# ネットワーク確認
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
     https://api.openai.com/v1/models

# ログ確認
tail -f /var/www/meeting-room/logs/app.log
```

#### 4. 高負荷時の対応

```bash
# CPU・メモリ確認
top
htop

# Gunicorn ワーカー数調整
# gunicorn.conf.py
workers = cpu_count * 2 + 1

# サービス再起動
sudo systemctl restart meeting-room
```

## 性能監視

### メトリクス収集

```python
# app.py に追加
import time
from functools import wraps

def monitor_performance(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = time.time()
        result = f(*args, **kwargs)
        end_time = time.time()
        app.logger.info(f'{f.__name__} took {end_time - start_time:.2f} seconds')
        return result
    return decorated_function

@app.route('/api/chat', methods=['POST'])
@monitor_performance
def chat_with_ai():
    # 既存のコード
```

### パフォーマンスアラート

```bash
# CPU使用率監視スクリプト (monitor.sh)
#!/bin/bash
CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
if (( $(echo "$CPU_USAGE > 80" | bc -l) )); then
    echo "High CPU usage: $CPU_USAGE%" | mail -s "Server Alert" admin@company.com
fi
```

## 災害復旧

### 復旧手順

#### 1. データベース復旧

```bash
# バックアップからの復元
sudo -u postgres dropdb meeting_rooms
sudo -u postgres createdb meeting_rooms
sudo -u postgres psql meeting_rooms < /var/backups/meeting-room/db_backup_YYYYMMDD.sql
```

#### 2. アプリケーション復旧

```bash
# バックアップからの復元
sudo systemctl stop meeting-room
rm -rf /var/www/meeting-room
cp -r /var/backups/meeting-room/app_backup_YYYYMMDD /var/www/meeting-room
sudo systemctl start meeting-room
```

#### 3. 動作確認

```bash
# ヘルスチェック
curl http://localhost:8000/health

# AIチャット機能テスト
curl -X POST http://localhost:8000/api/chat \
     -H "Content-Type: application/json" \
     -d '{"message": "今日の予約状況を教えてください"}'

# 予約APIテスト
curl -X POST http://localhost:8000/api/reservations \
     -H "Content-Type: application/json" \
     -d '{"room-id": "1", "date": "2025-09-29", "start-time": "14:00", "end-time": "15:00"}'
```

## 連絡先

### 緊急時連絡先
- システム管理者: admin@company.com
- 開発チーム: dev@company.com

### サポートリソース
- システムログ: `/var/log/nginx/`, `/var/www/meeting-room/logs/`
- 監視ダッシュボード: (設定に応じて)
- ドキュメント: `/var/www/meeting-room/README.md`
import os
import json
import redis
from typing import List, Dict, Optional

class RedisService:
    """Redisを使ったチャット履歴管理サービス"""

    def __init__(self):
        """Redis接続の初期化"""
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

    def _get_key(self, session_id: str) -> str:
        """セッションIDからRedisキーを生成"""
        return f"chat_history:{session_id}"

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

    def clear_history(self, session_id: str) -> None:
        """
        セッションのチャット履歴をクリア

        Args:
            session_id: セッションID
        """
        key = self._get_key(session_id)
        self.client.delete(key)

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

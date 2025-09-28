"""
タイムゾーン処理のユーティリティ
"""

import os
from datetime import datetime, timezone, timedelta
from typing import Optional

# JSTタイムゾーンを定義
JST = timezone(timedelta(hours=9))

def get_jst_now() -> datetime:
    """現在のJST時刻を取得"""
    return datetime.now(JST)

def parse_date_jst(date_str: str) -> datetime:
    """日付文字列(YYYY-MM-DD)をJSTのdatetimeに変換"""
    return datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=JST)

def parse_datetime_jst(date_str: str, time_str: str) -> datetime:
    """日付文字列と時刻文字列をJSTのdatetimeに変換"""
    datetime_str = f"{date_str} {time_str}"
    return datetime.strptime(datetime_str, "%Y-%m-%d %H:%M").replace(tzinfo=JST)

def format_jst_date(dt: datetime) -> str:
    """JSTのdatetimeを日付文字列(YYYY-MM-DD)に変換"""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=JST)
    return dt.strftime("%Y-%m-%d")

def format_jst_time(dt: datetime) -> str:
    """JSTのdatetimeを時刻文字列(HH:MM)に変換"""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=JST)
    return dt.strftime("%H:%M")

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

def setup_timezone():
    """アプリケーション全体のタイムゾーンをJSTに設定"""
    os.environ['TZ'] = 'Asia/Tokyo'

    # Pythonのtimeモジュールに反映
    try:
        import time
        time.tzset()
    except AttributeError:
        # Windows環境では tzset が利用できない場合がある
        pass
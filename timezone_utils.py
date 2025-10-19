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

def round_down_to_30min(dt: datetime) -> datetime:
    """
    時刻を30分刻みで切り下げ

    例:
        14:04 → 14:00
        14:35 → 14:30
        14:00 → 14:00
        14:30 → 14:30

    Args:
        dt: 対象のdatetime

    Returns:
        30分刻みに切り下げられたdatetime
    """
    minutes = dt.minute
    rounded_minutes = (minutes // 30) * 30  # 0 or 30
    return dt.replace(minute=rounded_minutes, second=0, microsecond=0)

def get_next_30min_slot(dt: datetime) -> datetime:
    """
    次の30分区切りを取得

    例:
        14:04 → 14:30
        14:30 → 15:00
        14:00 → 14:30
        14:35 → 15:00

    Args:
        dt: 対象のdatetime

    Returns:
        次の30分区切りのdatetime
    """
    rounded_down = round_down_to_30min(dt)
    return rounded_down + timedelta(minutes=30)

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

    Args:
        current_time: 現在時刻
        duration_minutes: 利用時間（分）

    Returns:
        (start_time, end_time) のタプル (HH:MM形式の文字列)
    """
    start_dt = round_down_to_30min(current_time)
    next_slot_dt = get_next_30min_slot(current_time)
    end_dt = next_slot_dt + timedelta(minutes=duration_minutes)

    return (format_jst_time(start_dt), format_jst_time(end_dt))
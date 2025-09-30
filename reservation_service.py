"""
予約関連のビジネスロジックを担当するサービスクラス
"""

from datetime import datetime, timedelta, time
from typing import List, Optional, Dict, Any
from sqlalchemy import select, and_, exists
from sqlalchemy.orm import selectinload
import models
from timezone_utils import JST, parse_datetime_jst, format_jst_date, format_jst_time, get_jst_now, convert_to_jst
from config import STARTHOUR, ENDHOUR


class ReservationService:
    """予約管理サービス"""

    @staticmethod
    def create_reservation(room_id: int, user_name: str, date: str,
                         start_time: str, end_time: str) -> Dict[str, Any]:
        """
        予約を作成する

        Args:
            room_id: 会議室ID
            user_name: ユーザー名
            date: 日付 (YYYY-MM-DD)
            start_time: 開始時刻 (HH:MM)
            end_time: 終了時刻 (HH:MM)

        Returns:
            作成結果とデータ
        """
        try:
            # 入力検証
            validation_result = ReservationService._validate_reservation_data(
                room_id, date, start_time, end_time
            )
            if not validation_result["valid"]:
                return {"success": False, "error": validation_result["error"]}

            # 日時変換（JSTで処理）
            start_datetime = parse_datetime_jst(date, start_time)
            end_datetime = parse_datetime_jst(date, end_time)

            # 重複チェックと予約作成
            with models.get_session() as session:
                if ReservationService._check_conflict(session, room_id, start_datetime, end_datetime):
                    return {"success": False, "error": "指定された時間帯は既に予約されています"}

                reservation = models.Reservation(
                    room_id=room_id,
                    user_name=user_name,
                    start_time=start_datetime,
                    end_time=end_datetime
                )

                session.add(reservation)
                session.commit()

                room = session.get(models.Room, room_id)

                return {
                    "success": True,
                    "message": "予約が完了しました",
                    "reservation": {
                        "id": reservation.id,
                        "room_name": room.name if room else "Unknown",
                        "room_id": room_id,
                        "date": date,
                        "start_time": start_time,
                        "end_time": end_time,
                        "user_name": user_name
                    }
                }

        except ValueError:
            return {"success": False, "error": "日時の形式が正しくありません"}
        except Exception as e:
            return {"success": False, "error": f"サーバーエラーが発生しました: {str(e)}"}

    @staticmethod
    def get_reservations_by_date(date: str) -> Dict[str, Any]:
        """
        指定日の予約一覧を取得する

        Args:
            date: 日付 (YYYY-MM-DD)

        Returns:
            取得結果とデータ
        """
        try:
            # JSTで日付処理
            target_date_jst = parse_datetime_jst(date, "00:00")
            next_day_jst = target_date_jst + timedelta(days=1)

            with models.get_session() as session:
                stmt = select(models.Reservation).join(models.Room).where(
                    models.Reservation.start_time >= target_date_jst,
                    models.Reservation.start_time < next_day_jst
                )
                reservations = session.scalars(stmt).all()

                result = []
                for reservation in reservations:
                    # データベースから取得した時刻をJSTに変換して表示
                    start_time_jst = convert_to_jst(reservation.start_time)
                    end_time_jst = convert_to_jst(reservation.end_time)

                    result.append({
                        "id": reservation.id,
                        "room_id": reservation.room_id,
                        "room_name": reservation.room.name,
                        "user_name": reservation.user_name,
                        "start_time": format_jst_time(start_time_jst),
                        "end_time": format_jst_time(end_time_jst),
                        "date": date
                    })

                return {"success": True, "reservations": result}

        except ValueError:
            return {"success": False, "error": "日付の形式が正しくありません"}
        except Exception as e:
            return {"success": False, "error": f"サーバーエラーが発生しました: {str(e)}"}
        
    @staticmethod
    def get_reservations_by_username(user_name: str) -> Dict[str, Any]:
        """
        指定されたユーザー名の予約一覧を取得する

        Args:
            user_name: ユーザー名

        Returns:
            取得結果とデータ
        """
        try:
            with models.get_session() as session:
                reservations = session.scalars(
                    select(models.Reservation)
                    .where(models.Reservation.user_name == user_name)
                    .options(selectinload(models.Reservation.room))
                    .order_by(models.Reservation.start_time)
                ).all()

                result = []
                for reservation in reservations:
                    # データベースから取得した時刻をJSTに変換して表示
                    start_time_jst = convert_to_jst(reservation.start_time)
                    end_time_jst = convert_to_jst(reservation.end_time)

                    result.append({
                        "id": reservation.id,
                        "room_id": reservation.room_id,
                        "room_name": reservation.room.name,
                        "user_name": reservation.user_name,
                        "start_time": format_jst_time(start_time_jst),
                        "end_time": format_jst_time(end_time_jst),
                        "date": format_jst_date(start_time_jst)
                    })

                return {"success": True, "reservations": result}

        except ValueError as e:
            return {"success": False, "error": f"値エラー:{e}"}
        except Exception as e:
            return {"success": False, "error": f"サーバーエラーが発生しました: {str(e)}"}
        
    @staticmethod
    def find_available_rooms_by_start_datetime_and_duration(date: str, start_time: str, duration_minutes: int) -> List[Dict[str, Any]]:
        """
        指定した開始日時と利用時間で空いている部屋の情報を返す。

        Args:
            date: 日付
            start_time: 開始時刻
            duration_minutes: 利用時間(分)
        Returns:
            利用可能な部屋の名前とidを持つリスト
        """
        # 入力検証
        if duration_minutes <= 0:
            raise ValueError("利用時間は0分より大きくなければなりません")

        try:
            start_datetime = parse_datetime_jst(date, start_time)
        except Exception:
            raise ValueError("開始日時の形式が正しくありません")

        end_datetime = start_datetime + timedelta(minutes=duration_minutes)

        # 営業時間チェック（開始は営業開始以降、終了は営業終了以前／同時は不可）
        if start_datetime.time() < time(STARTHOUR,0) or end_datetime.time() > time(ENDHOUR,0):
            raise ValueError("開始時刻もしくは終了時刻が業務時間外です")
        if not (end_datetime > start_datetime):
            raise ValueError("終了時刻は開始時刻より後に設定してください")

        # 重複のない部屋を検索
        with models.get_session() as session:
            overlap = and_(
                models.Reservation.room_id == models.Room.id,
                models.Reservation.start_time < end_datetime,
                models.Reservation.end_time > start_datetime,
            )

            subq = select(models.Reservation.id).where(overlap)
            stmt = (
                select(models.Room)
                .where(~exists(subq).correlate(models.Room))
                .order_by(models.Room.id)
            )

            rooms = session.scalars(stmt).all()

            return [{"id": room.id, "name": room.name} for room in rooms]


    @staticmethod
    def cancel_reservation(reservation_id: int) -> Dict[str, Any]:
        """
        予約をキャンセルする

        Args:
            reservation_id: 予約ID

        Returns:
            キャンセル結果
        """
        try:
            with models.get_session() as session:
                reservation = session.scalars(
                    select(models.Reservation).where(models.Reservation.id == reservation_id)
                ).first()

                if not reservation:
                    return {"success": False, "error": "予約が見つかりません"}

                session.delete(reservation)
                session.commit()

                return {
                    "success": True,
                    "message": "予約をキャンセルしました",
                    "reservation_id": reservation_id
                }

        except Exception as e:
            return {"success": False, "error": f"サーバーエラーが発生しました: {str(e)}"}

    @staticmethod
    def _validate_reservation_data(room_id: int, date: str, start_time: str, end_time: str) -> Dict[str, Any]:
        """予約データの基本検証(引数が揃っているか、開始時刻および終了時刻が勤務可能時間内か、開始時刻が終了時刻よりも後か)"""
        if not all([room_id, date, start_time, end_time]):
            return {"valid": False, "error": "必須項目が不足しています"}
        
        start_time = datetime.strptime(start_time, "%H:%M").time()
        end_time = datetime.strptime(end_time, "%H:%M").time() 

        earliest = time(STARTHOUR,0)
        latest = time(ENDHOUR, 0)

        if start_time < earliest or end_time > latest:
            return {"valid": False, "error": "7時から22時の間で予約してください"}
        
        if start_time >= end_time:
            return {"valid": False, "error": "終了時刻は開始時刻より後に設定してください"}
         

        return {"valid": True}




    @staticmethod
    def _check_conflict(session, room_id: int, new_start_time: datetime, new_end_time: datetime) -> bool:
        """時間重複をチェック"""
        existing = session.scalars(
            select(models.Reservation).where(
                models.Reservation.room_id == room_id,
                models.Reservation.start_time < new_end_time,
                models.Reservation.end_time > new_start_time
            )
        ).first()

        return existing is not None

"""
予約関連のビジネスロジックを担当するサービスクラス
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import models


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

            # 日時変換
            start_datetime = datetime.strptime(f"{date} {start_time}", "%Y-%m-%d %H:%M")
            end_datetime = datetime.strptime(f"{date} {end_time}", "%Y-%m-%d %H:%M")

            # 時間の妥当性チェック
            if start_datetime >= end_datetime:
                return {"success": False, "error": "終了時刻は開始時刻より後に設定してください"}

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

                room = session.query(models.Room).filter(models.Room.id == room_id).first()

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
            target_date = datetime.strptime(date, "%Y-%m-%d").date()

            with models.get_session() as session:
                reservations = session.query(models.Reservation).join(models.Room).filter(
                    models.Reservation.start_time >= datetime.combine(target_date, datetime.min.time()),
                    models.Reservation.start_time < datetime.combine(target_date, datetime.min.time()) + timedelta(days=1)
                ).all()

                result = []
                for reservation in reservations:
                    result.append({
                        "id": reservation.id,
                        "room_id": reservation.room_id,
                        "room_name": reservation.room.name,
                        "user_name": reservation.user_name,
                        "start_time": reservation.start_time.strftime("%H:%M"),
                        "end_time": reservation.end_time.strftime("%H:%M"),
                        "date": date
                    })

                return {"success": True, "reservations": result}

        except ValueError:
            return {"success": False, "error": "日付の形式が正しくありません"}
        except Exception as e:
            return {"success": False, "error": f"サーバーエラーが発生しました: {str(e)}"}

    @staticmethod
    def cancel_reservation(reservation_id: int, user_name: str) -> Dict[str, Any]:
        """
        予約をキャンセルする

        Args:
            reservation_id: 予約ID
            user_name: ユーザー名（権限確認用）

        Returns:
            キャンセル結果
        """
        try:
            with models.get_session() as session:
                reservation = session.query(models.Reservation).filter(
                    models.Reservation.id == reservation_id
                ).first()

                if not reservation:
                    return {"success": False, "error": "予約が見つかりません"}

                if reservation.user_name != user_name:
                    return {"success": False, "error": "他のユーザーの予約はキャンセルできません"}

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
        """予約データの基本検証"""
        if not all([room_id, date, start_time, end_time]):
            return {"valid": False, "error": "必須項目が不足しています"}

        return {"valid": True}

    @staticmethod
    def _check_conflict(session, room_id: int, start_datetime: datetime, end_datetime: datetime) -> bool:
        """時間重複をチェック"""
        existing = session.query(models.Reservation).filter(
            models.Reservation.room_id == room_id,
            models.Reservation.start_time < end_datetime,
            models.Reservation.end_time > start_datetime
        ).first()

        return existing is not None
"""
予約関連のルート定義
"""

from flask import Blueprint, request, jsonify
from services.reservation_service import ReservationService

# 予約関連のBlueprint
reservation_bp = Blueprint('reservation', __name__)

# グローバルユーザー名（実際のアプリでは認証システムから取得）
USER_NAME = "guest"


@reservation_bp.route('/api/reserve', methods=['POST'])
def create_reservation():
    """予約作成API"""
    data = request.get_json(silent=True) or {}

    room_id = data.get("room-id")
    date = data.get("date")
    start_time = data.get("start-time")
    end_time = data.get("end-time")

    result = ReservationService.create_reservation(
        room_id=int(room_id) if room_id else None,
        user_name=USER_NAME,
        date=date,
        start_time=start_time,
        end_time=end_time
    )

    if result["success"]:
        return jsonify(result)
    else:
        status_code = 400 if "必須項目" in result["error"] or "形式" in result["error"] else 409
        if "見つかりません" in result["error"]:
            status_code = 404
        return jsonify(result), status_code


@reservation_bp.route('/api/reservations/<date>', methods=['GET'])
def get_reservations_by_date(date):
    """指定日の予約一覧取得API"""
    result = ReservationService.get_reservations_by_date(date)

    if result["success"]:
        return jsonify(result)
    else:
        status_code = 400 if "形式" in result["error"] else 500
        return jsonify(result), status_code


@reservation_bp.route('/api/reservations/<int:reservation_id>', methods=['DELETE'])
def cancel_reservation(reservation_id):
    """予約キャンセルAPI"""
    result = ReservationService.cancel_reservation(reservation_id, USER_NAME)

    if result["success"]:
        return jsonify(result)
    else:
        status_code = 404 if "見つかりません" in result["error"] else 403
        if "他のユーザー" in result["error"]:
            status_code = 403
        elif "サーバーエラー" in result["error"]:
            status_code = 500
        return jsonify(result), status_code
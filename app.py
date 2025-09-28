from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

load_dotenv()

# タイムゾーンをJSTに設定
from timezone_utils import setup_timezone
setup_timezone()

import models
from reservation_service import ReservationService
from ai_service import AIService

app = Flask(__name__)

user_name = "guest"

@app.route('/')
def index():
    rooms = models.init_db()
    return render_template('index.html', rooms=rooms, user_name=user_name)

@app.route('/api/reservations', methods=['POST'])
def create_reservation():
    """予約作成API"""
    data = request.get_json(silent=False)

    room_id = data.get("room-id")
    date = data.get("date")
    start_time = data.get("start-time")
    end_time = data.get("end-time")
    result = ReservationService.create_reservation(
        room_id=int(room_id) if room_id else None,
        user_name=user_name,
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


@app.route('/api/reservations/<date>', methods=['GET'])
def get_reservations_by_date(date):
    """指定日の予約一覧取得API"""
    result = ReservationService.get_reservations_by_date(date)

    if result["success"]:
        return jsonify(result)
    else:
        status_code = 400 if "形式" in result["error"] else 500
        return jsonify(result), status_code


@app.route('/api/reservations/<int:reservation_id>', methods=['DELETE'])
def cancel_reservation(reservation_id):
    """予約キャンセルAPI"""
    result = ReservationService.cancel_reservation(reservation_id)

    if result["success"]:
        return jsonify(result)
    else:
        status_code = 404 if "見つかりません" in result["error"] else 403
        if "他のユーザー" in result["error"]:
            status_code = 403
        elif "サーバーエラー" in result["error"]:
            status_code = 500
        return jsonify(result), status_code


@app.route('/api/chat', methods=['POST'])
def chat_with_ai():
    """AIチャットAPI"""
    try:
        data = request.get_json()
        message = data.get('message', '').strip()

        if not message:
            return jsonify({
                'success': False,
                'error': 'メッセージが入力されていません'
            }), 400

        ai_service = AIService()
        result = ai_service.process_chat_message(message, user_name)

        return jsonify(result)

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'チャット処理エラー: {str(e)}',
            'response': '申し訳ありませんが、システムエラーが発生しました。'
        }), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)
"""
デモ用の予約データを作成するスクリプト
2025-10-24の予約表にサンプルデータを登録
"""
from datetime import datetime
from models import get_session, Room, Reservation
from sqlalchemy import select

def create_demo_reservations():
    """2025-10-24のデモ用予約を作成"""
    session = get_session()

    try:
        # 会議室を取得
        rooms = session.scalars(select(Room).order_by(Room.id)).all()
        if not rooms:
            print("エラー: 会議室が見つかりません。先に models.py を実行してください。")
            return

        print(f"会議室: {[r.name for r in rooms]}")

        # 2025-10-24の既存予約を削除
        target_date = "2025-10-24"
        existing = session.scalars(
            select(Reservation).where(
                Reservation.start_time >= datetime.strptime(f"{target_date} 00:00", "%Y-%m-%d %H:%M"),
                Reservation.start_time < datetime.strptime(f"{target_date} 23:59", "%Y-%m-%d %H:%M")
            )
        ).all()

        for r in existing:
            session.delete(r)
        session.commit()
        print(f"既存の予約 {len(existing)} 件を削除しました。")

        # 実際のRoom IDを取得（動的に対応）
        room_map = {room.name: room.id for room in rooms}

        # デモ用予約データ（いい感じに分散）
        demo_reservations = [
            # Room A - 中程度に埋まる
            {"room_name": "Room A", "user_name": "userA", "start": "09:00", "end": "10:30"},
            {"room_name": "Room A", "user_name": "userB", "start": "11:00", "end": "12:00"},
            {"room_name": "Room A", "user_name": "userC", "start": "14:00", "end": "15:30"},
            {"room_name": "Room A", "user_name": "userA", "start": "16:00", "end": "17:00"},

            # Room B - 比較的空いている
            {"room_name": "Room B", "user_name": "userB", "start": "10:00", "end": "11:00"},
            {"room_name": "Room B", "user_name": "userD", "start": "13:00", "end": "14:30"},
            {"room_name": "Room B", "user_name": "userA", "start": "18:00", "end": "19:00"},

            # Room C - よく使われている
            {"room_name": "Room C", "user_name": "userC", "start": "08:00", "end": "09:00"},
            {"room_name": "Room C", "user_name": "userA", "start": "09:30", "end": "11:00"},
            {"room_name": "Room C", "user_name": "userB", "start": "11:30", "end": "13:00"},
            {"room_name": "Room C", "user_name": "userD", "start": "14:00", "end": "16:00"},
            {"room_name": "Room C", "user_name": "userC", "start": "16:30", "end": "18:00"},

            # Room D - 大部屋、長時間利用
            {"room_name": "Room D", "user_name": "userA", "start": "10:00", "end": "12:00"},
            {"room_name": "Room D", "user_name": "userB", "start": "13:00", "end": "15:30"},
            {"room_name": "Room D", "user_name": "userC", "start": "16:00", "end": "18:30"},
        ]

        # 予約を作成
        created_count = 0
        for res_data in demo_reservations:
            # room_nameからroom_idを取得
            room_name = res_data["room_name"]
            if room_name not in room_map:
                print(f"警告: Room '{room_name}' が見つかりません。スキップします。")
                continue

            room_id = room_map[room_name]
            room = session.get(Room, room_id)

            start_dt = datetime.strptime(f"{target_date} {res_data['start']}", "%Y-%m-%d %H:%M")
            end_dt = datetime.strptime(f"{target_date} {res_data['end']}", "%Y-%m-%d %H:%M")

            reservation = Reservation(
                room_id=room_id,
                user_name=res_data["user_name"],
                start_time=start_dt,
                end_time=end_dt
            )
            session.add(reservation)
            created_count += 1
            print(f"作成: {room.name} - {res_data['user_name']} ({res_data['start']}~{res_data['end']})")

        session.commit()
        print(f"\n✅ デモ用予約 {created_count} 件を作成しました！")
        print(f"日付: {target_date}")
        print("\nユーザー別予約数:")
        for user in ["userA", "userB", "userC", "userD"]:
            count = len([r for r in demo_reservations if r["user_name"] == user])
            print(f"  {user}: {count}件")

    except Exception as e:
        session.rollback()
        print(f"エラー: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    create_demo_reservations()

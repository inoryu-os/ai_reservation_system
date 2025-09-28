import os
import json
import re
import requests
from datetime import datetime, timedelta
from openai import OpenAI
from reservation_service import ReservationService
import models

class AIService:
    def __init__(self):
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY is not set in environment variables")

        self.client = OpenAI(api_key=api_key)
        self.base_url = "http://127.0.0.1:5000"

    def process_chat_message(self, message, user_name="guest"):
        """
        ユーザーのチャットメッセージを処理し、Function Callingで既存APIを呼び出し
        """
        try:
            # 会議室情報を取得
            rooms = models.get_rooms()
            room_info = "\n".join([f"- {room.name} (ID: {room.id}, 定員: {room.capacity}名)" for room in rooms])

            # 現在の日時
            now = datetime.now()
            today = now.strftime("%Y-%m-%d")

            # Function Callingの定義
            functions = [
                {
                    "name": "create_reservation",
                    "description": "会議室の予約を作成する",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "room_id": {
                                "type": "integer",
                                "description": "会議室ID"
                            },
                            "date": {
                                "type": "string",
                                "description": "予約日 (YYYY-MM-DD形式)"
                            },
                            "start_time": {
                                "type": "string",
                                "description": "開始時刻 (HH:MM形式)"
                            },
                            "end_time": {
                                "type": "string",
                                "description": "終了時刻 (HH:MM形式)"
                            }
                        },
                        "required": ["room_id", "date", "start_time", "end_time"]
                    }
                },
                {
                    "name": "get_reservations",
                    "description": "指定日の予約一覧を取得する",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "date": {
                                "type": "string",
                                "description": "予約を確認する日付 (YYYY-MM-DD形式)"
                            }
                        },
                        "required": ["date"]
                    }
                },
                {
                    "name": "cancel_reservation",
                    "description": "予約をキャンセルする",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "reservation_id": {
                                "type": "integer",
                                "description": "キャンセルする予約のID"
                            }
                        },
                        "required": ["reservation_id"]
                    }
                }
            ]

            # システムプロンプト
            system_prompt = f"""
あなたは会議室予約システムのAIアシスタントです。
ユーザーのメッセージを解析して、適切な関数を呼び出して予約関連の操作を実行してください。

利用可能な会議室:
{room_info}

現在の日時: {now.strftime("%Y年%m月%d日 %H:%M")}

日時の解析ルール:
- 「明日」= {(now + timedelta(days=1)).strftime("%Y-%m-%d")}
- 「今日」= {today}
- 時間は24時間形式で解析してください
- 期間が指定されない場合は1時間としてください

ユーザーが予約、キャンセル、確認を求めた場合は、適切な関数を呼び出してください。
"""

            # OpenAI APIに送信
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                functions=functions,
                function_call="auto",
                temperature=0.1
            )

            # Function Callingの処理
            if response.choices[0].message.function_call:
                function_name = response.choices[0].message.function_call.name
                function_args = json.loads(response.choices[0].message.function_call.arguments)

                if function_name == "create_reservation":
                    return self._call_create_reservation_api(function_args, user_name)
                elif function_name == "get_reservations":
                    return self._call_get_reservations_api(function_args)
                elif function_name == "cancel_reservation":
                    return self._call_cancel_reservation_api(function_args, user_name)

            # 通常の応答
            return {
                "success": True,
                "response": response.choices[0].message.content,
                "action": "info"
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"AIサービスエラー: {str(e)}",
                "response": "申し訳ありませんが、システムエラーが発生しました。"
            }

    def _call_create_reservation_api(self, args, user_name):
        """REST APIを呼び出して予約を作成"""
        try:
            url = f"{self.base_url}/api/reserve"
            data = {
                "room-id": str(args["room_id"]),
                "date": args["date"],
                "start-time": args["start_time"],
                "end-time": args["end_time"]
            }

            response = requests.post(url, json=data, headers={"Content-Type": "application/json"})
            result = response.json()

            if response.status_code == 200 and result.get("success"):
                return {
                    "success": True,
                    "response": f"予約が完了しました！{result['reservation']['room_name']}を{args['date']} {args['start_time']}から{args['end_time']}まで予約しました。",
                    "action": "reserve",
                    "reservation": result["reservation"]
                }
            else:
                return {
                    "success": True,
                    "response": f"予約できませんでした: {result.get('error', '不明なエラー')}",
                    "action": "reserve"
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "response": "予約処理中にエラーが発生しました。"
            }

    def _call_get_reservations_api(self, args):
        """REST APIを呼び出して予約一覧を取得"""
        try:
            url = f"{self.base_url}/api/reservations/{args['date']}"
            response = requests.get(url)
            result = response.json()

            if response.status_code == 200 and result.get("success"):
                reservations = result["reservations"]
                if reservations:
                    reservation_list = "\n".join([
                        f"- {r['room_name']} {r['start_time']}~{r['end_time']} ({r['user_name']})"
                        for r in reservations
                    ])
                    return {
                        "success": True,
                        "response": f"{args['date']}の予約状況:\n{reservation_list}",
                        "action": "check"
                    }
                else:
                    return {
                        "success": True,
                        "response": f"{args['date']}には予約がありません。",
                        "action": "check"
                    }
            else:
                return {
                    "success": True,
                    "response": "予約状況の確認中にエラーが発生しました。",
                    "action": "check"
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "response": "確認処理中にエラーが発生しました。"
            }

    def _call_cancel_reservation_api(self, args, user_name):
        """REST APIを呼び出して予約をキャンセル"""
        try:
            url = f"{self.base_url}/api/reservations/{args['reservation_id']}"
            response = requests.delete(url)
            result = response.json()

            if response.status_code == 200 and result.get("success"):
                return {
                    "success": True,
                    "response": "予約をキャンセルしました。",
                    "action": "cancel"
                }
            else:
                return {
                    "success": True,
                    "response": f"キャンセルできませんでした: {result.get('error', '不明なエラー')}",
                    "action": "cancel"
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "response": "キャンセル処理中にエラーが発生しました。"
            }

    def _handle_reservation(self, parsed_response, user_name):
        """予約作成処理"""
        try:
            data = parsed_response.get("data", {})

            # 必要なデータが揃っているかチェック
            required_fields = ["room_id", "date", "start_time", "end_time"]
            missing_fields = [field for field in required_fields if not data.get(field)]

            if missing_fields:
                return {
                    "success": True,
                    "response": f"予約に必要な情報が不足しています: {', '.join(missing_fields)}。もう一度詳しく教えてください。",
                    "action": "reserve"
                }

            # 予約作成
            result = ReservationService.create_reservation(
                room_id=data["room_id"],
                user_name=user_name,
                date=data["date"],
                start_time=data["start_time"],
                end_time=data["end_time"]
            )

            if result["success"]:
                return {
                    "success": True,
                    "response": f"予約が完了しました！{parsed_response['response']}",
                    "action": "reserve",
                    "reservation": result["reservation"]
                }
            else:
                return {
                    "success": True,
                    "response": f"予約できませんでした: {result['error']}",
                    "action": "reserve"
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "response": "予約処理中にエラーが発生しました。"
            }

    def _handle_cancellation(self, parsed_response, user_name):
        """キャンセル処理"""
        try:
            data = parsed_response.get("data", {})
            reservation_id = data.get("reservation_id")

            if not reservation_id:
                # 予約IDが指定されていない場合、今日の予約一覧を表示
                today = datetime.now().strftime("%Y-%m-%d")
                result = ReservationService.get_reservations_by_date(today)

                if result["success"] and result["reservations"]:
                    user_reservations = [r for r in result["reservations"] if r["user_name"] == user_name]
                    if user_reservations:
                        reservation_list = "\n".join([
                            f"ID: {r['id']} - {r['room_name']} {r['start_time']}~{r['end_time']}"
                            for r in user_reservations
                        ])
                        return {
                            "success": True,
                            "response": f"あなたの予約一覧:\n{reservation_list}\n\nキャンセルしたい予約のIDを教えてください。",
                            "action": "cancel"
                        }
                    else:
                        return {
                            "success": True,
                            "response": "今日のあなたの予約はありません。",
                            "action": "cancel"
                        }
                else:
                    return {
                        "success": True,
                        "response": "予約の確認中にエラーが発生しました。",
                        "action": "cancel"
                    }

            # キャンセル実行
            result = ReservationService.cancel_reservation(reservation_id, user_name)

            if result["success"]:
                return {
                    "success": True,
                    "response": f"予約をキャンセルしました。{parsed_response['response']}",
                    "action": "cancel"
                }
            else:
                return {
                    "success": True,
                    "response": f"キャンセルできませんでした: {result['error']}",
                    "action": "cancel"
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "response": "キャンセル処理中にエラーが発生しました。"
            }

    def _handle_check(self, parsed_response):
        """予約確認処理"""
        try:
            data = parsed_response.get("data", {})
            date = data.get("date", datetime.now().strftime("%Y-%m-%d"))

            result = ReservationService.get_reservations_by_date(date)

            if result["success"]:
                reservations = result["reservations"]
                if reservations:
                    reservation_list = "\n".join([
                        f"{r['room_name']} {r['start_time']}~{r['end_time']} ({r['user_name']})"
                        for r in reservations
                    ])
                    return {
                        "success": True,
                        "response": f"{date}の予約状況:\n{reservation_list}",
                        "action": "check"
                    }
                else:
                    return {
                        "success": True,
                        "response": f"{date}には予約がありません。",
                        "action": "check"
                    }
            else:
                return {
                    "success": True,
                    "response": "予約状況の確認中にエラーが発生しました。",
                    "action": "check"
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "response": "確認処理中にエラーが発生しました。"
            }
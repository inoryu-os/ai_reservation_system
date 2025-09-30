import os
import json
import requests
from datetime import datetime, timedelta
from openai import OpenAI, AzureOpenAI
from reservation_service import ReservationService
import models
from timezone_utils import get_jst_now, format_jst_date

class AIService:
    def __init__(self):
        # OpenAI or Azure OpenAI を環境変数で自動切り替え
        azure_key = os.getenv("AZURE_OPENAI_KEY")
        azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        azure_api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
        azure_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")

        if azure_key and azure_endpoint:
            # Azure OpenAI クライアント
            self.client = AzureOpenAI(
                api_key=azure_key,
                azure_endpoint=azure_endpoint,
                api_version=azure_api_version,
            )
            # Azure では model にはデプロイメント名を指定
            if not azure_deployment:
                raise ValueError("AZURE_OPENAI_DEPLOYMENT_NAME is required when using Azure OpenAI")
            self.model = azure_deployment
        else:
            # OpenAI クライアント
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                raise ValueError("OPENAI_API_KEY is not set in environment variables")
            self.client = OpenAI(api_key=api_key)
            # 既存挙動を維持（必要ならモデルは環境変数で上書き可）
            self.model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

        self.base_url = "http://127.0.0.1:5000"

    def process_chat_message(self, message, user_name="guest"):
        """
        ユーザーのチャットメッセージを処理し、Function Callingで既存APIを呼び出し
        """
        try:
            # 会議室情報を取得
            rooms = models.get_rooms()
            room_info = "\n".join([f"- {room.name} (ID: {room.id}, 定員: {room.capacity}名)" for room in rooms])

            # 現在の日時（JST）
            now = get_jst_now()
            today = format_jst_date(now)

            # Tools（関数ツール）の定義（最新の推奨インターフェース）
            tools = [
                {
                    "type": "function",
                    "function": {
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
                    }
                },
                {
                    "type": "function",
                    "function": {
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
                    }
                },
                {
                    "type": "function",
                    "function": {
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
                }
            ]

            # システムプロンプト
            system_prompt = f"""
あなたは会議室予約システムのAIアシスタントです。
ユーザーのメッセージを解析して、適切な関数を呼び出して予約関連の操作を実行してください。

利用可能な会議室:
{room_info}

現在の日時: {now.strftime("%Y年%m月%d日 %H:%M")} (JST)

日時の解析ルール:
- 「明日」= {format_jst_date(now + timedelta(days=1))}
- 「今日」= {today}
- 時間は24時間形式で解析してください
- 期間が指定されない場合は1時間としてください

ユーザーが予約、キャンセル、確認を求めた場合は、適切な関数を呼び出してください。
"""

            # OpenAI/Azure OpenAI APIに送信（tools を使用）
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                tools=tools,
                tool_choice="auto",
                temperature=0.1
            )

            # Tools 呼び出しの処理
            msg = response.choices[0].message
            tool_calls = getattr(msg, "tool_calls", None)
            if tool_calls:
                # 今回は最初の tool_call を処理
                call = tool_calls[0]
                if call.get("type") == "function":
                    fn = call["function"]["name"]
                    args_json = call["function"].get("arguments") or "{}"
                    try:
                        fn_args = json.loads(args_json)
                    except Exception:
                        fn_args = {}

                    if fn == "create_reservation":
                        return self._call_create_reservation_api(fn_args)
                    elif fn == "get_reservations":
                        return self._call_get_reservations_api(fn_args)
                    elif fn == "cancel_reservation":
                        return self._call_cancel_reservation_api(fn_args)

            # 通常の応答
            return {
                "success": True,
                "response": msg.content,
                "action": "info"
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"AIサービスエラー: {str(e)}",
                "response": "申し訳ありませんが、システムエラーが発生しました。"
            }

    def _call_create_reservation_api(self, args):
        """REST APIを呼び出して予約を作成し、LLMに結果を返す"""
        url = f"{self.base_url}/api/reservations"
        data = {
            "room-id": str(args["room_id"]),
            "date": args["date"],
            "start-time": args["start_time"],
            "end-time": args["end_time"]
        }
        try:
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

    def _call_cancel_reservation_api(self, args):
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
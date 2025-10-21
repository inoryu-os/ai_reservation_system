import os
import json
import requests
from datetime import datetime, timedelta
from openai import OpenAI, AzureOpenAI
from reservation_service import ReservationService
import models
from timezone_utils import get_jst_now, format_jst_date, format_jst_time, round_down_to_30min, get_next_30min_slot, calculate_reservation_time_for_now
from redis_service import RedisService

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
        self.redis_service = RedisService()

    def _detect_language(self, text: str) -> str:
        """
        テキストの言語を検出（日本語 or 英語）

        Args:
            text: 検出対象のテキスト

        Returns:
            "ja" または "en"
        """
        # 日本語文字（ひらがな、カタカナ、漢字）が含まれているか確認
        japanese_chars = sum(1 for char in text if '\u3040' <= char <= '\u30ff' or '\u4e00' <= char <= '\u9fff')

        # 日本語文字が3文字以上含まれていれば日本語と判定
        if japanese_chars >= 3:
            return "ja"
        else:
            return "en"

    def process_chat_message(self, message, user_name="guest", session_id=None):
        """
        ユーザーのチャットメッセージを処理し、Function Callingで既存APIを呼び出し
        """
        try:
            # ユーザーのメッセージ言語を検出
            user_language = self._detect_language(message)
            # 会議室情報を取得
            rooms = models.get_rooms()
            room_info = "\n".join([f"- {room.name} (ID: {room.id}, 定員: {room.capacity}名)" for room in rooms])

            # 現在の日時（JST）
            now = get_jst_now()
            today = format_jst_date(now)

            # 「今から」予約用の時刻情報（30分刻み）
            rounded_start = round_down_to_30min(now)
            next_slot = get_next_30min_slot(now)
            rounded_start_str = format_jst_time(rounded_start)
            next_slot_str = format_jst_time(next_slot)

            # Tools（関数ツール）の定義（最新の推奨インターフェース）
            tools = [
                {
                    "type": "function",
                    "function": {
                        "name": "create_reservation",
                        "description": "会議室の予約を作成する。ユーザーから受け取った部屋名を利用可能な会議室リストから検索してroom_idに変換してください。",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "room_id": {
                                    "type": "integer",
                                    "description": "会議室ID。ユーザーが指定した部屋名から該当するIDを見つけて設定してください。"
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
                        "name": "find_available_rooms",
                        "description": "指定の開始時刻と利用時間で空いている会議室を検索する。ユーザーが部屋を指定せずに予約したい場合は必ずこの関数を最初に呼び出してください。",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "date": {"type": "string", "description": "予約日 (YYYY-MM-DD形式)"},
                                "start_time": {"type": "string", "description": "開始時刻 (HH:MM形式、例: 14:00)"},
                                "duration_minutes": {"type": "integer", "description": "利用時間（分単位、例: 60分=1時間）"}
                            },
                            "required": ["date", "start_time", "duration_minutes"]
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
                },
                {
                    "type": "function",
                    "function": {
                        "name": "get_my_reservations",
                        "description": "ユーザー自身の予約一覧を取得する。「今日の予約」「私の予約」「自分の予約」などのフレーズで呼び出す。",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "date": {
                                    "type": "string",
                                    "description": "予約を確認する日付 (YYYY-MM-DD形式、省略時は全期間)"
                                }
                            },
                            "required": []
                        }
                    }
                }
            ]

            # システムプロンプト
            system_prompt = f"""
あなたは会議室予約システムのAIアシスタントです。
ユーザーのメッセージを解析して、適切な関数を呼び出して予約関連の操作を実行してください。

現在のユーザー名: {user_name}

利用可能な会議室（名前とID）:
{room_info}

現在の日時: {now.strftime("%Y年%m月%d日 %H:%M")} (JST)
予約可能な開始時刻: {rounded_start_str} (現在時刻を30分刻みで切り下げた時刻)
次の30分区切り: {next_slot_str}

日時の解析ルール:
- 「明日」= {format_jst_date(now + timedelta(days=1))}
- 「今日」= {today}
- 時間は24時間形式で解析してください
- 期間が指定されない場合は1時間としてください

予約時刻の重要なルール:
- **予約時刻は必ず30分刻み（00分または30分）にしてください**
- 「今から」「今すぐ」などのフレーズが使われた場合は、以下の時刻で予約してください:
  * 開始時刻: {rounded_start_str}
  * 終了時刻: {next_slot_str}の30分後 + さらに利用時間を加算

  **具体例で理解してください:**
  現在が{now.strftime("%H:%M")}の場合、

  「今から30分利用したい」→ start_time: "{rounded_start_str}", end_time: 以下を計算
    {next_slot_str} (直後の区切り) の30分後 = {format_jst_time(next_slot + timedelta(minutes=30))}
    ↑これが終了時刻

  「今から60分利用したい」→ start_time: "{rounded_start_str}", end_time: 以下を計算
    {next_slot_str} (直後の区切り) の60分後 = {format_jst_time(next_slot + timedelta(minutes=60))}
    ↑これが終了時刻

- 具体的な時刻が指定された場合も、必ず30分刻みの時刻（例: 14:00, 14:30, 15:00）を使用してください

予約処理のフロー（必ず以下の順序で実行）:
1. ユーザーが会議室を指定していない場合:
   - 必ずfind_available_rooms関数で空き部屋を検索してください
   - 検索結果をユーザーに提示してください
   - ユーザーが部屋を選択してから予約を実行してください

2. ユーザーが会議室名を指定している場合:
   - 上記の「利用可能な会議室」リストから部屋名に対応するIDを見つけてください
   - 見つけたroom_idを使ってcreate_reservation関数を呼び出してください
   - 例: ユーザーが「会議室A」と言った場合、リストから「会議室A (ID: 1)」を見つけて、room_id=1で予約

3. 予約確認:
   - 「今日の予約」「私の予約」「自分の予約」などのフレーズ → get_my_reservations関数を使用（現在のユーザーの予約のみ）
   - 特定の日付の全体の予約状況を確認 → get_reservations関数を使用（全ユーザーの予約）

4. 予約キャンセル:
   - cancel_reservation関数で予約をキャンセル

重要なルール:
- **ユーザーが英語でメッセージを送った場合は、英語で応答してください**
- **ユーザーが日本語でメッセージを送った場合は、日本語で応答してください**
- ユーザーとのやり取りは常に「部屋名」を使用してください
- 関数呼び出し時は必ず「部屋ID」に変換してください
- 部屋名からIDへの変換は上記の会議室リストを参照してください
- 部屋名が曖昧な場合は、部分一致で検索してください（例: 「A」→「会議室A」）
- ユーザーが「自分の予約」を確認したい場合は必ずget_my_reservations関数を使用してください

関数実行後のレスポンス形式:
- **create_reservation成功時**: 「予約が完了しました！[部屋名]を[日付] [開始時刻]から[終了時刻]まで予約しました。」(英語の場合: "Reservation completed! [room_name] has been booked from [start_time] to [end_time] on [date].")
- **create_reservation失敗時**: 「予約できませんでした: [エラー理由]」(英語の場合: "Reservation failed: [error_reason]")
- **find_available_rooms結果あり**: 「空いている部屋:\n- [部屋名]\n...\n予約する部屋名を教えてください。例えば『[部屋名]』のように返信してください。」(英語の場合: "Available rooms:\n- [room_name]\n...\nPlease tell me which room you'd like to book. For example, reply with '[room_name]'.")
- **find_available_rooms結果なし**: 「指定の時間帯で空いている部屋はありません。」(英語の場合: "No rooms are available for the specified time.")
- **get_reservations/get_my_reservations結果あり**: 「[日付]の予約状況:\n- [部屋名] [開始時刻]~[終了時刻] ([ユーザー名])」の形式でリスト表示
- **get_reservations/get_my_reservations結果なし**: 「[日付]には予約がありません。」または「あなたの予約はありません。」
- **cancel_reservation成功時**: 「予約をキャンセルしました。」(英語の場合: "Reservation cancelled successfully.")
- **cancel_reservation失敗時**: 「キャンセルできませんでした: [エラー理由]」

常にフレンドリーで丁寧な口調で応答してください。
"""

            # チャット履歴を取得（セッションIDがある場合）
            messages = [{"role": "system", "content": system_prompt}]

            if session_id:
                # 過去のチャット履歴を取得
                history = self.redis_service.get_history(session_id)
                messages.extend(history)

            # 現在のユーザーメッセージを追加
            messages.append({"role": "user", "content": message})

            # OpenAI/Azure OpenAI APIに送信（tools を使用）
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=tools,
                tool_choice="auto",
                temperature=0.1
            )

            # Tools 呼び出しの処理
            msg = response.choices[0].message
            tool_calls = getattr(msg, "tool_calls", None)

            # ユーザーメッセージを履歴に保存
            if session_id:
                self.redis_service.add_message(session_id, "user", message)

            if tool_calls:
                # アシスタントのメッセージ（tool_calls含む）を履歴に追加
                messages.append({
                    "role": "assistant",
                    "content": msg.content,
                    "tool_calls": [
                        {
                            "id": call.id,
                            "type": call.type,
                            "function": {
                                "name": call.function.name,
                                "arguments": call.function.arguments
                            }
                        } for call in tool_calls
                    ]
                })

                # 各tool_callの結果を取得してmessagesに追加
                # 最初のtool呼び出しの結果を保持（レスポンスに含めるため）
                first_tool_result = None
                first_function_name = None

                for call in tool_calls:
                    if call.type == "function":
                        fn = call.function.name
                        args_json = call.function.arguments or "{}"
                        try:
                            fn_args = json.loads(args_json)
                        except Exception:
                            fn_args = {}

                        # 実際の関数を呼び出し
                        tool_result = None
                        if fn == "create_reservation":
                            tool_result = self._execute_create_reservation(fn_args)
                        elif fn == "find_available_rooms":
                            tool_result = self._execute_find_available_rooms(fn_args)
                        elif fn == "get_reservations":
                            tool_result = self._execute_get_reservations(fn_args)
                        elif fn == "get_my_reservations":
                            tool_result = self._execute_get_my_reservations(fn_args, user_name)
                        elif fn == "cancel_reservation":
                            tool_result = self._execute_cancel_reservation(fn_args)

                        # 最初のtool結果を保存
                        if first_tool_result is None:
                            first_tool_result = tool_result
                            first_function_name = fn

                        # tool の実行結果をmessagesに追加
                        messages.append({
                            "role": "tool",
                            "tool_call_id": call.id,
                            "content": json.dumps(tool_result, ensure_ascii=False)
                        })

                # LLMに再度リクエストしてレスポンスを生成させる
                second_response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.1
                )

                final_message = second_response.choices[0].message
                ai_response = final_message.content

                # AIの応答を履歴に保存
                if session_id:
                    self.redis_service.add_message(session_id, "assistant", ai_response)

                # レスポンスを構築
                response_data = {
                    "success": True,
                    "response": ai_response,
                    "action": self._determine_action(first_function_name)
                }

                # create_reservationの場合、予約データを追加
                if first_function_name == "create_reservation" and first_tool_result:
                    if first_tool_result.get("success") and first_tool_result.get("reservation"):
                        response_data["reservation"] = first_tool_result["reservation"]

                # cancel_reservationの場合、予約IDを追加
                if first_function_name == "cancel_reservation" and first_tool_result:
                    if first_tool_result.get("success") and first_tool_result.get("reservation_id"):
                        response_data["reservation_id"] = first_tool_result["reservation_id"]

                return response_data

            # 通常の応答（tool_calls がない場合）
            ai_response = msg.content

            # AIの応答を履歴に保存
            if session_id:
                self.redis_service.add_message(session_id, "assistant", ai_response)

            return {
                "success": True,
                "response": ai_response,
                "action": "info"
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"AIサービスエラー: {str(e)}",
                "response": "申し訳ありませんが、システムエラーが発生しました。"
            }

    def _determine_action(self, function_name: str) -> str:
        """関数名からアクションタイプを判定"""
        action_map = {
            "create_reservation": "reserve",
            "find_available_rooms": "check",
            "get_reservations": "check",
            "get_my_reservations": "check",
            "cancel_reservation": "cancel"
        }
        return action_map.get(function_name, "info")

    def _execute_find_available_rooms(self, args):
        """予約可能な部屋の検索を実行（結果をJSONで返す）"""
        try:
            date = args.get("date")
            start_time = args.get("start_time")
            duration = int(args.get("duration_minutes")) if args.get("duration_minutes") is not None else None

            if not all([date, start_time, duration]):
                return {
                    "success": False,
                    "error": "検索に必要な情報が不足しています（date, start_time, duration_minutes）"
                }

            rooms = ReservationService.find_available_rooms_by_start_datetime_and_duration(date, start_time, duration)
            return {
                "success": True,
                "rooms": rooms,
                "date": date,
                "start_time": start_time,
                "duration_minutes": duration
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"空き状況の確認中にエラーが発生しました: {str(e)}"
            }

    def _execute_create_reservation(self, args):
        """予約を作成（結果をJSONで返す）"""
        url = f"{self.base_url}/api/reservations"

        room_id = args.get("room_id")
        if not room_id:
            return {
                "success": False,
                "error": "部屋IDが指定されていません"
            }

        data = {
            "room-id": str(room_id),
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
                    "reservation": result["reservation"]
                }
            else:
                return {
                    "success": False,
                    "error": result.get('error', '不明なエラー')
                }

        except Exception as e:
            return {
                "success": False,
                "error": f"予約処理中にエラーが発生しました: {str(e)}"
            }

    def _execute_get_reservations(self, args):
        """予約一覧を取得（結果をJSONで返す）"""
        try:
            url = f"{self.base_url}/api/reservations/{args['date']}"
            response = requests.get(url)
            result = response.json()

            if response.status_code == 200 and result.get("success"):
                return {
                    "success": True,
                    "reservations": result["reservations"],
                    "date": args['date']
                }
            else:
                return {
                    "success": False,
                    "error": "予約状況の確認中にエラーが発生しました"
                }

        except Exception as e:
            return {
                "success": False,
                "error": f"確認処理中にエラーが発生しました: {str(e)}"
            }

    def _execute_cancel_reservation(self, args):
        """予約をキャンセル（結果をJSONで返す）"""
        try:
            url = f"{self.base_url}/api/reservations/{args['reservation_id']}"
            response = requests.delete(url)
            result = response.json()

            if response.status_code == 200 and result.get("success"):
                return {
                    "success": True,
                    "reservation_id": args['reservation_id']
                }
            else:
                return {
                    "success": False,
                    "error": result.get('error', '不明なエラー')
                }

        except Exception as e:
            return {
                "success": False,
                "error": f"キャンセル処理中にエラーが発生しました: {str(e)}"
            }

    def _execute_get_my_reservations(self, args, user_name):
        """ユーザー自身の予約一覧を取得（結果をJSONで返す）"""
        try:
            date = args.get("date")
            result = ReservationService.get_reservations_by_username(user_name, date)

            if result.get("success"):
                return {
                    "success": True,
                    "reservations": result["reservations"],
                    "date": date,
                    "user_name": user_name
                }
            else:
                return {
                    "success": False,
                    "error": result.get("error", "予約状況の確認中にエラーが発生しました")
                }

        except Exception as e:
            return {
                "success": False,
                "error": f"確認処理中にエラーが発生しました: {str(e)}"
            }

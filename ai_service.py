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

            # AIの応答をチャット履歴に保存
            if session_id:
                # ユーザーメッセージを保存
                self.redis_service.add_message(session_id, "user", message)

            if tool_calls:
                # 今回は最初の tool_call を処理
                call = tool_calls[0]
                if call.type == "function":
                    fn = call.function.name
                    args_json = call.function.arguments or "{}"
                    try:
                        fn_args = json.loads(args_json)
                    except Exception:
                        fn_args = {}

                    result = None
                    if fn == "create_reservation":
                        result = self._call_create_reservation_api(fn_args, user_language)
                    elif fn == "find_available_rooms":
                        result = self._call_find_available_rooms_api(fn_args, user_language)
                    elif fn == "get_reservations":
                        result = self._call_get_reservations_api(fn_args, user_language)
                    elif fn == "get_my_reservations":
                        result = self._call_get_my_reservations_api(fn_args, user_name, user_language)
                    elif fn == "cancel_reservation":
                        result = self._call_cancel_reservation_api(fn_args, user_language)

                    # AIの応答を履歴に保存
                    if session_id and result:
                        self.redis_service.add_message(session_id, "assistant", result.get("response", ""))

                    return result

            # 通常の応答
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

    def _call_find_available_rooms_api(self, args, lang="ja"):
        """予約可能な部屋の検索を実行"""
        try:
            date = args.get("date")
            start_time = args.get("start_time")
            duration = int(args.get("duration_minutes")) if args.get("duration_minutes") is not None else None
            if not all([date, start_time, duration]):
                msg = "検索に必要な情報が不足しています（date, start_time, duration_minutes）" if lang == "ja" else "Missing required information (date, start_time, duration_minutes)"
                return {
                    "success": True,
                    "response": msg,
                    "action": "check"
                }

            rooms = ReservationService.find_available_rooms_by_start_datetime_and_duration(date, start_time, duration)
            if rooms:
                text = "\n".join([f"- {r['name']}" for r in rooms])
                if lang == "ja":
                    msg = f"空いている部屋:\n{text}\n予約する部屋名を教えてください。例えば『{rooms[0]['name']}』のように返信してください。"
                else:
                    msg = f"Available rooms:\n{text}\nPlease tell me which room you'd like to book. For example, reply with '{rooms[0]['name']}'."
                return {
                    "success": True,
                    "response": msg,
                    "action": "check",
                    "rooms": rooms
                }
            else:
                msg = "指定の時間帯で空いている部屋はありません。" if lang == "ja" else "No rooms are available for the specified time."
                return {
                    "success": True,
                    "response": msg,
                    "action": "check",
                    "rooms": []
                }
        except Exception as e:
            msg = "空き状況の確認中にエラーが発生しました。" if lang == "ja" else "An error occurred while checking availability."
            return {
                "success": False,
                "error": str(e),
                "response": msg
            }

    def _call_create_reservation_api(self, args, lang="ja"):
        """REST APIを呼び出して予約を作成し、LLMに結果を返す"""
        url = f"{self.base_url}/api/reservations"

        # room_idは必須（AIが部屋名からIDに変換済み）
        room_id = args.get("room_id")
        if not room_id:
            msg = "部屋IDが指定されていません。システムエラーです。" if lang == "ja" else "Room ID not specified. System error."
            return {
                "success": True,
                "response": msg,
                "action": "reserve"
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
                if lang == "ja":
                    msg = f"予約が完了しました！{result['reservation']['room_name']}を{args['date']} {args['start_time']}から{args['end_time']}まで予約しました。"
                else:
                    msg = f"Reservation completed! {result['reservation']['room_name']} has been booked from {args['start_time']} to {args['end_time']} on {args['date']}."
                return {
                    "success": True,
                    "response": msg,
                    "action": "reserve",
                    "reservation": result["reservation"]
                }
            else:
                error_msg = result.get('error', '不明なエラー' if lang == "ja" else 'Unknown error')
                msg = f"予約できませんでした: {error_msg}" if lang == "ja" else f"Reservation failed: {error_msg}"
                return {
                    "success": True,
                    "response": msg,
                    "action": "reserve"
                }

        except Exception as e:
            msg = "予約処理中にエラーが発生しました。" if lang == "ja" else "An error occurred during reservation."
            return {
                "success": False,
                "error": str(e),
                "response": msg
            }

    def _call_get_reservations_api(self, args, lang="ja"):
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
                    if lang == "ja":
                        msg = f"{args['date']}の予約状況:\n{reservation_list}"
                    else:
                        msg = f"Reservations for {args['date']}:\n{reservation_list}"
                    return {
                        "success": True,
                        "response": msg,
                        "action": "check"
                    }
                else:
                    msg = f"{args['date']}には予約がありません。" if lang == "ja" else f"No reservations on {args['date']}."
                    return {
                        "success": True,
                        "response": msg,
                        "action": "check"
                    }
            else:
                msg = "予約状況の確認中にエラーが発生しました。" if lang == "ja" else "An error occurred while checking reservations."
                return {
                    "success": True,
                    "response": msg,
                    "action": "check"
                }

        except Exception as e:
            msg = "確認処理中にエラーが発生しました。" if lang == "ja" else "An error occurred during the check."
            return {
                "success": False,
                "error": str(e),
                "response": msg
            }

    def _call_cancel_reservation_api(self, args, lang="ja"):
        """REST APIを呼び出して予約をキャンセル"""
        try:
            url = f"{self.base_url}/api/reservations/{args['reservation_id']}"
            response = requests.delete(url)
            result = response.json()

            if response.status_code == 200 and result.get("success"):
                msg = "予約をキャンセルしました。" if lang == "ja" else "Reservation cancelled successfully."
                return {
                    "success": True,
                    "response": msg,
                    "action": "cancel"
                }
            else:
                error_msg = result.get('error', '不明なエラー' if lang == "ja" else 'Unknown error')
                msg = f"キャンセルできませんでした: {error_msg}" if lang == "ja" else f"Cancellation failed: {error_msg}"
                return {
                    "success": True,
                    "response": msg,
                    "action": "cancel"
                }

        except Exception as e:
            msg = "キャンセル処理中にエラーが発生しました。" if lang == "ja" else "An error occurred during cancellation."
            return {
                "success": False,
                "error": str(e),
                "response": msg
            }

    def _call_get_my_reservations_api(self, args, user_name, lang="ja"):
        """ユーザー自身の予約一覧を取得"""
        try:
            date = args.get("date")
            result = ReservationService.get_reservations_by_username(user_name, date)

            if result.get("success"):
                reservations = result["reservations"]
                if reservations:
                    reservation_list = "\n".join([
                        f"- {r['room_name']} {r['start_time']}~{r['end_time']} ({r['date']})"
                        for r in reservations
                    ])
                    if date:
                        msg = f"{date}のあなたの予約:\n{reservation_list}" if lang == "ja" else f"Your reservations on {date}:\n{reservation_list}"
                        return {
                            "success": True,
                            "response": msg,
                            "action": "check"
                        }
                    else:
                        msg = f"あなたの予約一覧:\n{reservation_list}" if lang == "ja" else f"Your reservations:\n{reservation_list}"
                        return {
                            "success": True,
                            "response": msg,
                            "action": "check"
                        }
                else:
                    if date:
                        msg = f"{date}にあなたの予約はありません。" if lang == "ja" else f"You have no reservations on {date}."
                        return {
                            "success": True,
                            "response": msg,
                            "action": "check"
                        }
                    else:
                        msg = "あなたの予約はありません。" if lang == "ja" else "You have no reservations."
                        return {
                            "success": True,
                            "response": msg,
                            "action": "check"
                        }
            else:
                msg = "予約状況の確認中にエラーが発生しました。" if lang == "ja" else "An error occurred while checking reservations."
                return {
                    "success": True,
                    "response": msg,
                    "action": "check"
                }

        except Exception as e:
            msg = "確認処理中にエラーが発生しました。" if lang == "ja" else "An error occurred during the check."
            return {
                "success": False,
                "error": str(e),
                "response": msg
            }

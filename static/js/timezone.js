/**
 * タイムゾーン処理のユーティリティ (フロントエンド用)
 */

/**
 * JST（日本標準時）のタイムゾーンオフセット（+9時間）
 */
const JST_OFFSET = 9 * 60; // 分単位

/**
 * 現在のJST時刻を取得
 * @returns {Date} JST時刻のDateオブジェクト
 */
export function getJSTNow() {
  const now = new Date();
  return convertToJST(now);
}

/**
 * 任意のDateオブジェクトをJSTに変換
 * @param {Date} date 変換する日時
 * @returns {Date} JST時刻のDateオブジェクト
 */
export function convertToJST(date) {
  const utc = date.getTime() + (date.getTimezoneOffset() * 60000);
  return new Date(utc + (JST_OFFSET * 60000));
}

/**
 * JST時刻を日付文字列(YYYY-MM-DD)に変換
 * @param {Date} jstDate JST時刻のDateオブジェクト
 * @returns {string} YYYY-MM-DD形式の文字列
 */
export function formatJSTDate(jstDate) {
  const year = jstDate.getFullYear();
  const month = String(jstDate.getMonth() + 1).padStart(2, '0');
  const day = String(jstDate.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

/**
 * JST時刻を時刻文字列(HH:MM)に変換
 * @param {Date} jstDate JST時刻のDateオブジェクト
 * @returns {string} HH:MM形式の文字列
 */
export function formatJSTTime(jstDate) {
  const hours = String(jstDate.getHours()).padStart(2, '0');
  const minutes = String(jstDate.getMinutes()).padStart(2, '0');
  return `${hours}:${minutes}`;
}

/**
 * 今日の日付をJSTで取得
 * @returns {string} YYYY-MM-DD形式の今日の日付
 */
export function getTodayJST() {
  return formatJSTDate(getJSTNow());
}

/**
 * 現在のJST時刻を表示用の文字列に変換
 * @returns {string} YYYY年MM月DD日 HH:MM (JST)形式の文字列
 */
export function getJSTDisplayString() {
  const jstNow = getJSTNow();
  const year = jstNow.getFullYear();
  const month = jstNow.getMonth() + 1;
  const day = jstNow.getDate();
  const time = formatJSTTime(jstNow);
  return `${year}年${month}月${day}日 ${time} (JST)`;
}
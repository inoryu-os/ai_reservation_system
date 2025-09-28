import { getJSTNow } from "./timezone.js";
import { ReservationTable } from "./reservationTable.js";
import { ReservationFormUI } from "./formUI.js";
import "./chat.js";

let reservationTable;

/**
 * アプリケーション初期化
 */
document.addEventListener("DOMContentLoaded", async () => {
  // 予約表の初期化
  reservationTable = new ReservationTable();

  // 予約フォームUIの初期化（表の後に初期化しておく）
  new ReservationFormUI();

  // カレンダータイトルをJSTの現在月で初期化
  const calendarTitle = document.getElementById('calendar-title');
  if (calendarTitle) {
    const jstDate = getJSTNow();
    const year = jstDate.getFullYear();
    const month = jstDate.getMonth() + 1;
    calendarTitle.textContent = `${year}年${month}月`;
  }

  // 今日の予約を読み込み
  await reservationTable.refreshToday();

  // チャット機能から使用するためにグローバルに公開
  window.loadTodaysReservations = () => reservationTable.refreshToday();
  window.displayReservationInTable = (reservation, includeCancel = true) =>
    reservationTable.displayReservationInTable(reservation, includeCancel);
  window.ReservationTable = reservationTable;
});

import { ReservationTable } from "./reservationTable.js";
import { ReservationFormUI } from "./formUI.js";
import { CompactCalendar } from "./calendar.js";
import "./chat.js";

let reservationTable;
let compactCalendar;

/**
 * アプリケーション初期化
 */
document.addEventListener("DOMContentLoaded", async () => {
  // 予約表の初期化
  reservationTable = new ReservationTable();

  // 予約フォームUIの初期化（表の後に初期化しておく）
  new ReservationFormUI();

  // コンパクトカレンダーの初期化
  compactCalendar = new CompactCalendar();

  // 今日の予約を読み込み
  await reservationTable.refreshToday();

  // チャット機能・フォームから使用するためにグローバルに公開
  window.loadTodaysReservations = () => reservationTable.refreshToday();
  window.displayReservationInTable = (reservation, includeCancel = true) =>
    reservationTable.displayReservationInTable(reservation, includeCancel);
  window.ReservationTable = reservationTable;
  window.CompactCalendar = compactCalendar;
});

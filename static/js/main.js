import { createReservation, getReservationsByDate, cancelReservation as apiCancelReservation} from "./api.js";
import { displayReservationInTable, displayReservationsInTable, clearBookingTable } from "./bookingTable.js";
import { getElements, getFormData, showConfirm, resetForm, generateTimeOptions, populateSelect } from "./ui.js";
import { getTodayJST } from "./timezone.js";
import "./chat.js";

/**
 * 今日の予約を読み込み表示
 */
async function loadTodaysReservations() {
  const today = getTodayJST();
  const result = await getReservationsByDate(today);

  if (result.success) {
    displayReservationsInTable(result.reservations, true);
  } else {
    console.error('予約データの取得エラー:', result.error);
  }
}

/**
 * 予約フォームの送信処理
 * @param {Event} event
 * @param {HTMLFormElement} form
 * @param {HTMLButtonElement} submitButton
 */
async function handleReservationSubmit(event, form, submitButton) {
  event.preventDefault();

  const data = getFormData(form);

  const result = await createReservation(data);

  if (result.success) {
    displayReservationInTable(result.reservation, true);
    resetForm(form);
  }
}

/**
 * キャンセルボタンのクリック処理
 * @param {Event} event
 */
async function handleCancelClick(event) {
  if (!event.target.classList.contains('cancel-btn')) return;

  const reservationId = event.target.getAttribute('data-reservation-id');

  if (!showConfirm('この予約をキャンセルしますか？')) return;

  const result = await apiCancelReservation(reservationId);

  if (result.success) {
    await loadTodaysReservations();
  } 
}

/**
 * アプリケーション初期化
 */
document.addEventListener("DOMContentLoaded", async () => {
  const { startSelect, endSelect, reservationForm, submitButton } = getElements();

  // 時間選択肢を設定
  populateSelect(startSelect, generateTimeOptions(), "開始時刻");
  populateSelect(endSelect, generateTimeOptions(), "終了時刻");

  // 日付フィールドにJSTの今日の日付を設定
  const dateInput = document.getElementById('date-select');
  if (dateInput) {
    dateInput.value = getTodayJST();
  }

  // カレンダータイトルをJSTの現在月で初期化
  const calendarTitle = document.getElementById('calendar-title');
  if (calendarTitle) {
    const jstNow = new Date();
    const jstDate = new Date(jstNow.getTime() + (9 * 60 * 60 * 1000)); // JST (+9時間)
    const year = jstDate.getFullYear();
    const month = jstDate.getMonth() + 1;
    calendarTitle.textContent = `${year}年${month}月`;
  }

  // 予約表のタイトルをJSTの今日で初期化
  const bookingTableDate = document.getElementById('booking-table-date');
  if (bookingTableDate) {
    const jstNow = new Date();
    const jstDate = new Date(jstNow.getTime() + (9 * 60 * 60 * 1000)); // JST (+9時間)
    const year = jstDate.getFullYear();
    const month = jstDate.getMonth() + 1;
    const day = jstDate.getDate();
    bookingTableDate.textContent = `今日 (${year}年${month}月${day}日)`;
  }

  // 今日の予約を読み込み
  await loadTodaysReservations();

  // イベントリスナーを設定
  reservationForm.addEventListener('submit', (event) =>
    handleReservationSubmit(event, reservationForm, submitButton)
  );

  document.addEventListener('click', handleCancelClick);

  // チャット機能から使用するためにグローバルに公開
  window.loadTodaysReservations = loadTodaysReservations;
  window.displayReservationInTable = displayReservationInTable;
});
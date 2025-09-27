import { createReservation, getReservationsByDate, cancelReservation as apiCancelReservation} from "./api.js";
import { displayReservationInTable, displayReservationsInTable, clearBookingTable } from "./bookingTable.js";
import { getElements, getFormData, showConfirm, resetForm, generateTimeOptions, populateSelect } from "./ui.js";

/**
 * 今日の予約を読み込み表示
 */
async function loadTodaysReservations() {
  const today = new Date().toISOString().split('T')[0];
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

  // 今日の予約を読み込み
  await loadTodaysReservations();

  // イベントリスナーを設定
  reservationForm.addEventListener('submit', (event) =>
    handleReservationSubmit(event, reservationForm, submitButton)
  );

  document.addEventListener('click', handleCancelClick);
});
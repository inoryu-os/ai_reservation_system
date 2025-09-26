import { generateTimeOptions, populateSelect } from "./time.js";
import { createReservation, getReservationsByDate, cancelReservation as apiCancelReservation, getTodayDate } from "./api.js";
import { displayReservationInTable, displayReservationsInTable, clearBookingTable } from "./bookingTable.js";
import { getElements, showMessage, setButtonLoadingState, getFormData, showConfirm, resetForm } from "./ui.js";

/**
 * 今日の予約を読み込み表示
 */
async function loadTodaysReservations() {
  const today = getTodayDate();
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
  setButtonLoadingState(submitButton, true, '予約中...');

  const result = await createReservation(data);

  setButtonLoadingState(submitButton, false);

  if (result.success) {
    showMessage(result.message, true);
    displayReservationInTable(result.reservation, true);
    resetForm(form);
  } else {
    showMessage(result.error, false);
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

  setButtonLoadingState(event.target, true, '...');

  const result = await apiCancelReservation(reservationId);

  if (result.success) {
    showMessage(result.message, true);
    await loadTodaysReservations();
  } else {
    showMessage(result.error, false);
    setButtonLoadingState(event.target, false);
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
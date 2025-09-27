/**
 * UI操作を担当するモジュール
 */

/**
 * DOM要素を取得
 * @returns {object}
 */
export function getElements() {
  return {
    startSelect: document.getElementById("start-time"),
    endSelect: document.getElementById("end-time"),
    reservationForm: document.getElementById("reservation-form"),
    bookingTableBody: document.getElementById("booking-table-body"),
    submitButton: document.getElementById('reserve-btn')
  };
}

/**
 * フォームからデータを取得
 * @param {HTMLFormElement} form
 * @returns {object}
 */
export function getFormData(form) {
  const formData = new FormData(form);
  return {
    'room-id': formData.get('room-id'),
    'date': formData.get('date'),
    'start-time': formData.get('start-time'),
    'end-time': formData.get('end-time')
  };
}

/**
 * 確認ダイアログを表示
 * @param {string} message
 * @returns {boolean}
 */
export function showConfirm(message) {
  return confirm(message);
}

/**
 * フォームをリセット
 * @param {HTMLFormElement} form
 */
export function resetForm(form) {
  form.reset();
}
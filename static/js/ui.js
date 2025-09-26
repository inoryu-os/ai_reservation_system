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
 * メッセージを表示
 * @param {string} message 表示メッセージ
 * @param {boolean} isSuccess 成功メッセージかどうか
 */
export function showMessage(message, isSuccess = true) {
  const alertClass = isSuccess ? 'alert-success' : 'alert-danger';
  const alertHtml = `
    <div class="alert ${alertClass} alert-dismissible fade show" role="alert">
      ${message}
      <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="閉じる"></button>
    </div>
  `;

  // 既存のアラートを削除
  const existingAlert = document.querySelector('.alert');
  if (existingAlert) {
    existingAlert.remove();
  }

  // 新しいアラートを挿入
  const form = document.getElementById('reservation-form');
  form.insertAdjacentHTML('beforebegin', alertHtml);
}

/**
 * ボタンのローディング状態を設定
 * @param {HTMLElement} button
 * @param {boolean} isLoading
 * @param {string} loadingText
 */
export function setButtonLoadingState(button, isLoading, loadingText = '処理中...') {
  if (isLoading) {
    button.dataset.originalText = button.innerHTML;
    button.innerHTML = `<i class="fas fa-spinner fa-spin me-2"></i>${loadingText}`;
    button.disabled = true;
  } else {
    button.innerHTML = button.dataset.originalText || button.innerHTML;
    button.disabled = false;
  }
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
/**
 * UI操作を担当するモジュール
 */
import { TIME } from "./config.js";


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

// 予約時間の配列を生成（[{value:"07:00", text:"07:00"}, ...]）
export function generateTimeOptions() {
  const { startHour, endHour, stepMinutes } = TIME;
  const options = [];
  for (let hour = startHour; hour <= endHour; hour++) {
    for (let minute = 0; minute < 60; minute += stepMinutes) {
      if (hour === endHour && minute > 0) break;
      const h = String(hour).padStart(2, "0");
      const m = String(minute).padStart(2, "0");
      const timeStr = `${h}:${m}`;
      options.push({ value: timeStr, text: timeStr });
    }
  }
  return options;
}

// <select> を options で埋める
export function populateSelect(selectElement, options, defaultText) {
  if (!selectElement) return;
  selectElement.innerHTML = "";

  if (defaultText) {
    const def = document.createElement("option");
    def.value = "";
    def.textContent = defaultText;
    selectElement.appendChild(def);
  }
  for (const opt of options) {
    const el = document.createElement("option");
    el.value = opt.value;
    el.textContent = opt.text;
    if (opt.disabled) el.disabled = true;
    selectElement.appendChild(el);
  }
}
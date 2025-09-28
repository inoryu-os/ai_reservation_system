/**
 * 予約フォームのUIと処理をまとめたクラス
 */
import { createReservation } from "./api.js";
import { getTodayJST } from "./timezone.js";
import { TIME } from "./config.js";

export class ReservationFormUI {
  constructor() {
    this.form = document.getElementById("reservation-form");
    if (!this.form) return; // フォームが無い場合は何もしない

    this.startSelect = document.getElementById("start-time");
    this.endSelect = document.getElementById("end-time");
    this.dateInput = document.getElementById("date-select");
    this.submitButton = document.getElementById("reserve-btn");

    this.init();
  }

  init() {
    // 時刻セレクトの初期化
    const timeOptions = generateTimeOptions();
    populateSelect(this.startSelect, timeOptions, "開始時刻");
    populateSelect(this.endSelect, timeOptions, "終了時刻");

    // 日付の初期値をJSTの今日に設定
    if (this.dateInput) {
      this.dateInput.value = getTodayJST();
    }

    // 送信イベント
    this.form.addEventListener("submit", (e) => this.handleSubmit(e));
  }

  async handleSubmit(event) {
    event.preventDefault();
    if (!this.form) return;

    const payload = getFormData(this.form);

    // 送信中のUI状態
    this.setSubmitting(true);

    try {
      const result = await createReservation(payload);
      if (result.success) {
        if (window.displayReservationInTable) {
          window.displayReservationInTable(result.reservation, true);
        }
        resetForm(this.form);

        // 送信後も今日の日付に戻す（UXのため）
        if (this.dateInput) {
          this.dateInput.value = getTodayJST();
        }
      } else {
        // エラーはAPI側で整形済み。必要ならアラート等で表示
        console.error("予約作成エラー:", result.error);
        alert(result.error || "予約の作成に失敗しました");
      }
    } catch (err) {
      console.error("予約送信中にエラー:", err);
      alert("通信エラーが発生しました");
    } finally {
      this.setSubmitting(false);
    }
  }

  setSubmitting(isSubmitting) {
    if (!this.submitButton) return;
    this.submitButton.disabled = isSubmitting;
    this.submitButton.innerHTML = isSubmitting
      ? '<i class="fas fa-spinner fa-spin me-2" aria-hidden="true"></i>送信中'
      : '<i class="fas fa-calendar-plus me-2" aria-hidden="true"></i>予約する';
  }
}

// 以下、UIユーティリティ（このモジュール内に集約）

function generateTimeOptions() {
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

function populateSelect(selectElement, options, defaultText) {
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

function getFormData(form) {
  const formData = new FormData(form);
  return {
    'room-id': formData.get('room-id'),
    'date': formData.get('date'),
    'start-time': formData.get('start-time'),
    'end-time': formData.get('end-time')
  };
}

function resetForm(form) {
  form.reset();
}

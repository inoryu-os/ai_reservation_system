import { TIME } from "./config.js";

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
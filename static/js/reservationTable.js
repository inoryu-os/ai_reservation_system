/**
 * 予約表（テーブル）表示・操作を担当するクラス
 */
import { getReservationsByDate, cancelReservation } from "./api.js";
import { getJSTNow, getTodayJST } from "./timezone.js";

export class ReservationTable {
  constructor() {
    this.tableBody = document.getElementById("booking-table-body");
    this.titleEl = document.getElementById("booking-table-date");
    this.container = document.querySelector(".booking-table");

    // テーブルボディをJSで構築
    this.buildTableBody();

    // タイトルを即時に今日へ設定
    this.setTodayTitle();

    // 初期化（キャンセルボタンの委譲ハンドラ）
    this.initEventDelegation();
  }

  initEventDelegation() {
    document.addEventListener("click", async (e) => {
      const target = e.target;
      if (!(target instanceof Element)) return;
      if (!target.classList.contains("cancel-btn")) return;

      const reservationId = target.getAttribute("data-reservation-id");
      if (!reservationId) return;

      if (!showConfirm("この予約をキャンセルしますか？")) return;

      const result = await cancelReservation(reservationId);
      if (result.success) {
        await this.refreshToday();
      }
    });
  }

  async refreshToday() {
    const today = getTodayJST();
    const result = await getReservationsByDate(today);
    if (result.success) {
      this.setTodayTitle();
      this.displayReservationsInTable(result.reservations, true);
    } else {
      console.error("予約データの取得エラー:", result.error);
    }
  }

  setTodayTitle() {
    if (!this.titleEl) return;
    const jstDate = getJSTNow();
    const year = jstDate.getFullYear();
    const month = jstDate.getMonth() + 1;
    const day = jstDate.getDate();
    this.titleEl.textContent = `今日 (${year}年${month}月${day}日)`;
  }

  buildTableBody() {
    if (!this.tableBody) return;
    const roomHeaders = document.querySelectorAll('.room-header');
    const cols = roomHeaders.length;
    const slots = this.generateTimeSlots();

    this.tableBody.innerHTML = '';

    for (const slot of slots) {
      const tr = document.createElement('tr');

      const th = document.createElement('th');
      th.className = 'text-center';
      th.setAttribute('scope', 'row');
      const hh = String(slot.hour).padStart(2, '0');
      const mm = String(slot.min).padStart(2, '0');
      th.textContent = `${hh}:${mm}~`;
      tr.appendChild(th);

      for (let i = 0; i < cols; i++) {
        const td = document.createElement('td');
        td.className = 'booking-cell';
        tr.appendChild(td);
      }

      this.tableBody.appendChild(tr);
    }
  }

  clear() {
    const bookingCells = document.querySelectorAll('.booking-cell');
    bookingCells.forEach(cell => {
      cell.innerHTML = '';
      cell.classList.remove('table-warning');
    });
  }

  displayReservationsInTable(reservations, includeCancel = false) {
    this.clear();
    reservations.forEach(r => this.displayReservationInTable(r, includeCancel));
  }

  displayReservationInTable(reservation, includeCancel = false) {
    const { room_id, start_time, end_time, user_name } = reservation;

    const bookingCells = document.querySelectorAll('.booking-cell');
    const roomHeaders = document.querySelectorAll('.room-header');

    const roomColumnIndex = this.findRoomColumnIndex(roomHeaders, room_id);
    if (roomColumnIndex === -1) return;

    const { startHour, startMin, endHour, endMin } = this.parseTimeRange(start_time, end_time);

    const timeSlots = this.generateTimeSlots();
    timeSlots.forEach((slot, slotIndex) => {
      const slotTime = slot.hour * 60 + slot.min;
      const reservationStart = startHour * 60 + startMin;
      const reservationEnd = endHour * 60 + endMin;

      if (slotTime >= reservationStart && slotTime < reservationEnd) {
        const cellIndex = slotIndex * roomHeaders.length + roomColumnIndex;
        const cell = bookingCells[cellIndex];
        if (cell) {
          cell.innerHTML = this.createReservationCellContent(user_name, reservation.id, includeCancel);
          cell.classList.add('table-warning');
        }
      }
    });
  }

  generateTimeSlots() {
    const slots = [];
    for (let hour = 7; hour < 23; hour++) {
      for (let min = 0; min < 60; min += 30) {
        if (hour === 22 && min === 30) break; // 22:30で終了
        slots.push({ hour, min });
      }
    }
    return slots;
  }

  findRoomColumnIndex(roomHeaders, roomId) {
    for (let i = 0; i < roomHeaders.length; i++) {
      if (roomHeaders[i].dataset.roomId === roomId.toString()) {
        return i;
      }
    }
    return -1;
  }

  parseTimeRange(startTime, endTime) {
    const [startHour, startMin] = startTime.split(':').map(Number);
    const [endHour, endMin] = endTime.split(':').map(Number);
    return { startHour, startMin, endHour, endMin };
  }

  createReservationCellContent(userName, reservationId, includeCancel) {
    const cancelButton = includeCancel && reservationId
      ? `<button class="btn btn-sm btn-outline-danger cancel-btn" data-reservation-id="${reservationId}" title="キャンセル">×</button>`
      : '';
    return `
      <div class="booking-reserved d-flex justify-content-between align-items-center">
        <small>${userName}</small>
        ${cancelButton}
      </div>
    `;
  }
}

// 簡易確認ダイアログ（このモジュールに集約）
function showConfirm(message) {
  return confirm(message);
}

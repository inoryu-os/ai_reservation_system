/**
 * 予約表操作を担当するモジュール
 */

/**
 * 時間スロット設定
 */
const TIME_SLOTS = {
  START_HOUR: 7,
  END_HOUR: 23,
  INTERVAL_MINUTES: 30
};

/**
 * 時間スロットを生成
 * @returns {Array<{hour: number, min: number}>}
 */
function generateTimeSlots() {
  const slots = [];
  for (let hour = TIME_SLOTS.START_HOUR; hour < TIME_SLOTS.END_HOUR; hour++) {
    for (let min = 0; min < 60; min += TIME_SLOTS.INTERVAL_MINUTES) {
      if (hour === 22 && min === 30) break; // 22:30で終了
      slots.push({ hour, min });
    }
  }
  return slots;
}

/**
 * 予約表を初期化（全てのセルをクリア）
 */
export function clearBookingTable() {
  const bookingCells = document.querySelectorAll('.booking-cell');
  bookingCells.forEach(cell => {
    cell.innerHTML = '';
    cell.classList.remove('table-warning');
  });
}

/**
 * 予約情報を予約表に表示
 * @param {object} reservation 予約データ
 * @param {boolean} includeCancel キャンセルボタンを含めるか
 */
export function displayReservationInTable(reservation, includeCancel = false) {
  const { room_id, start_time, end_time, user_name } = reservation;

  const bookingCells = document.querySelectorAll('.booking-cell');
  const roomHeaders = document.querySelectorAll('.room-header');

  // 会議室の列インデックスを取得
  const roomColumnIndex = findRoomColumnIndex(roomHeaders, room_id);
  if (roomColumnIndex === -1) return;

  // 時間の解析
  const { startHour, startMin, endHour, endMin } = parseTimeRange(start_time, end_time);

  // 時間スロットの生成と予約表示
  const timeSlots = generateTimeSlots();
  timeSlots.forEach((slot, slotIndex) => {
    const slotTime = slot.hour * 60 + slot.min;
    const reservationStart = startHour * 60 + startMin;
    const reservationEnd = endHour * 60 + endMin;

    if (slotTime >= reservationStart && slotTime < reservationEnd) {
      const cellIndex = slotIndex * roomHeaders.length + roomColumnIndex;
      const cell = bookingCells[cellIndex];

      if (cell) {
        cell.innerHTML = createReservationCellContent(user_name, reservation.id, includeCancel);
        cell.classList.add('table-warning');
      }
    }
  });
}

/**
 * 複数の予約を予約表に表示
 * @param {Array} reservations 予約データの配列
 * @param {boolean} includeCancel キャンセルボタンを含めるか
 */
export function displayReservationsInTable(reservations, includeCancel = false) {
  clearBookingTable();
  reservations.forEach(reservation => {
    displayReservationInTable(reservation, includeCancel);
  });
}

/**
 * 会議室の列インデックスを検索
 * @param {NodeList} roomHeaders
 * @param {string|number} roomId
 * @returns {number}
 */
function findRoomColumnIndex(roomHeaders, roomId) {
  for (let i = 0; i < roomHeaders.length; i++) {
    if (roomHeaders[i].dataset.roomId === roomId.toString()) {
      return i;
    }
  }
  return -1;
}

/**
 * 時間範囲を解析
 * @param {string} startTime HH:MM形式
 * @param {string} endTime HH:MM形式
 * @returns {object}
 */
function parseTimeRange(startTime, endTime) {
  const [startHour, startMin] = startTime.split(':').map(Number);
  const [endHour, endMin] = endTime.split(':').map(Number);

  return { startHour, startMin, endHour, endMin };
}

/**
 * 予約セルの内容を作成
 * @param {string} userName
 * @param {number|undefined} reservationId
 * @param {boolean} includeCancel
 * @returns {string}
 */
function createReservationCellContent(userName, reservationId, includeCancel) {
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
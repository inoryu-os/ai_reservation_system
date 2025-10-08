/**
 * コンパクトカレンダー機能
 */
import { getJSTNow } from "./timezone.js";
import { getReservationsByDate } from "./api.js";

export class CompactCalendar {
  constructor() {
    this.calendarBody = document.querySelector('.calendar-table tbody');
    this.calendarTitle = document.getElementById('calendar-title');
    this.prevButton = document.getElementById('prev-month');
    this.nextButton = document.getElementById('next-month');
    this.dateInput = document.getElementById('date-select');

    if (!this.calendarBody) return;

    // 現在表示中の年月（JST基準）
    const now = getJSTNow();
    this.currentYear = now.getFullYear();
    this.currentMonth = now.getMonth(); // 0-11

    // 今日の日付を保持（比較用）
    this.today = {
      year: now.getFullYear(),
      month: now.getMonth(),
      date: now.getDate()
    };

    // 選択中の日付
    this.selectedDate = null;

    this.init();
  }

  init() {
    // カレンダーを描画
    this.renderCalendar();

    // イベントリスナー設定
    if (this.prevButton) {
      this.prevButton.addEventListener('click', () => this.prevMonth());
    }
    if (this.nextButton) {
      this.nextButton.addEventListener('click', () => this.nextMonth());
    }

    // カレンダーの日付クリック処理（イベント委譲）
    if (this.calendarBody) {
      this.calendarBody.addEventListener('click', (e) => {
        const target = e.target;
        if (target.classList.contains('calendar-day')) {
          const dateStr = target.dataset.date;
          if (dateStr) {
            this.selectDate(dateStr);
          }
        }
      });
    }
  }

  prevMonth() {
    this.currentMonth--;
    if (this.currentMonth < 0) {
      this.currentMonth = 11;
      this.currentYear--;
    }
    this.renderCalendar();
  }

  nextMonth() {
    this.currentMonth++;
    if (this.currentMonth > 11) {
      this.currentMonth = 0;
      this.currentYear++;
    }
    this.renderCalendar();
  }

  renderCalendar() {
    if (!this.calendarBody) return;

    // タイトルを更新
    if (this.calendarTitle) {
      this.calendarTitle.textContent = `${this.currentYear}年${this.currentMonth + 1}月`;
    }

    // カレンダーボディをクリア
    this.calendarBody.innerHTML = '';

    // 月の最初の日と最後の日
    const firstDay = new Date(this.currentYear, this.currentMonth, 1);
    const lastDay = new Date(this.currentYear, this.currentMonth + 1, 0);

    // 最初の日の曜日（0=日曜）
    const firstDayOfWeek = firstDay.getDay();

    // 月の日数
    const daysInMonth = lastDay.getDate();

    // カレンダーを構築
    let day = 1;
    let hasMoreDays = true;

    for (let week = 0; week < 6 && hasMoreDays; week++) {
      const tr = document.createElement('tr');
      tr.className = 'text-center';

      for (let dayOfWeek = 0; dayOfWeek < 7; dayOfWeek++) {
        const td = document.createElement('td');
        td.className = 'p-1';

        // 最初の週で、まだ月の開始前
        if (week === 0 && dayOfWeek < firstDayOfWeek) {
          td.innerHTML = '';
        }
        // 月の日数を超えた
        else if (day > daysInMonth) {
          td.innerHTML = '';
          hasMoreDays = false;
        }
        // 有効な日付
        else {
          const dateStr = this.formatDate(this.currentYear, this.currentMonth, day);
          const isToday = this.isToday(this.currentYear, this.currentMonth, day);
          const isSelected = this.selectedDate === dateStr;

          const button = document.createElement('button');
          button.type = 'button';
          button.className = 'calendar-day btn btn-sm';
          button.dataset.date = dateStr;
          button.textContent = day;

          // 今日の場合
          if (isToday) {
            button.classList.add('btn-primary', 'text-white');
          }
          // 選択中の場合
          else if (isSelected) {
            button.classList.add('btn-success');
          }
          // 通常の日
          else {
            button.classList.add('btn-outline-secondary');
          }

          // 日曜日は赤文字
          if (dayOfWeek === 0 && !isToday && !isSelected) {
            button.classList.add('text-danger');
          }
          // 土曜日は青文字
          if (dayOfWeek === 6 && !isToday && !isSelected) {
            button.classList.add('text-primary');
          }

          td.appendChild(button);
          day++;
        }

        tr.appendChild(td);
      }

      this.calendarBody.appendChild(tr);
    }
  }

  async selectDate(dateStr, updateInput = true) {
    this.selectedDate = dateStr;

    // 選択した日付の年月を表示するようにカレンダーを移動
    const [year, month, day] = dateStr.split('-').map(Number);
    this.currentYear = year;
    this.currentMonth = month - 1; // 0-11

    // カレンダーを再描画（選択状態を反映）
    this.renderCalendar();

    // 日付入力フォームに自動入力（外部から呼ばれた場合は更新しない）
    if (updateInput && this.dateInput) {
      this.dateInput.value = dateStr;
    }

    // 選択した日付の予約情報を取得して予約表に表示
    await this.updateReservationTable(dateStr);
  }

  async updateReservationTable(dateStr) {
    if (window.ReservationTable) {
      const result = await getReservationsByDate(dateStr);
      if (result.success) {
        // 予約表のタイトルを更新
        const [year, month, day] = dateStr.split('-').map(Number);
        const titleEl = document.getElementById('booking-table-date');
        if (titleEl) {
          const isToday = this.isToday(year, month - 1, day);
          if (isToday) {
            titleEl.textContent = `今日 (${year}年${month}月${day}日)`;
          } else {
            titleEl.textContent = `${year}年${month}月${day}日`;
          }
        }

        // 予約データを表示
        window.ReservationTable.displayReservationsInTable(result.reservations, true);
      }
    }
  }

  // 外部から日付を選択（formUIからの呼び出し用）
  async selectDateFromExternal(dateStr, updateInput = false) {
    await this.selectDate(dateStr, updateInput);
  }

  formatDate(year, month, day) {
    const y = String(year);
    const m = String(month + 1).padStart(2, '0');
    const d = String(day).padStart(2, '0');
    return `${y}-${m}-${d}`;
  }

  isToday(year, month, day) {
    return (
      year === this.today.year &&
      month === this.today.month &&
      day === this.today.date
    );
  }
}

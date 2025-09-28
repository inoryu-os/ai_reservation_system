import {generateTimeOptions} from "./ui.js"

  const tbody = document.getElementById('booking-table-body');

  export function displayReservationInTable(reservation, includeCancel = false) {
    const options = generateTimeOptions;
    const row_num = options.length();
    for (let i = 0; i < row_num ; i++){
      tbody.innerHTML = '<th>${options}</th>';
    };
  }
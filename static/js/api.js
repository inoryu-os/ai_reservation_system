/**
 * API通信を担当するモジュール
 */

const API_ENDPOINTS = {
  RESERVE: '/api/reserve',
  RESERVATIONS: '/api/reservations',
};

/**
 * 共通のfetch処理
 * @param {string} url
 * @param {object} options
 * @returns {Promise<object>}
 */
async function fetchAPI(url, options = {}) {
  try {
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      },
      ...options
    });

    const result = await response.json();
    return result;
  } catch (error) {
    console.error(`API通信エラー (${url}):`, error);
    return {
      success: false,
      error: 'ネットワークエラーが発生しました'
    };
  }
}

/**
 * 予約作成
 * @param {object} reservationData
 * @returns {Promise<object>}
 */
export async function createReservation(reservationData) {
  return await fetchAPI(API_ENDPOINTS.RESERVE, {
    method: 'POST',
    body: JSON.stringify(reservationData)
  });
}

/**
 * 指定日の予約一覧取得
 * @param {string} date YYYY-MM-DD形式の日付
 * @returns {Promise<object>}
 */
export async function getReservationsByDate(date) {
  return await fetchAPI(`${API_ENDPOINTS.RESERVATIONS}/${date}`);
}

/**
 * 予約キャンセル
 * @param {number} reservationId
 * @returns {Promise<object>}
 */
export async function cancelReservation(reservationId) {
  return await fetchAPI(`${API_ENDPOINTS.RESERVATIONS}/${reservationId}`, {
    method: 'DELETE'
  });
}

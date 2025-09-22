import axios from 'axios';

// バックエンドAPIのベースURL
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001/api';

// APIクライアントを作成
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// --- Diagnostics: request/response logging in development ---
if (process.env.NODE_ENV !== 'production') {
  apiClient.interceptors.request.use((config) => {
    // eslint-disable-next-line no-console
    console.info('[API request]', {
      method: config.method,
      url: `${config.baseURL || ''}${config.url}`,
      data: config.data,
    });
    return config;
  });

  apiClient.interceptors.response.use(
    (response) => {
      // eslint-disable-next-line no-console
      console.info('[API response]', {
        status: response.status,
        url: response.config?.url,
        requestId: response.headers?.['x-request-id'] || null,
      });
      return response;
    },
    (error) => {
      const status = error.response?.status;
      const data = error.response?.data;
      const requestId = error.response?.headers?.['x-request-id'] || null;
      // eslint-disable-next-line no-console
      console.error('[API error]', { status, data, requestId });
      return Promise.reject(error);
    }
  );
}

/**
 * 予測を取得する
 * @param {Object} data - 予測に必要なデータ
 * @returns {Promise<Object>} 予測結果
 */
export const makePrediction = async (data) => {
  try {
    const response = await apiClient.post('/predict', data);
    return response.data;
  } catch (error) {
    console.error('APIエラー (予測):', error);
    throw error;
  }
};

/**
 * 週間予測を取得する
 * @param {Object} data - 予測に必要なデータ
 * @returns {Promise<Object>} 7日分の予測結果
 */
export const makeWeekPrediction = async (data) => {
  try {
    const response = await apiClient.post('/predict_week', data);
    return response.data;
  } catch (error) {
    console.error('APIエラー (週間予測):', error);
    throw error;
  }
};

/**
 * 月間予測を取得する
 * @param {Object} data - { year, month, total_outpatient, intro_outpatient, ER, bed_count }
 * @returns {Promise<Object>} 月間の予測結果
 */
export const makeMonthPrediction = async (data) => {
  try {
    const response = await apiClient.post('/predict_month', data);
    return response.data;
  } catch (error) {
    console.error('APIエラー (月間予測):', error);
    throw error;
  }
};

/**
 * シナリオ一覧を取得する
 * @returns {Promise<Array>} シナリオ一覧
 */
export const getScenarios = async () => {
  try {
    const response = await apiClient.get('/scenarios');
    return response.data;
  } catch (error) {
    console.error('APIエラー (シナリオ取得):', error);
    throw error;
  }
};

/**
 * ヘルスチェック
 * @returns {Promise<Object>} ヘルスチェック結果
 */
export const checkHealth = async () => {
  try {
    const response = await apiClient.get('/health');
    return response.data;
  } catch (error) {
    console.error('APIエラー (ヘルスチェック):', error);
    throw error;
  }
}; 

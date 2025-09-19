import axios from 'axios';

// バックエンドAPIのベースURL
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

// APIクライアントを作成
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

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
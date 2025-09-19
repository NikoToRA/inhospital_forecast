import os
import json
from datetime import datetime
from typing import Optional, Dict, List
from supabase import create_client, Client
import logging

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SupabaseService:
    def __init__(self):
        """Supabaseクライアントを初期化"""
        self.supabase_url = os.environ.get('SUPABASE_URL')
        self.supabase_key = os.environ.get('SUPABASE_KEY')

        if not self.supabase_url or not self.supabase_key:
            logger.warning("Supabase credentials not found. Database features disabled.")
            self.client = None
        else:
            try:
                self.client: Client = create_client(self.supabase_url, self.supabase_key)
                logger.info("Supabase client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Supabase client: {e}")
                self.client = None

    def is_available(self) -> bool:
        """Supabaseが利用可能かチェック"""
        return self.client is not None

    def log_prediction(self, prediction_data: Dict) -> bool:
        """
        予測結果をSupabaseに記録

        Args:
            prediction_data (dict): 予測データ

        Returns:
            bool: 記録成功かどうか
        """
        if not self.client:
            logger.warning("Supabase not available. Skipping prediction log.")
            return False

        try:
            # 予測ログデータを準備
            log_data = {
                'prediction_date': prediction_data.get('date'),
                'predicted_value': prediction_data.get('prediction'),
                'total_outpatient': prediction_data.get('features', {}).get('total_outpatient'),
                'intro_outpatient': prediction_data.get('features', {}).get('intro_outpatient'),
                'er_patients': prediction_data.get('features', {}).get('ER'),
                'bed_count': prediction_data.get('features', {}).get('bed_count'),
                'public_holiday': prediction_data.get('features', {}).get('public_holiday', False),
                'day_of_week': prediction_data.get('day'),
                'features': json.dumps(prediction_data.get('features', {}))
            }

            # Supabaseに挿入
            result = self.client.table('prediction_logs').insert(log_data).execute()
            logger.info("Prediction logged to Supabase successfully")
            return True

        except Exception as e:
            logger.error(f"Error logging prediction to Supabase: {e}")
            return False

    def get_prediction_history(self, limit: int = 100) -> List[Dict]:
        """
        予測履歴を取得

        Args:
            limit (int): 取得する件数

        Returns:
            list: 予測履歴のリスト
        """
        if not self.client:
            return []

        try:
            result = self.client.table('prediction_logs') \
                .select('*') \
                .order('created_at', desc=True) \
                .limit(limit) \
                .execute()

            return result.data

        except Exception as e:
            logger.error(f"Error fetching prediction history: {e}")
            return []

    def get_app_setting(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        アプリケーション設定を取得

        Args:
            key (str): 設定キー
            default: デフォルト値

        Returns:
            設定値
        """
        if not self.client:
            return default

        try:
            result = self.client.table('app_settings') \
                .select('setting_value') \
                .eq('setting_key', key) \
                .execute()

            if result.data:
                return result.data[0]['setting_value']
            return default

        except Exception as e:
            logger.error(f"Error getting app setting {key}: {e}")
            return default

    def set_app_setting(self, key: str, value: str, description: str = None) -> bool:
        """
        アプリケーション設定を保存

        Args:
            key (str): 設定キー
            value (str): 設定値
            description (str): 説明

        Returns:
            bool: 保存成功かどうか
        """
        if not self.client:
            return False

        try:
            # 既存の設定があるかチェック
            existing = self.client.table('app_settings') \
                .select('id') \
                .eq('setting_key', key) \
                .execute()

            data = {
                'setting_key': key,
                'setting_value': value,
                'updated_at': datetime.now().isoformat()
            }

            if description:
                data['description'] = description

            if existing.data:
                # 更新
                result = self.client.table('app_settings') \
                    .update(data) \
                    .eq('setting_key', key) \
                    .execute()
            else:
                # 新規作成
                result = self.client.table('app_settings') \
                    .insert(data) \
                    .execute()

            return True

        except Exception as e:
            logger.error(f"Error setting app setting {key}: {e}")
            return False

    def cache_scenario_data(self, scenario_data: List[Dict], data_hash: str) -> bool:
        """
        シナリオデータをキャッシュ

        Args:
            scenario_data (list): シナリオデータ
            data_hash (str): データのハッシュ値

        Returns:
            bool: キャッシュ成功かどうか
        """
        if not self.client:
            return False

        try:
            data = {
                'data_hash': data_hash,
                'scenario_data': json.dumps(scenario_data),
                'updated_at': datetime.now().isoformat()
            }

            # 既存データがあるかチェック
            existing = self.client.table('scenario_cache') \
                .select('id') \
                .eq('data_hash', data_hash) \
                .execute()

            if existing.data:
                # 更新
                result = self.client.table('scenario_cache') \
                    .update(data) \
                    .eq('data_hash', data_hash) \
                    .execute()
            else:
                # 新規作成
                result = self.client.table('scenario_cache') \
                    .insert(data) \
                    .execute()

            return True

        except Exception as e:
            logger.error(f"Error caching scenario data: {e}")
            return False

    def get_cached_scenario_data(self, data_hash: str) -> Optional[List[Dict]]:
        """
        キャッシュされたシナリオデータを取得

        Args:
            data_hash (str): データのハッシュ値

        Returns:
            キャッシュされたシナリオデータ
        """
        if not self.client:
            return None

        try:
            result = self.client.table('scenario_cache') \
                .select('scenario_data') \
                .eq('data_hash', data_hash) \
                .execute()

            if result.data:
                return json.loads(result.data[0]['scenario_data'])
            return None

        except Exception as e:
            logger.error(f"Error getting cached scenario data: {e}")
            return None

    def get_stats(self) -> Dict:
        """
        統計情報を取得

        Returns:
            dict: 統計情報
        """
        if not self.client:
            return {"error": "Supabase not available"}

        try:
            # 予測ログの統計
            total_predictions = self.client.table('prediction_logs') \
                .select('id', count='exact') \
                .execute()

            # 直近の予測
            recent_predictions = self.client.table('prediction_logs') \
                .select('*') \
                .order('created_at', desc=True) \
                .limit(5) \
                .execute()

            return {
                "total_predictions": total_predictions.count if hasattr(total_predictions, 'count') else 0,
                "recent_predictions": recent_predictions.data,
                "database_status": "connected"
            }

        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {"error": str(e)}
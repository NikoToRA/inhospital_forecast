import os
import psycopg2
import pandas as pd
from psycopg2.extras import RealDictCursor
import logging
from datetime import datetime

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseService:
    def __init__(self):
        """PostgreSQLデータベース接続を初期化"""
        self.connection_string = os.environ.get('DATABASE_URL') or os.environ.get('AZURE_POSTGRESQL_CONNECTIONSTRING')

        if not self.connection_string:
            logger.warning("Database connection string not found. Database features disabled.")
            self.connection = None
        else:
            try:
                self.connection = psycopg2.connect(self.connection_string)
                logger.info("Database connection established successfully")
                self._create_tables()
            except Exception as e:
                logger.error(f"Failed to connect to database: {e}")
                self.connection = None

    def _create_tables(self):
        """必要なテーブルを作成"""
        if not self.connection:
            return

        try:
            with self.connection.cursor() as cursor:
                # 予測ログテーブル
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS prediction_logs (
                        id SERIAL PRIMARY KEY,
                        prediction_date DATE NOT NULL,
                        predicted_value FLOAT NOT NULL,
                        total_outpatient INTEGER,
                        intro_outpatient INTEGER,
                        er_patients INTEGER,
                        bed_count INTEGER,
                        public_holiday BOOLEAN,
                        day_of_week VARCHAR(10),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # シナリオデータテーブル（CSVデータのキャッシュ用）
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS scenario_data (
                        id SERIAL PRIMARY KEY,
                        total_outpatient INTEGER,
                        intro_outpatient INTEGER,
                        er_patients INTEGER,
                        bed_count INTEGER,
                        public_holiday BOOLEAN,
                        public_holiday_previous_day BOOLEAN,
                        mon BOOLEAN DEFAULT FALSE,
                        tue BOOLEAN DEFAULT FALSE,
                        wed BOOLEAN DEFAULT FALSE,
                        thu BOOLEAN DEFAULT FALSE,
                        fri BOOLEAN DEFAULT FALSE,
                        sat BOOLEAN DEFAULT FALSE,
                        sun BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # アプリケーション設定テーブル
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS app_settings (
                        id SERIAL PRIMARY KEY,
                        setting_key VARCHAR(100) UNIQUE NOT NULL,
                        setting_value TEXT,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                self.connection.commit()
                logger.info("Database tables created successfully")

        except Exception as e:
            logger.error(f"Error creating tables: {e}")
            self.connection.rollback()

    def log_prediction(self, prediction_data):
        """
        予測結果をデータベースに記録

        Args:
            prediction_data (dict): 予測データ
        """
        if not self.connection:
            return False

        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO prediction_logs (
                        prediction_date, predicted_value, total_outpatient,
                        intro_outpatient, er_patients, bed_count,
                        public_holiday, day_of_week
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    prediction_data.get('date'),
                    prediction_data.get('prediction'),
                    prediction_data.get('features', {}).get('total_outpatient'),
                    prediction_data.get('features', {}).get('intro_outpatient'),
                    prediction_data.get('features', {}).get('ER'),
                    prediction_data.get('features', {}).get('bed_count'),
                    prediction_data.get('features', {}).get('public_holiday', False),
                    prediction_data.get('day')
                ))
                self.connection.commit()
                logger.info("Prediction logged to database")
                return True

        except Exception as e:
            logger.error(f"Error logging prediction: {e}")
            self.connection.rollback()
            return False

    def get_prediction_history(self, limit=100):
        """
        予測履歴を取得

        Args:
            limit (int): 取得する件数

        Returns:
            list: 予測履歴のリスト
        """
        if not self.connection:
            return []

        try:
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT * FROM prediction_logs
                    ORDER BY created_at DESC
                    LIMIT %s
                """, (limit,))

                results = cursor.fetchall()
                return [dict(row) for row in results]

        except Exception as e:
            logger.error(f"Error fetching prediction history: {e}")
            return []

    def store_scenario_data(self, df):
        """
        シナリオデータをデータベースに保存

        Args:
            df (pd.DataFrame): シナリオデータのDataFrame
        """
        if not self.connection:
            return False

        try:
            # 既存のデータを削除
            with self.connection.cursor() as cursor:
                cursor.execute("DELETE FROM scenario_data")

            # 新しいデータを挿入
            for _, row in df.iterrows():
                with self.connection.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO scenario_data (
                            total_outpatient, intro_outpatient, er_patients,
                            bed_count, public_holiday, public_holiday_previous_day,
                            mon, tue, wed, thu, fri, sat, sun
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        int(row.get('total_outpatient', 0)),
                        int(row.get('intro_outpatient', 0)),
                        int(row.get('ER', 0)),
                        int(row.get('bed_count', 280)),
                        bool(row.get('public_holiday', False)),
                        bool(row.get('public_holiday_previous_day', False)),
                        bool(row.get('mon', False)),
                        bool(row.get('tue', False)),
                        bool(row.get('wed', False)),
                        bool(row.get('thu', False)),
                        bool(row.get('fri', False)),
                        bool(row.get('sat', False)),
                        bool(row.get('sun', False))
                    ))

            self.connection.commit()
            logger.info(f"Stored {len(df)} scenario records to database")
            return True

        except Exception as e:
            logger.error(f"Error storing scenario data: {e}")
            self.connection.rollback()
            return False

    def get_scenario_data(self):
        """
        データベースからシナリオデータを取得

        Returns:
            pd.DataFrame: シナリオデータ、またはNone
        """
        if not self.connection:
            return None

        try:
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("SELECT * FROM scenario_data ORDER BY id")
                results = cursor.fetchall()

                if not results:
                    return None

                df = pd.DataFrame([dict(row) for row in results])
                # 不要なカラムを削除
                if 'id' in df.columns:
                    df = df.drop(['id', 'created_at'], axis=1)

                logger.info(f"Retrieved {len(df)} scenario records from database")
                return df

        except Exception as e:
            logger.error(f"Error retrieving scenario data: {e}")
            return None

    def get_app_setting(self, key, default=None):
        """
        アプリケーション設定を取得

        Args:
            key (str): 設定キー
            default: デフォルト値

        Returns:
            設定値
        """
        if not self.connection:
            return default

        try:
            with self.connection.cursor() as cursor:
                cursor.execute(
                    "SELECT setting_value FROM app_settings WHERE setting_key = %s",
                    (key,)
                )
                result = cursor.fetchone()
                return result[0] if result else default

        except Exception as e:
            logger.error(f"Error getting app setting {key}: {e}")
            return default

    def set_app_setting(self, key, value):
        """
        アプリケーション設定を保存

        Args:
            key (str): 設定キー
            value: 設定値
        """
        if not self.connection:
            return False

        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO app_settings (setting_key, setting_value, updated_at)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (setting_key)
                    DO UPDATE SET setting_value = %s, updated_at = %s
                """, (key, str(value), datetime.now(), str(value), datetime.now()))

                self.connection.commit()
                return True

        except Exception as e:
            logger.error(f"Error setting app setting {key}: {e}")
            self.connection.rollback()
            return False

    def close(self):
        """データベース接続を閉じる"""
        if self.connection:
            self.connection.close()
            logger.info("Database connection closed")
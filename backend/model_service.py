import joblib
import pandas as pd
import numpy as np
from datetime import datetime
import os

class ModelService:
    def __init__(self, model_path='models/fixed_rf_model.joblib'):
        """
        モデルサービスを初期化
        """
        self.model_path = model_path
        self.model = self.load_model()
    
    def load_model(self):
        """
        モデルをロードする
        """
        try:
            model = joblib.load(self.model_path)
            print(f"モデルを正常にロードしました: {self.model_path}")
            
            # モデルの修正（必要な場合）
            for estimator in model.estimators_:
                if not hasattr(estimator, 'monotonic_cst'):
                    estimator.monotonic_cst = None
            
            return model
        except Exception as e:
            print(f"モデルのロードに失敗しました: {e}")
            # ダミーモデルを返す
            class DummyModel:
                def predict(self, X):
                    return np.zeros(len(X))
            return DummyModel()
    
    def predict(self, features):
        """
        単一のデータセットに対する予測を行う
        """
        try:
            df = pd.DataFrame([features])
            prediction = self.model.predict(df)
            return float(prediction[0])
        except Exception as e:
            print(f"予測に失敗しました: {e}")
            return 0.0
    
    def predict_batch(self, features_list):
        """
        複数のデータセットに対する予測を行う
        """
        predictions = []
        for features in features_list:
            prediction = self.predict(features)
            predictions.append(prediction)
        return predictions
    
    def get_default_scenarios(self):
        """
        デフォルトのシナリオを返す
        """
        scenarios = [
            {
                "name": "月曜日、外来患者数が多い",
                "day_of_week": "mon",
                "public_holiday": False,
                "public_holiday_previous_day": False,
                "total_outpatient": 800,
                "intro_outpatient": 30,
                "er": 20,
                "bed_count": 280
            },
            {
                "name": "火曜日、通常の外来患者数",
                "day_of_week": "tue",
                "public_holiday": False,
                "public_holiday_previous_day": False,
                "total_outpatient": 600,
                "intro_outpatient": 20,
                "er": 15,
                "bed_count": 280
            },
            {
                "name": "水曜日、外来患者数が多い",
                "day_of_week": "wed",
                "public_holiday": False,
                "public_holiday_previous_day": False,
                "total_outpatient": 750,
                "intro_outpatient": 25,
                "er": 15,
                "bed_count": 280
            },
            {
                "name": "土曜日、少ない外来患者数",
                "day_of_week": "sat",
                "public_holiday": False,
                "public_holiday_previous_day": False,
                "total_outpatient": 200,
                "intro_outpatient": 5,
                "er": 15,
                "bed_count": 280
            },
            {
                "name": "祝日",
                "day_of_week": "tue",
                "public_holiday": True,
                "public_holiday_previous_day": False,
                "total_outpatient": 100,
                "intro_outpatient": 3,
                "er": 15,
                "bed_count": 280
            }
        ]
        return scenarios
    
    def create_features_from_scenario(self, scenario):
        """
        シナリオからモデル用の特徴量を作成
        """
        # 曜日の1-hotエンコーディング
        days = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
        day_of_week = scenario.get('day_of_week', 'mon')
        day_features = {day: 1 if day == day_of_week else 0 for day in days}
        
        # 特徴量の作成
        features = {
            **day_features,
            'public_holiday': int(scenario.get('public_holiday', False)),
            'public_holiday_previous_day': int(scenario.get('public_holiday_previous_day', False)),
            'total_outpatient': int(scenario.get('total_outpatient', 500)),
            'intro_outpatient': int(scenario.get('intro_outpatient', 20)),
            'ER': int(scenario.get('er', 15)),
            'bed_count': int(scenario.get('bed_count', 280))
        }
        
        return features 
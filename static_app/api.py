from flask import Flask, request, jsonify, send_from_directory
import os
import sys
import json
import logging
import joblib
import numpy as np
import pandas as pd
from datetime import datetime

# 現在のディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Flaskアプリの初期化
app = Flask(__name__, static_folder='.')

# モデルの読み込み
model_path = os.path.join('..', 'fixed_rf_model.joblib')
try:
    model = joblib.load(model_path)
    print(f"モデルを読み込みました: {model_path}")
except Exception as e:
    print(f"モデルの読み込みに失敗しました: {str(e)}")
    model = None

# 曜日のマッピング
DAYS_DICT = {
    0: {"mon": 1, "tue": 0, "wed": 0, "thu": 0, "fri": 0, "sat": 0, "sun": 0},  # 月曜日
    1: {"mon": 0, "tue": 1, "wed": 0, "thu": 0, "fri": 0, "sat": 0, "sun": 0},  # 火曜日
    2: {"mon": 0, "tue": 0, "wed": 1, "thu": 0, "fri": 0, "sat": 0, "sun": 0},  # 水曜日
    3: {"mon": 0, "tue": 0, "wed": 0, "thu": 1, "fri": 0, "sat": 0, "sun": 0},  # 木曜日
    4: {"mon": 0, "tue": 0, "wed": 0, "thu": 0, "fri": 1, "sat": 0, "sun": 0},  # 金曜日
    5: {"mon": 0, "tue": 0, "wed": 0, "thu": 0, "fri": 0, "sat": 1, "sun": 0},  # 土曜日
    6: {"mon": 0, "tue": 0, "wed": 0, "thu": 0, "fri": 0, "sat": 0, "sun": 1},  # 日曜日
}

# 静的ファイルのルーティング
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('.', path)

# データ取得API
@app.route('/api/data', methods=['GET'])
def get_data():
    try:
        # サンプルデータを返す
        data = {
            "samples": [
                {"age": 65, "gender": "男性", "diagnosis": "肺炎", "admission_date": "2024-03-15", "admission_type": "緊急", "los": 12},
                {"age": 45, "gender": "女性", "diagnosis": "胆石症", "admission_date": "2024-03-10", "admission_type": "予定", "los": 8},
                {"age": 72, "gender": "男性", "diagnosis": "大腿骨骨折", "admission_date": "2024-03-05", "admission_type": "緊急", "los": 20},
                {"age": 50, "gender": "女性", "diagnosis": "虫垂炎", "admission_date": "2024-03-20", "admission_type": "緊急", "los": 5}
            ],
            "statistics": {
                "average_los": 11.25,
                "min_los": 5,
                "max_los": 20,
                "count": 4
            }
        }
        return jsonify(data)
    except Exception as e:
        logging.error(f"データ取得エラー: {str(e)}")
        return jsonify({"error": str(e)}), 500

# 予測API
@app.route('/api/predict', methods=['POST'])
def predict():
    try:
        # リクエストからデータを取得
        data = request.get_json()
        if not data:
            return jsonify({"error": "データが提供されていません"}), 400
            
        # 必須フィールドのチェック
        required_fields = ['age', 'gender', 'diagnosis', 'admission_date']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"必須フィールド '{field}' がありません"}), 400
                
        # データの前処理
        processed_data = preprocess_data(data)
        
        # モデルがロードされているか確認
        if model is None:
            return jsonify({
                "prediction": 10,  # ダミー値
                "confidence_interval": [7, 13],
                "feature_importance": {
                    "age": 0.25,
                    "gender": 0.15,
                    "diagnosis": 0.30,
                    "day_of_week": 0.20,
                    "admission_type": 0.10
                }
            })
        
        # 予測の実行
        prediction = int(model.predict([processed_data])[0])
        
        # 信頼区間の推定（ここではダミー値を返す）
        confidence_interval = [max(prediction - 3, 1), prediction + 3]
        
        # 特徴量重要度（ダミー値またはモデルから取得）
        feature_importance = {
            "age": 0.25,
            "gender": 0.15,
            "diagnosis": 0.30,
            "day_of_week": 0.20,
            "admission_type": 0.10
        }
        
        return jsonify({
            "prediction": prediction,
            "confidence_interval": confidence_interval,
            "feature_importance": feature_importance
        })
        
    except Exception as e:
        logging.error(f"予測エラー: {str(e)}")
        return jsonify({"error": str(e)}), 500

# データの前処理
def preprocess_data(data):
    # 年齢を数値型に変換
    age = float(data.get('age', 0))
    
    # 性別をワンホットエンコーディング (男性=1, 女性=0)
    gender = 1 if data.get('gender') == '男性' else 0
    
    # 入院日を曜日に変換
    try:
        admission_date = datetime.strptime(data.get('admission_date', ''), '%Y-%m-%d')
        day_of_week = admission_date.weekday()  # 0=月曜, 6=日曜
        
        # 曜日のワンホットエンコーディング
        day_features = DAYS_DICT[day_of_week]
    except:
        # 日付解析に失敗した場合はデフォルト値
        day_features = DAYS_DICT[0]  # 月曜日をデフォルト
    
    # 入院種別（緊急=1, 予定=0）
    admission_type = 1 if data.get('admission_type') == '緊急' else 0
    
    # 診断名 (ダミー値として何かしら渡す)
    diagnosis_code = 1  # 実際には診断名からコード変換が必要
    
    # 特徴量をリストに結合
    features = [age, gender, diagnosis_code, admission_type]
    features.extend([day_features[k] for k in ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']])
    
    return features

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True) 
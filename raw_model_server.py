#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
純粋なモデル予測サーバー
一切の介入・調整なし、モデルの生の予測結果のみ
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import joblib
import pandas as pd
import numpy as np
import warnings

# 警告を非表示
warnings.filterwarnings("ignore")

app = Flask(__name__)
CORS(app)

# グローバル変数
model = None

def load_model():
    """モデルをロード"""
    global model
    try:
        model = joblib.load('fixed_rf_model.joblib')
        print("✅ モデルロード完了")
        return True
    except Exception as e:
        print(f"❌ モデルロード失敗: {e}")
        return False

@app.route('/api/health', methods=['GET'])
def health():
    """ヘルスチェック"""
    return jsonify({
        "status": "ok",
        "model_loaded": model is not None
    })

@app.route('/api/predict_raw', methods=['POST'])
def predict_raw():
    """
    純粋なモデル予測
    受け取った特徴量をそのままモデルに渡す
    """
    try:
        if model is None:
            return jsonify({"error": "モデルが未ロード"}), 500
        
        data = request.json
        if not data:
            return jsonify({"error": "データなし"}), 400
        
        # 必要な特徴量（CSVの順序通り）
        required_features = [
            'mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun',
            'public_holiday', 'public_holiday_previous_day',
            'total_outpatient', 'intro_outpatient', 'ER', 'bed_count'
        ]
        
        # 特徴量を抽出
        features = {}
        for feature in required_features:
            if feature not in data:
                return jsonify({"error": f"特徴量 '{feature}' がありません"}), 400
            features[feature] = data[feature]
        
        # DataFrameに変換してモデルで予測
        X = pd.DataFrame([features])
        prediction = model.predict(X)[0]
        
        return jsonify({
            "prediction": float(prediction),
            "input_features": features,
            "message": "純粋なモデル出力（介入なし）"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/test_with_actual', methods=['GET'])
def test_with_actual():
    """
    実際のCSVデータを使ってテスト
    """
    try:
        if model is None:
            return jsonify({"error": "モデルが未ロード"}), 500
        
        # CSVデータを読み込み
        data = pd.read_csv('ultimate_pickup_data.csv')
        
        # 最初の5行でテスト
        results = []
        for i in range(5):
            row = data.iloc[i]
            actual_y = float(row['y'])
            
            # 特徴量を抽出
            features = row.drop(['date', 'y']).to_dict()
            X = pd.DataFrame([features])
            
            # 予測
            pred = model.predict(X)[0]
            
            results.append({
                "row": i + 1,
                "date": row['date'],
                "actual": actual_y,
                "predicted": float(pred),
                "error": float(abs(pred - actual_y)),
                "features": {k: float(v) if isinstance(v, np.integer) else v for k, v in features.items()}
            })
        
        return jsonify({
            "test_results": results,
            "message": "実データとの比較（介入なし）"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("=== 純粋なモデル予測サーバー ===")
    print("介入・調整一切なし")
    
    if not load_model():
        exit(1)
    
    print("🔍 利用可能エンドポイント:")
    print("  GET  /api/health - ヘルスチェック")
    print("  POST /api/predict_raw - 純粋な予測")
    print("  GET  /api/test_with_actual - 実データテスト")
    print()
    print("📍 サーバー: http://localhost:9000")
    
    app.run(host='0.0.0.0', port=9000, debug=False)
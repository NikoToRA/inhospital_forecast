#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
シンプルな病院入院患者数予測API
ローカルデプロイ用の最小構成
"""

from flask import Flask, request, jsonify, g
from flask_cors import CORS
import logging
from logging.handlers import RotatingFileHandler
import joblib
import pandas as pd
import numpy as np
from datetime import datetime
import time
import os
import warnings

# 警告を非表示にする（既知の互換性警告のため）
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

app = Flask(__name__)
CORS(app)  # 開発用にCORSを有効化

# --- Logging setup: rotating file + console, request/response/error tracing ---
def setup_logging(flask_app: Flask) -> None:
    try:
        log_dir = os.path.join(os.path.dirname(__file__), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        log_file_path = os.path.join(log_dir, 'simple_server.log')

        formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s - %(message)s')
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)

        file_handler = RotatingFileHandler(
            log_file_path, maxBytes=5 * 1024 * 1024, backupCount=3, encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.INFO)

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.INFO)

        if not any(isinstance(h, RotatingFileHandler) for h in root_logger.handlers):
            root_logger.addHandler(file_handler)
        if not any(isinstance(h, logging.StreamHandler) and not isinstance(h, RotatingFileHandler) for h in root_logger.handlers):
            root_logger.addHandler(console_handler)

        flask_app.logger.handlers = root_logger.handlers
        flask_app.logger.setLevel(logging.INFO)
        flask_app.logger.info('Logging initialized (simple_server)')
    except Exception as log_err:
        print(f"Failed to setup logging: {log_err}")


setup_logging(app)

@app.before_request
def _log_request():
    g.request_start_time = time.time()
    g.request_id = f"{int(g.request_start_time * 1000)}-{os.getpid()}"
    body_preview = ''
    try:
        if request.is_json:
            body_preview = str(request.get_json(silent=True))
            if body_preview and len(body_preview) > 500:
                body_preview = body_preview[:500] + '...'
    except Exception:
        body_preview = '<unparsable>'
    app.logger.info(
        f"[{g.request_id}] {request.method} {request.path} from {request.remote_addr} body={body_preview}"
    )


@app.after_request
def _log_response(response):
    try:
        duration_ms = int((time.time() - getattr(g, 'request_start_time', time.time())) * 1000)
        app.logger.info(
            f"[{getattr(g, 'request_id', '-')}] {request.method} {request.path} -> {response.status_code} in {duration_ms}ms"
        )
        response.headers['X-Request-ID'] = getattr(g, 'request_id', '')
        response.headers['X-Process-Time'] = str(duration_ms)
    except Exception:
        pass
    return response


@app.errorhandler(Exception)
def _handle_exception(e):
    app.logger.exception(f"[{getattr(g, 'request_id', '-')}] Unhandled exception: {e}")
    return jsonify({"error": str(e), "request_id": getattr(g, 'request_id', '')}), 500

# グローバル変数でモデルを保持
model = None

def load_model():
    """モデルを読み込む"""
    global model
    try:
        model = joblib.load('fixed_rf_model.joblib')
        print("✅ モデルを正常にロードしました")
        return True
    except Exception as e:
        print(f"❌ モデルのロードに失敗: {e}")
        return False

def get_day_features(date_str=None):
    """日付から曜日特徴量を取得"""
    if date_str:
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            date_obj = datetime.now()
    else:
        date_obj = datetime.now()
    
    # 曜日のone-hotエンコーディング
    weekday = date_obj.weekday()  # 0:月曜, 1:火曜, ..., 6:日曜
    days = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
    
    day_features = {}
    for i, day in enumerate(days):
        day_features[day] = 1 if i == weekday else 0
    
    return day_features, days[weekday]

@app.route('/api/health', methods=['GET'])
def health_check():
    """ヘルスチェック"""
    return jsonify({
        "status": "healthy",
        "model_loaded": model is not None,
        "current_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })

@app.route('/api/predict', methods=['POST'])
def predict():
    """予測API"""
    try:
        if model is None:
            return jsonify({"error": "モデルがロードされていません"}), 500
        
        # リクエストデータを取得
        data = request.json
        if not data:
            return jsonify({"error": "リクエストデータがありません"}), 400
        
        print(f"受信データ: {data}")
        
        # 日付から曜日特徴量を取得
        date_str = data.get('date', datetime.now().strftime('%Y-%m-%d'))
        day_features, day_name = get_day_features(date_str)
        
        # 特徴量を構築
        features = {
            **day_features,
            'public_holiday': int(data.get('public_holiday', 0)),
            'public_holiday_previous_day': int(data.get('public_holiday_previous_day', 0)),
            'total_outpatient': int(data.get('total_outpatient', 500)),
            'intro_outpatient': int(data.get('intro_outpatient', 20)),
            'ER': int(data.get('ER', 15)),
            'bed_count': int(data.get('bed_count', 280))
        }
        
        # DataFrameに変換
        df = pd.DataFrame([features])
        
        # 予測実行
        prediction = model.predict(df)
        prediction_value = float(prediction[0])
        
        # 結果を返す
        result = {
            "prediction": round(prediction_value, 2),
            "date": date_str,
            "day": day_name,
            "features_used": features,
            "model": "RandomForest"
        }
        
        print(f"予測結果: {prediction_value:.2f}人")
        return jsonify(result)
        
    except Exception as e:
        print(f"予測エラー: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/predict_batch', methods=['POST'])
def predict_batch():
    """複数の予測を一括実行"""
    try:
        if model is None:
            return jsonify({"error": "モデルがロードされていません"}), 500
        
        data = request.json
        scenarios = data.get('scenarios', [])
        
        if not scenarios:
            return jsonify({"error": "シナリオデータがありません"}), 400
        
        results = []
        for scenario in scenarios:
            # 各シナリオで予測
            day_features, day_name = get_day_features(scenario.get('date'))
            
            features = {
                **day_features,
                'public_holiday': int(scenario.get('public_holiday', 0)),
                'public_holiday_previous_day': int(scenario.get('public_holiday_previous_day', 0)),
                'total_outpatient': int(scenario.get('total_outpatient', 500)),
                'intro_outpatient': int(scenario.get('intro_outpatient', 20)),
                'ER': int(scenario.get('ER', 15)),
                'bed_count': int(scenario.get('bed_count', 280))
            }
            
            df = pd.DataFrame([features])
            prediction = model.predict(df)
            
            results.append({
                "prediction": round(float(prediction[0]), 2),
                "date": scenario.get('date', datetime.now().strftime('%Y-%m-%d')),
                "day": day_name,
                "scenario_name": scenario.get('name', f'シナリオ{len(results)+1}')
            })
        
        return jsonify({
            "predictions": results,
            "count": len(results)
        })
        
    except Exception as e:
        print(f"バッチ予測エラー: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("=== 病院入院患者数予測API ===")
    print("モデルを読み込み中...")
    
    if not load_model():
        print("❌ モデルの読み込みに失敗しました。サーバーを終了します。")
        exit(1)
    
    print("✅ サーバーを開始します")
    print("📊 API エンドポイント:")
    print("  - GET  /api/health     : ヘルスチェック") 
    print("  - POST /api/predict    : 単体予測")
    print("  - POST /api/predict_batch : 複数予測")
    print("📍 サーバーURL: http://localhost:8000")
    
    app.run(host='0.0.0.0', port=8000, debug=True)
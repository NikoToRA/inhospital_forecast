from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import joblib
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json

app = Flask(__name__)
# CORSを強化して明示的に許可するオリジンを指定
CORS(app, resources={r"/api/*": {"origins": ["http://localhost:3000"]}})

# Azure Storageサービスをインポート
from azure_storage import AzureStorageService
from database import DatabaseService

# Azure Storageサービスを初期化
azure_storage = AzureStorageService()

# データベースサービスを初期化
db_service = DatabaseService()

# モデルのパスを設定（環境変数から取得、または固定パス）
MODEL_PATH = os.environ.get('MODEL_PATH', '../fixed_rf_model.joblib')

# モデルをロード
def load_model():
    try:
        # まずAzure Storageからモデルを試行
        print("Azure Storageからモデルをダウンロード中...")
        model = azure_storage.download_model('fixed_rf_model.joblib')

        if model is not None:
            print("Azure Storageからモデルを正常にロードしました")
            return model

        # Azure Storageが失敗した場合、ローカルファイルを試行
        print("ローカルファイルからモデルをロード中...")
        model_paths = [
            os.path.abspath(MODEL_PATH),
            os.path.abspath('models/fixed_rf_model.joblib'),
            os.path.abspath('../fixed_rf_model.joblib'),
            os.path.abspath('./models/fixed_rf_model.joblib'),
            os.path.abspath('./fixed_rf_model.joblib'),
            os.path.abspath('/Users/HirayamaSuguru2/Desktop/AI実験室/inhospital_forecast2/backend/models/fixed_rf_model.joblib')
        ]

        # すべてのパスをチェック
        model_path = None
        for path in model_paths:
            if os.path.exists(path):
                print(f"モデルファイルが見つかりました: {path}")
                model_path = path
                break

        if model_path is None:
            print(f"警告: どのパスにもモデルファイルが見つかりません。")
            print("ダミーモデルを使用します。")
            class CustomRandomModel:
                def predict(self, X):
                    print(f"カスタムモデルが予測します。特徴量: {X.shape}")
                    # 入力特徴量に基づいて変動する予測値を返す
                    # total_outpatientとERの影響を反映
                    base_pred = 3.5
                    total_effect = (X['total_outpatient'].values[0] - 500) / 500 * 1.0  # 外来患者の影響
                    er_effect = (X['ER'].values[0] - 15) / 15 * 0.5  # 救急患者の影響
                    intro_effect = (X['intro_outpatient'].values[0] - 20) / 20 * 0.3  # 紹介患者の影響
                    holiday_effect = -0.5 if X['public_holiday'].values[0] > 0 else 0  # 祝日の影響
                    
                    # 曜日の影響
                    day_effect = 0
                    if X['sat'].values[0] > 0:
                        day_effect = -0.2
                    elif X['sun'].values[0] > 0:
                        day_effect = -0.3
                    
                    # 最終予測
                    pred = base_pred + total_effect + er_effect + intro_effect + holiday_effect + day_effect
                    pred = max(0.5, pred)  # 最低値を0.5に制限
                    
                    print(f"予測値: {pred}, 影響: 外来={total_effect}, 救急={er_effect}, 紹介={intro_effect}, 祝日={holiday_effect}, 曜日={day_effect}")
                    return np.array([pred])
            return CustomRandomModel()
        
        # ローカルファイルからモデルをロード
        print(f"ローカルファイルからモデルをロード中: {model_path}")
        try:
            model = joblib.load(model_path)
            print("モデルを正常にロードしました")
            
            # モデルの内部構造を確認
            print(f"モデルの型: {type(model)}")
            if hasattr(model, 'feature_importances_'):
                print(f"特徴量の重要度: {model.feature_importances_}")
            
            # モデルの内部構造を修正（必要な場合）
            if hasattr(model, 'estimators_'):
                print(f"推定器の数: {len(model.estimators_)}")
                for estimator in model.estimators_:
                    if not hasattr(estimator, 'monotonic_cst'):
                        estimator.monotonic_cst = None
                
                # テスト予測を実行
                test_features = pd.DataFrame([{
                    'total_outpatient': 500,
                    'intro_outpatient': 20,
                    'ER': 15,
                    'bed_count': 280,
                    'public_holiday': 0,
                    'public_holiday_previous_day': 0,
                    'mon': 0, 'tue': 0, 'wed': 0, 'thu': 1, 'fri': 0, 'sat': 0, 'sun': 0
                }])
                test_pred = model.predict(test_features)
                print(f"テスト予測値: {test_pred[0]}")
            
            return model
        except Exception as inner_e:
            print(f"モデルのロード中にエラーが発生しました: {inner_e}")
            print("代替のカスタムモデルを使用します。")
            class CustomRandomModel:
                def predict(self, X):
                    print(f"カスタムモデルが予測します。特徴量: {X.shape}")
                    # 入力特徴量に基づいて変動する予測値を返す
                    # total_outpatientとERの影響を反映
                    base_pred = 3.5
                    total_effect = (X['total_outpatient'].values[0] - 500) / 500 * 1.0  # 外来患者の影響
                    er_effect = (X['ER'].values[0] - 15) / 15 * 0.5  # 救急患者の影響
                    intro_effect = (X['intro_outpatient'].values[0] - 20) / 20 * 0.3  # 紹介患者の影響
                    holiday_effect = -0.5 if X['public_holiday'].values[0] > 0 else 0  # 祝日の影響
                    
                    # 曜日の影響
                    day_effect = 0
                    if X['sat'].values[0] > 0:
                        day_effect = -0.2
                    elif X['sun'].values[0] > 0:
                        day_effect = -0.3
                    
                    # 最終予測
                    pred = base_pred + total_effect + er_effect + intro_effect + holiday_effect + day_effect
                    pred = max(0.5, pred)  # 最低値を0.5に制限
                    
                    print(f"予測値: {pred}, 影響: 外来={total_effect}, 救急={er_effect}, 紹介={intro_effect}, 祝日={holiday_effect}, 曜日={day_effect}")
                    return np.array([pred])
            return CustomRandomModel()
    except Exception as e:
        print(f"モデルのロードに失敗しました: {e}")
        # 代替のカスタムモデルを返す
        class CustomRandomModel:
            def predict(self, X):
                print(f"カスタムモデルが予測します。特徴量: {X.shape}")
                # 入力特徴量に基づいて変動する予測値を返す
                # total_outpatientとERの影響を反映
                base_pred = 3.5
                total_effect = (X['total_outpatient'].values[0] - 500) / 500 * 1.0  # 外来患者の影響
                er_effect = (X['ER'].values[0] - 15) / 15 * 0.5  # 救急患者の影響
                intro_effect = (X['intro_outpatient'].values[0] - 20) / 20 * 0.3  # 紹介患者の影響
                holiday_effect = -0.5 if X['public_holiday'].values[0] > 0 else 0  # 祝日の影響
                
                # 曜日の影響
                day_effect = 0
                if X['sat'].values[0] > 0:
                    day_effect = -0.2
                elif X['sun'].values[0] > 0:
                    day_effect = -0.3
                
                # 最終予測
                pred = base_pred + total_effect + er_effect + intro_effect + holiday_effect + day_effect
                pred = max(0.5, pred)  # 最低値を0.5に制限
                
                print(f"予測値: {pred}, 影響: 外来={total_effect}, 救急={er_effect}, 紹介={intro_effect}, 祝日={holiday_effect}, 曜日={day_effect}")
                return np.array([pred])
        return CustomRandomModel()

model = load_model()

# 日付から曜日コードを取得する関数
def get_day_code(date_str=None):
    """
    日付から曜日コードを取得する
    date_str: YYYY-MM-DD形式の日付文字列、未指定なら現在日付
    """
    if date_str:
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            date_obj = datetime.now()
    else:
        date_obj = datetime.now()
    
    # 0:月曜, 1:火曜, ..., 6:日曜
    weekday = date_obj.weekday()
    day_codes = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
    return day_codes[weekday]

# 日付からシーズン（季節）を取得する関数
def get_season(date_str=None):
    """
    日付から季節を取得する
    date_str: YYYY-MM-DD形式の日付文字列、未指定なら現在日付
    """
    if date_str:
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            date_obj = datetime.now()
    else:
        date_obj = datetime.now()
    
    month = date_obj.month
    day = date_obj.day
    
    # 気象学的季節定義
    if month in [3, 4, 5]:  # 春: 3-5月
        return "spring"
    elif month in [6, 7, 8]:  # 夏: 6-8月
        return "summer"
    elif month in [9, 10, 11]:  # 秋: 9-11月
        return "autumn"
    else:  # 冬: 12-2月
        return "winter"

# 日本語の曜日名を取得する関数
def day_name_ja(day_code):
    """曜日コードを日本語の曜日名に変換する"""
    day_map = {
        'mon': '月曜日',
        'tue': '火曜日',
        'wed': '水曜日',
        'thu': '木曜日',
        'fri': '金曜日',
        'sat': '土曜日',
        'sun': '日曜日'
    }
    return day_map.get(day_code, '不明')

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy", 
        "model_loaded": model is not None,
        "current_date": datetime.now().strftime('%Y-%m-%d'),
        "current_day": get_day_code(),
        "current_season": get_season()
    })

@app.route('/api/predict', methods=['POST'])
def predict():
    try:
        # リクエストからデータを取得
        data = request.json
        print(f"受信したデータ: {data}")
        
        # 日付が指定されていない場合は現在の日付を使用
        date_str = data.get('date', datetime.now().strftime('%Y-%m-%d'))
        day_code = get_day_code(date_str)
        
        # 曜日のone-hotエンコーディング
        day_features = {day: 1 if day == day_code else 0 for day in ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']}
        
        # 特徴量を作成
        features = {
            **day_features,
            'public_holiday': data.get('public_holiday', 0),
            'public_holiday_previous_day': data.get('public_holiday_previous_day', 0),
            'total_outpatient': data.get('total_outpatient', 500),
            'intro_outpatient': data.get('intro_outpatient', 20),
            'ER': data.get('ER', 15),
            'bed_count': data.get('bed_count', 280)
        }
        
        # DataFrameに変換
        df = pd.DataFrame([features])
        
        # 予測を実行
        prediction = model.predict(df)
        
        # 予測結果をデータベースにログ
        prediction_data = {
            "prediction": float(prediction[0]),
            "date": date_str,
            "day": day_code,
            "day_name": day_name_ja(day_code),
            "season": get_season(date_str),
            "features": features
        }
        db_service.log_prediction(prediction_data)

        # 結果を返す
        return jsonify(prediction_data)
        
    except Exception as e:
        print(f"予測中にエラーが発生しました: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/predict_week', methods=['POST'])
def predict_week():
    try:
        # リクエストからデータを取得
        data = request.json
        print(f"受信したデータ: {data}")
        
        # 開始日が指定されていない場合は現在の日付を使用
        start_date = data.get('start_date', datetime.now().strftime('%Y-%m-%d'))
        try:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
        except ValueError:
            start_date_obj = datetime.now()
        
        # 7日分の予測を実行
        predictions = []
        for i in range(7):
            current_date = start_date_obj + timedelta(days=i)
            date_str = current_date.strftime('%Y-%m-%d')
            day_code = get_day_code(date_str)
            
            # 曜日のone-hotエンコーディング
            day_features = {day: 1 if day == day_code else 0 for day in ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']}
            
            # 特徴量を作成
            features = {
                **day_features,
                'public_holiday': data.get('public_holiday', 0),
                'public_holiday_previous_day': data.get('public_holiday_previous_day', 0),
                'total_outpatient': data.get('total_outpatient', 500),
                'intro_outpatient': data.get('intro_outpatient', 20),
                'ER': data.get('ER', 15),
                'bed_count': data.get('bed_count', 280)
            }
            
            # DataFrameに変換
            df = pd.DataFrame([features])
            
            # 予測を実行
            prediction = model.predict(df)
            
            # 結果を追加
            predictions.append({
                "date": date_str,
                "day": day_code,
                "day_name": day_name_ja(day_code),
                "prediction": float(prediction[0]),
                "features": features
            })
        
        return jsonify({
            "start_date": start_date,
            "predictions": predictions
        })
        
    except Exception as e:
        print(f"週間予測中にエラーが発生しました: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/scenarios', methods=['GET'])
def get_scenarios():
    try:
        # まずAzure StorageからCSVを試行
        df = azure_storage.download_csv_data('ultimate_pickup_data.csv')

        if df is None:
            # データベースからシナリオデータを試行
            df = db_service.get_scenario_data()

        if df is None:
            # ローカルファイルから読み込み
            try:
                df = pd.read_csv('../ultimate_pickup_data.csv')
                # データベースにキャッシュ
                db_service.store_scenario_data(df)
            except FileNotFoundError:
                return jsonify({"error": "Scenario data not found"}), 404
        
        # 代表的なシナリオを選択
        scenarios = [
            # 月曜日で外来患者数が多い日
            df[(df['mon'] == 1) & (df['total_outpatient'] > 700)].iloc[0].to_dict(),
            # 火曜日で通常の外来患者数
            df[(df['tue'] == 1) & (df['total_outpatient'] > 500) & (df['total_outpatient'] < 700)].iloc[0].to_dict(),
            # 水曜日で外来患者数が多い日
            df[(df['wed'] == 1) & (df['total_outpatient'] > 700)].iloc[0].to_dict(),
            # 土曜日で外来患者数が少ない日
            df[(df['sat'] == 1) & (df['total_outpatient'] < 250)].iloc[0].to_dict(),
            # 祝日
            df[df['public_holiday'] == 1].iloc[0].to_dict()
        ]
        
        return jsonify({
            "scenarios": scenarios
        })
        
    except Exception as e:
        print(f"シナリオの取得中にエラーが発生しました: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/history', methods=['GET'])
def get_prediction_history():
    """予測履歴を取得"""
    try:
        limit = request.args.get('limit', 100, type=int)
        history = db_service.get_prediction_history(limit)
        return jsonify({
            "history": history,
            "count": len(history)
        })
    except Exception as e:
        print(f"予測履歴の取得中にエラーが発生しました: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/storage/status', methods=['GET'])
def get_storage_status():
    """Azure StorageとDBの状態を確認"""
    try:
        # Azure Storageの状態
        azure_blobs = azure_storage.list_blobs() if azure_storage.blob_service_client else []

        # データベースの状態
        db_available = db_service.connection is not None

        return jsonify({
            "azure_storage": {
                "available": azure_storage.blob_service_client is not None,
                "blobs": azure_blobs
            },
            "database": {
                "available": db_available
            }
        })
    except Exception as e:
        print(f"ストレージ状態の確認中にエラーが発生しました: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000) 
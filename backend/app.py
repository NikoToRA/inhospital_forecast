from flask import Flask, request, jsonify, g
from flask_cors import CORS
import os
import joblib
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import logging
from logging.handlers import RotatingFileHandler
import time
# 祝日ライブラリ（任意）
try:
    import jpholiday  # type: ignore
    HAS_JPHOLIDAY = True
except Exception:
    HAS_JPHOLIDAY = False

app = Flask(__name__)
# --- Logging setup: rotating file + console, request/response/error tracing ---
def setup_logging(flask_app: Flask) -> None:
    try:
        log_dir = os.path.join(os.path.dirname(__file__), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        log_file_path = os.path.join(log_dir, 'app.log')

        formatter = logging.Formatter(
            '%(asctime)s %(levelname)s %(name)s - %(message)s'
        )

        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)

        # File handler (rotating)
        file_handler = RotatingFileHandler(
            log_file_path, maxBytes=5 * 1024 * 1024, backupCount=3, encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.INFO)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.INFO)

        # Avoid duplicate handler registration when reloaded
        if not any(isinstance(h, RotatingFileHandler) for h in root_logger.handlers):
            root_logger.addHandler(file_handler)
        if not any(isinstance(h, logging.StreamHandler) and not isinstance(h, RotatingFileHandler) for h in root_logger.handlers):
            root_logger.addHandler(console_handler)

        flask_app.logger.handlers = root_logger.handlers
        flask_app.logger.setLevel(logging.INFO)
        flask_app.logger.info('Logging initialized')
    except Exception as log_err:
        # As a last resort, print to stdout; do not raise
        print(f"Failed to setup logging: {log_err}")


setup_logging(app)

@app.before_request
def _log_request():
    g.request_start_time = time.time()
    g.request_id = f"{int(g.request_start_time * 1000)}-{os.getpid()}"
    body_preview = ''
    try:
        if request.is_json:
            body_preview = json.dumps(request.get_json(silent=True))
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
# CORS設定 - 環境変数から取得、またはデフォルト
cors_origins = os.environ.get('CORS_ORIGINS', 'http://localhost:3000,http://localhost:3001,http://localhost:3002,http://127.0.0.1:3000,http://127.0.0.1:3001,http://127.0.0.1:3002').split(',')
# すべてのルートにCORSを適用（ルートルートと全APIエンドポイント）
CORS(app, resources={
    r"/*": {"origins": "*"},
    r"/api/*": {"origins": "*"}
})

# Supabase設定
from supabase_client import SupabaseService

# Supabaseサービスを初期化
supabase_service = SupabaseService()

# モデルのパスを設定（環境変数から取得、または固定パス）
RF_MODEL_PATH = os.environ.get('RF_MODEL_PATH', '../fixed_rf_model.joblib')
PROPHET_MODEL_PATH = os.environ.get('PROPHET_MODEL_PATH', '../prophet_model.joblib')

# RandomForestモデルをロード
def load_rf_model():
    try:
        # ローカルファイルからモデルをロード
        model_paths = [
            os.path.abspath(RF_MODEL_PATH),
            os.path.abspath('models/fixed_rf_model.joblib'),
            os.path.abspath('../fixed_rf_model.joblib'),
            os.path.abspath('./models/fixed_rf_model.joblib'),
            os.path.abspath('./fixed_rf_model.joblib')
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

# Prophetモデルをロード
def load_prophet_model():
    try:
        # Prophet用のパスをチェック
        prophet_paths = [
            os.path.abspath(PROPHET_MODEL_PATH),
            os.path.abspath('../prophet_model.joblib'),
            os.path.abspath('./prophet_model.joblib'),
            os.path.abspath('models/prophet_model.joblib')
        ]

        for path in prophet_paths:
            if os.path.exists(path):
                print(f"Prophetモデルファイルが見つかりました: {path}")
                return joblib.load(path)

        print("警告: Prophetモデルが見つかりません。")
        return None
    except Exception as e:
        print(f"Prophetモデルのロードに失敗しました: {e}")
        return None

# 両方のモデルをロード
rf_model = load_rf_model()
prophet_model = load_prophet_model()

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

# 日本の祝日チェック関数（簡易版）
def is_japanese_holiday(date_str):
    """日付が日本の祝日かどうかをチェック。
    jpholiday が使える場合はそれを使用し、なければ簡易版にフォールバック。
    """
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
    except Exception:
        return False

    if HAS_JPHOLIDAY:
        try:
            return jpholiday.is_holiday(date_obj)
        except Exception:
            pass

    # フォールバック（2025年の主要祝日）
    holidays_2025 = {
        '2025-01-01', '2025-01-13', '2025-02-11', '2025-03-20',
        '2025-04-29', '2025-05-03', '2025-05-04', '2025-05-05',
        '2025-07-21', '2025-08-11', '2025-09-15', '2025-09-23',
        '2025-10-13', '2025-11-03', '2025-11-23'
    }
    return date_str in holidays_2025

def is_previous_day_holiday(date_str):
    """前日が日本の祝日かどうかをチェック"""
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        previous_day = date_obj - timedelta(days=1)
        prev_date_str = previous_day.strftime('%Y-%m-%d')
        return is_japanese_holiday(prev_date_str)
    except:
        return False

# ルートルート - デバッグ情報を返す
@app.route('/', methods=['GET'])
def root():
    """ルートエンドポイント - システム情報とデバッグ情報を返す"""
    return jsonify({
        "message": "Hospital Forecast API Backend",
        "version": "1.0.0",
        "status": "running",
        "available_endpoints": {
            "health": "/api/health",
            "predict": "/api/predict (POST)",
            "predict_week": "/api/predict_week (POST)",
            "predict_month": "/api/predict_month (POST)",
            "scenarios": "/api/scenarios",
            "status": "/api/status",
            "history": "/api/history",
            "stats": "/api/stats"
        },
        "models_loaded": {
            "randomforest": rf_model is not None,
            "prophet": prophet_model is not None
        },
        "timestamp": datetime.now().isoformat(),
        "debug": True
    })

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy",
        "rf_model_loaded": rf_model is not None,
        "prophet_model_loaded": prophet_model is not None,
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

        # 自動的に日本の祝日をチェック
        is_holiday = is_japanese_holiday(date_str)
        is_prev_holiday = is_previous_day_holiday(date_str)

        # 曜日のone-hotエンコーディング
        day_features = {day: 1 if day == day_code else 0 for day in ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']}

        # 特徴量を作成（祝日は自動設定）
        features = {
            **day_features,
            'public_holiday': 1 if is_holiday else 0,
            'public_holiday_previous_day': 1 if is_prev_holiday else 0,
            'total_outpatient': data.get('total_outpatient', 500),
            'intro_outpatient': data.get('intro_outpatient', 20),
            'ER': data.get('ER', 15),
            'bed_count': data.get('bed_count', 280)
        }
        
        # DataFrameに変換
        df = pd.DataFrame([features])
        
        # RandomForestモデルで予測を実行
        prediction = rf_model.predict(df)
        
        # 予測結果を準備
        prediction_result = {
            "prediction": round(float(prediction[0]), 1),
            "date": date_str,
            "day": day_code,
            "day_name": day_name_ja(day_code),
            "season": get_season(date_str),
            "features": features
        }

        # Supabaseにログ記録（エラーがあっても処理は継続）
        try:
            supabase_service.log_prediction(prediction_result)
        except Exception as log_error:
            print(f"Supabaseログ記録エラー: {log_error}")

        # 結果を返す
        return jsonify(prediction_result)
        
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
        
        # 7日分の予測を実行し、フロントで必要な情報を整形
        predictions = []

        # 入力の基準値
        base_outpatient = data.get('total_outpatient', 500)
        base_intro = data.get('intro_outpatient', 20)
        base_er = data.get('ER', 15)
        bed_count = data.get('bed_count', 280)
        use_prophet = bool(data.get('use_prophet', False))

        if use_prophet and prophet_model is not None:
            # Prophetで時系列予測
            future_dates = pd.date_range(start=start_date_obj, periods=7, freq='D')
            future_df = pd.DataFrame({'ds': future_dates})
            forecast = prophet_model.predict(future_df)

            for i, (_, row) in enumerate(forecast.iterrows()):
                current_date = start_date_obj + timedelta(days=i)
                date_str = current_date.strftime('%Y-%m-%d')
                day_code = get_day_code(date_str)

                # 表示用の特徴量（週末・祝日で調整）
                is_weekend = day_code in ['sat', 'sun']
                is_holiday = is_japanese_holiday(date_str)
                if is_weekend or is_holiday:
                    adjusted_outpatient = int(base_outpatient * 0.3)
                    adjusted_intro = int(base_intro * 0.2)
                    adjusted_er = int(base_er * 1.2)
                else:
                    adjusted_outpatient = base_outpatient
                    adjusted_intro = base_intro
                    adjusted_er = base_er

                predictions.append({
                    "date": date_str,
                    "day": day_code,
                    "day_label": ['月', '火', '水', '木', '金', '土', '日'][current_date.weekday()],
                    "day_name": day_name_ja(day_code),
                    "prediction": round(max(0, float(row['yhat'])), 1),
                    "prediction_lower": round(max(0, float(row['yhat_lower'])), 1),
                    "prediction_upper": round(max(0, float(row['yhat_upper'])), 1),
                    "is_weekend": is_weekend,
                    "is_holiday": is_holiday,
                    "features": {
                        'total_outpatient': adjusted_outpatient,
                        'intro_outpatient': adjusted_intro,
                        'ER': adjusted_er,
                        'bed_count': bed_count,
                        'public_holiday': 1 if is_holiday else 0
                    },
                    "model_used": "prophet"
                })
        else:
            # RandomForestで予測（デフォルト）
            for i in range(7):
                current_date = start_date_obj + timedelta(days=i)
                date_str = current_date.strftime('%Y-%m-%d')
                day_code = get_day_code(date_str)

                # 曜日のone-hotエンコーディング
                day_features = {day: 1 if day == day_code else 0 for day in ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']}

                # 週末・祝日で表示用の特徴量を調整
                is_weekend = day_code in ['sat', 'sun']
                is_holiday = is_japanese_holiday(date_str)
                if is_weekend or is_holiday:
                    adjusted_outpatient = int(base_outpatient * 0.3)
                    adjusted_intro = int(base_intro * 0.2)
                    adjusted_er = int(base_er * 1.2)
                else:
                    adjusted_outpatient = base_outpatient
                    adjusted_intro = base_intro
                    adjusted_er = base_er

                # 予測用の特徴量を作成
                features = {
                    **day_features,
                    'public_holiday': 1 if is_holiday else 0,
                    'public_holiday_previous_day': 1 if is_previous_day_holiday(date_str) else 0,
                    'total_outpatient': adjusted_outpatient,
                    'intro_outpatient': adjusted_intro,
                    'ER': adjusted_er,
                    'bed_count': bed_count
                }

                # DataFrameに変換
                df = pd.DataFrame([features])

                # RandomForestで予測
                prediction = rf_model.predict(df)

                # 結果を追加
                predictions.append({
                    "date": date_str,
                    "day": day_code,
                    "day_label": ['月', '火', '水', '木', '金', '土', '日'][current_date.weekday()],
                    "day_name": day_name_ja(day_code),
                    "prediction": round(float(prediction[0]), 1),
                    "is_weekend": is_weekend,
                    "is_holiday": is_holiday,
                    "features": {
                        'total_outpatient': adjusted_outpatient,
                        'intro_outpatient': adjusted_intro,
                        'ER': adjusted_er,
                        'bed_count': bed_count,
                        'public_holiday': 1 if is_holiday else 0
                    },
                    "model_used": "randomforest"
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
        # ローカルファイルからCSVを読み込み
        try:
            df = pd.read_csv('../ultimate_pickup_data.csv')
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

@app.route('/api/status', methods=['GET'])
def get_status():
    """アプリケーションの状態を確認"""
    try:
        return jsonify({
            "local_files": {
                "model_exists": os.path.exists("../fixed_rf_model.joblib"),
                "data_exists": os.path.exists("../ultimate_pickup_data.csv")
            },
            "rf_model_loaded": rf_model is not None,
                "prophet_model_loaded": prophet_model is not None,
            "supabase_available": supabase_service.is_available(),
            "app_version": "1.0.0"
        })
    except Exception as e:
        print(f"状態確認中にエラーが発生しました: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/history', methods=['GET'])
def get_prediction_history():
    """予測履歴を取得"""
    try:
        limit = request.args.get('limit', 100, type=int)
        history = supabase_service.get_prediction_history(limit)
        return jsonify({
            "history": history,
            "count": len(history)
        })
    except Exception as e:
        print(f"予測履歴の取得中にエラーが発生しました: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """統計情報を取得"""
    try:
        stats = supabase_service.get_stats()
        return jsonify(stats)
    except Exception as e:
        print(f"統計情報の取得中にエラーが発生しました: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/predict_month', methods=['POST'])
def predict_month():
    """月間予測を実行"""
    try:
        # リクエストからデータを取得
        data = request.json
        print(f"受信したデータ: {data}")

        # 年月が指定されていない場合は現在の月を使用
        year = data.get('year', datetime.now().year)
        month = data.get('month', datetime.now().month)

        # 月の初日と最終日を計算
        from calendar import monthrange
        start_date = datetime(year, month, 1)
        _, last_day = monthrange(year, month)

        # 月全体の予測を実行
        predictions = []
        use_prophet = bool(data.get('use_prophet', False))

        if use_prophet and prophet_model is not None:
            # Prophetで月全体を時系列予測
            month_dates = pd.date_range(start=start_date, periods=last_day, freq='D')
            future_df = pd.DataFrame({'ds': month_dates})
            forecast = prophet_model.predict(future_df)

            for i, (_, row) in enumerate(forecast.iterrows()):
                current_date = datetime(year, month, i + 1)
                date_str = current_date.strftime('%Y-%m-%d')
                day_code = get_day_code(date_str)
                is_weekend = day_code in ['sat', 'sun']
                is_holiday = is_japanese_holiday(date_str)

                # 表示用の特徴量（週末・祝日で調整）
                base_outpatient = data.get('total_outpatient', 500)
                base_intro = data.get('intro_outpatient', 20)
                base_er = data.get('ER', 15)
                bed_count = data.get('bed_count', 280)
                if is_weekend or is_holiday:
                    adjusted_outpatient = int(base_outpatient * 0.3)
                    adjusted_intro = int(base_intro * 0.2)
                    adjusted_er = int(base_er * 1.2)
                else:
                    adjusted_outpatient = base_outpatient
                    adjusted_intro = base_intro
                    adjusted_er = base_er

                predictions.append({
                    'date': date_str,
                    'day': i + 1,
                    'day_of_week': current_date.weekday(),
                    'day_label': ['月', '火', '水', '木', '金', '土', '日'][current_date.weekday()],
                    'prediction': round(max(0, float(row['yhat'])), 1),
                    'prediction_lower': round(max(0, float(row['yhat_lower'])), 1),
                    'prediction_upper': round(max(0, float(row['yhat_upper'])), 1),
                    'is_weekend': is_weekend,
                    'is_holiday': is_holiday,
                    'model_used': 'prophet',
                    'features': {
                        'total_outpatient': adjusted_outpatient,
                        'intro_outpatient': adjusted_intro,
                        'ER': adjusted_er,
                        'bed_count': bed_count,
                        'public_holiday': 1 if is_holiday else 0
                    }
                })
        else:
            # RandomForestで月全体を予測（デフォルト）
            for day in range(1, last_day + 1):
                current_date = datetime(year, month, day)
                date_str = current_date.strftime('%Y-%m-%d')
                day_code = get_day_code(date_str)

                # 曜日のone-hotエンコーディング
                day_features = {day: 1 if day == day_code else 0 for day in ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']}

                # 基本データ（土日祝日は外来患者数を調整）
                base_outpatient = data.get('total_outpatient', 500)
                base_intro = data.get('intro_outpatient', 20)
                base_er = data.get('ER', 15)

                # 土日祝日の調整
                is_weekend = day_code in ['sat', 'sun']
                # 祝日判定は日付ベースで統一（週次と揃える）
                is_holiday = is_japanese_holiday(date_str)

                if is_weekend or is_holiday:
                    adjusted_outpatient = int(base_outpatient * 0.3)
                    adjusted_intro = int(base_intro * 0.2)
                    adjusted_er = int(base_er * 1.2)
                else:
                    adjusted_outpatient = base_outpatient
                    adjusted_intro = base_intro
                    adjusted_er = base_er

                # 特徴量を作成
                features = {
                    **day_features,
                    'public_holiday': 1 if is_holiday else 0,
                    'public_holiday_previous_day': 1 if is_previous_day_holiday(date_str) else 0,
                    'total_outpatient': adjusted_outpatient,
                    'intro_outpatient': adjusted_intro,
                    'ER': adjusted_er,
                    'bed_count': data.get('bed_count', 280)
                }

                # DataFrameに変換
                features_df = pd.DataFrame([features])

                # RandomForestで予測
                prediction_value = rf_model.predict(features_df)[0]
                prediction_rounded = round(float(prediction_value), 1)

                # 結果に追加
                predictions.append({
                    'date': date_str,
                    'day': day,
                    'day_of_week': current_date.weekday(),
                    'day_label': ['月', '火', '水', '木', '金', '土', '日'][current_date.weekday()],
                    'prediction': prediction_rounded,
                    'is_weekend': is_weekend,
                    'is_holiday': is_holiday,
                    'model_used': 'randomforest',
                    'features': {
                        'total_outpatient': adjusted_outpatient,
                        'intro_outpatient': adjusted_intro,
                        'ER': adjusted_er,
                        'bed_count': data.get('bed_count', 280),
                        'public_holiday': 1 if is_holiday else 0
                    }
                })

        # 結果をまとめる
        month_result = {
            'year': year,
            'month': month,
            'month_name': f"{year}年{month}月",
            'predictions': predictions,
            'statistics': {
                'total_days': len(predictions),
                'max_prediction': max(p['prediction'] for p in predictions),
                'min_prediction': min(p['prediction'] for p in predictions),
                'avg_prediction': round(sum(p['prediction'] for p in predictions) / len(predictions), 1),
                'weekday_avg': round(sum(p['prediction'] for p in predictions if not p['is_weekend']) / len([p for p in predictions if not p['is_weekend']]), 1),
                'weekend_avg': round(sum(p['prediction'] for p in predictions if p['is_weekend']) / len([p for p in predictions if p['is_weekend']]), 1) if any(p['is_weekend'] for p in predictions) else 0
            }
        }

        # Supabaseに結果をログ
        if supabase_service.is_available():
            try:
                for prediction in predictions:
                    log_data = {
                        'date': prediction['date'],
                        'prediction': prediction['prediction'],
                        'features': prediction['features']
                    }
                    supabase_service.log_prediction(log_data)
            except Exception as e:
                print(f"Supabaseログ記録エラー: {e}")

        # 結果を返す
        return jsonify(month_result)

    except Exception as e:
        print(f"月間予測中にエラーが発生しました: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    debug = os.environ.get('FLASK_ENV') != 'production'
    app.run(debug=debug, host='0.0.0.0', port=port) 

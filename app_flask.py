from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import joblib
import os
import calendar
import jpholiday

# Flaskアプリケーションの初期化
app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app)  # CORS対応

# 日付・曜日の定義
DAYS_OF_WEEK = ["月曜日", "火曜日", "水曜日", "木曜日", "金曜日", "土曜日", "日曜日"]
DAYS_DICT = {
    "月曜日": {"mon": 1, "tue": 0, "wed": 0, "thu": 0, "fri": 0, "sat": 0, "sun": 0},
    "火曜日": {"mon": 0, "tue": 1, "wed": 0, "thu": 0, "fri": 0, "sat": 0, "sun": 0},
    "水曜日": {"mon": 0, "tue": 0, "wed": 1, "thu": 0, "fri": 0, "sat": 0, "sun": 0},
    "木曜日": {"mon": 0, "tue": 0, "wed": 0, "thu": 1, "fri": 0, "sat": 0, "sun": 0},
    "金曜日": {"mon": 0, "tue": 0, "wed": 0, "thu": 0, "fri": 1, "sat": 0, "sun": 0},
    "土曜日": {"mon": 0, "tue": 0, "wed": 0, "thu": 0, "fri": 0, "sat": 1, "sun": 0},
    "日曜日": {"mon": 0, "tue": 0, "wed": 0, "thu": 0, "fri": 0, "sat": 0, "sun": 1},
}

# 曜日と数値のマッピング（0=月曜日、1=火曜日、...6=日曜日）
WEEKDAY_MAP = {
    0: "月曜日", 
    1: "火曜日", 
    2: "水曜日", 
    3: "木曜日", 
    4: "金曜日", 
    5: "土曜日", 
    6: "日曜日"
}

# 日付から曜日を取得する関数
def get_day_of_week_from_date(date):
    # 日本の曜日（0が月曜日）
    weekday = date.weekday()
    return WEEKDAY_MAP[weekday]

# 日付が祝日かどうか判定する関数
def is_holiday(date):
    # 祝日のみ True (土日は祝日と見なさない)
    return jpholiday.is_holiday(date)

# 前日が祝日かどうか判定する関数
def is_previous_day_holiday(date):
    previous_day = date - timedelta(days=1)
    return is_holiday(previous_day)

# モデルを読み込む関数
def load_model():
    try:
        # モデルを読み込む
        model = joblib.load('fixed_rf_model.joblib')
        return model
    except Exception as e:
        print(f"モデルの読み込みに失敗しました: {e}")
        # ダミーモデルを作成
        class DummyModel:
            def predict(self, X):
                return np.zeros(len(X))
        return DummyModel()

# 予測を実行する関数
def predict_admission(model, input_data):
    try:
        # 予測を実行
        prediction = model.predict(input_data)
        return prediction[0]
    except Exception as e:
        print(f"予測に失敗しました: {e}")
        return 0

# 複数日の予測を行う関数
def predict_multiple_days(model, base_data, start_date, num_days=7):
    """
    指定された日数分の予測を行う
    """
    # 予測結果を格納するリスト
    forecasts = []
    
    # 初期日付と曜日
    current_date = start_date
    
    # num_days分の予測を行う
    for i in range(num_days):
        # 現在の日付を取得
        day_name = get_day_of_week_from_date(current_date)
        
        # 曜日のone-hotエンコーディングを取得
        day_encoding = DAYS_DICT[day_name]
        
        # 祝日かどうかを判定
        is_current_holiday = is_holiday(current_date)
        is_prev_holiday = is_previous_day_holiday(current_date)
        
        # 曜日のone-hotエンコーディングを更新
        for day_key in ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]:
            base_data[day_key] = 0
        
        for day_key, value in day_encoding.items():
            base_data[day_key] = value
        
        # 外来患者数は曜日によって変動させる（実際には過去データから学習した方がよい）
        day_factor = {
            "月曜日": 1.1,  # 月曜は多め
            "火曜日": 1.0,
            "水曜日": 1.0,
            "木曜日": 0.9,
            "金曜日": 0.9,
            "土曜日": 0.5,  # 土曜は少なめ
            "日曜日": 0.3,  # 日曜はさらに少なめ
        }
        
        # 祝日の場合は日曜日と同様の係数を使用
        if is_current_holiday:
            patient_factor = day_factor["日曜日"]
        else:
            patient_factor = day_factor[day_name]
        
        # 外来患者数を曜日係数で調整（明示的に浮動小数点数に変換、iloc[0]を使用）
        base_data['total_outpatient'] = float(base_data['total_outpatient'].iloc[0]) * patient_factor
        # 紹介患者数も同様に調整
        base_data['intro_outpatient'] = float(base_data['intro_outpatient'].iloc[0]) * patient_factor
        # 救急患者数は曜日の影響が少ないため、小さな変動にする
        base_data['ER'] = float(base_data['ER'].iloc[0]) * (0.9 + 0.2 * patient_factor)
        
        # 予測実行
        prediction = predict_admission(model, base_data)
        formatted_date = current_date.strftime("%Y/%m/%d")
        forecasts.append({
            "日付": formatted_date,
            "曜日": day_name,
            "祝日": "はい" if is_current_holiday else "いいえ",
            "予測入院患者数": prediction
        })
        
        # 日付を更新
        current_date = current_date + timedelta(days=1)
    
    return forecasts

# 静的ファイルを提供するルート
@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

# 単一予測エンドポイント
@app.route('/api/predict', methods=['POST'])
def predict():
    try:
        data = request.json
        
        # 日付を解析
        prediction_date = datetime.strptime(data['date'], '%Y-%m-%d')
        
        # 曜日を取得
        day_of_week = get_day_of_week_from_date(prediction_date)
        
        # 曜日のone-hotエンコーディング
        day_encoding = DAYS_DICT[day_of_week]
        
        # 祝日判定
        is_holiday_flag = is_holiday(prediction_date)
        is_prev_holiday = is_previous_day_holiday(prediction_date)
        
        # 入力データの作成
        input_data = pd.DataFrame({
            'mon': [day_encoding["mon"]],
            'tue': [day_encoding["tue"]],
            'wed': [day_encoding["wed"]],
            'thu': [day_encoding["thu"]],
            'fri': [day_encoding["fri"]],
            'sat': [day_encoding["sat"]],
            'sun': [day_encoding["sun"]],
            'public_holiday': [1 if is_holiday_flag else 0],
            'public_holiday_previous_day': [1 if is_prev_holiday else 0],
            'total_outpatient': [data['total_outpatient']],
            'intro_outpatient': [data['intro_outpatient']],
            'ER': [data['er_count']],
            'bed_count': [data['bed_count']]
        })
        
        # モデルを読み込む
        model = load_model()
        
        # 予測を実行
        prediction = predict_admission(model, input_data)
        
        # 1週間の予測を実行
        weekly_forecast = predict_multiple_days(model, input_data.copy(), prediction_date)
        
        return jsonify({
            "prediction": prediction,
            "weekly_forecast": weekly_forecast
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 事前定義シナリオ取得エンドポイント
@app.route('/api/predefined_scenarios', methods=['GET'])
def get_predefined_scenarios():
    try:
        today = datetime.now()
        
        # 事前定義シナリオ
        predefined_scenarios = [
            {
                "id": "scenario1",
                "name": "月曜日、外来患者数が多い",
                "date": (today + timedelta(days=(0 - today.weekday()) % 7)).strftime("%Y-%m-%d"),  # 次の月曜日
                "total_outpatient": 800,
                "intro_outpatient": 30,
                "er_count": 20,
                "bed_count": 280
            },
            {
                "id": "scenario2",
                "name": "火曜日、通常の外来患者数",
                "date": (today + timedelta(days=(1 - today.weekday()) % 7)).strftime("%Y-%m-%d"),  # 次の火曜日
                "total_outpatient": 600,
                "intro_outpatient": 20,
                "er_count": 15,
                "bed_count": 280
            },
            {
                "id": "scenario3",
                "name": "水曜日、外来患者数が多い",
                "date": (today + timedelta(days=(2 - today.weekday()) % 7)).strftime("%Y-%m-%d"),  # 次の水曜日
                "total_outpatient": 750,
                "intro_outpatient": 25,
                "er_count": 15,
                "bed_count": 280
            },
            {
                "id": "scenario4",
                "name": "土曜日、少ない外来患者数",
                "date": (today + timedelta(days=(5 - today.weekday()) % 7)).strftime("%Y-%m-%d"),  # 次の土曜日
                "total_outpatient": 200,
                "intro_outpatient": 5,
                "er_count": 15,
                "bed_count": 280
            },
            {
                "id": "scenario5",
                "name": "祝日（平日想定）",
                "date": (today + timedelta(days=1)).strftime("%Y-%m-%d"),  # 翌日
                "total_outpatient": 100,
                "intro_outpatient": 3,
                "er_count": 15,
                "bed_count": 280
            }
        ]
        
        return jsonify({"scenarios": predefined_scenarios})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# シナリオ比較エンドポイント
@app.route('/api/compare', methods=['POST'])
def compare_scenarios():
    try:
        data = request.json
        scenarios = data.get('scenarios', [])
        
        if not scenarios:
            return jsonify({"error": "シナリオが指定されていません"}), 400
        
        # モデルを読み込む
        model = load_model()
        
        # 結果を格納するリスト
        results = []
        
        for scenario in scenarios:
            # 日付を解析
            scenario_date = datetime.strptime(scenario['date'], '%Y-%m-%d')
            
            # 曜日を取得
            day_of_week = get_day_of_week_from_date(scenario_date)
            
            # 曜日のone-hotエンコーディング
            day_encoding = DAYS_DICT[day_of_week]
            
            # 祝日判定
            is_holiday_flag = is_holiday(scenario_date)
            is_prev_holiday = is_previous_day_holiday(scenario_date)
            
            # 入力データの作成
            input_data = pd.DataFrame({
                'mon': [day_encoding["mon"]],
                'tue': [day_encoding["tue"]],
                'wed': [day_encoding["wed"]],
                'thu': [day_encoding["thu"]],
                'fri': [day_encoding["fri"]],
                'sat': [day_encoding["sat"]],
                'sun': [day_encoding["sun"]],
                'public_holiday': [1 if is_holiday_flag else 0],
                'public_holiday_previous_day': [1 if is_prev_holiday else 0],
                'total_outpatient': [scenario['total_outpatient']],
                'intro_outpatient': [scenario['intro_outpatient']],
                'ER': [scenario['er_count']],
                'bed_count': [scenario['bed_count']]
            })
            
            # 予測を実行
            prediction = predict_admission(model, input_data)
            
            results.append({
                "シナリオ": scenario['name'],
                "日付": scenario_date.strftime("%Y/%m/%d"),
                "曜日": day_of_week,
                "予測入院患者数": prediction
            })
        
        return jsonify({"results": results})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 月間カレンダーエンドポイント
@app.route('/api/calendar', methods=['POST'])
def generate_calendar():
    try:
        data = request.json
        year = int(data['year'])
        month = int(data['month'])
        avg_total_outpatient = float(data['avg_total_outpatient'])
        avg_intro_outpatient = float(data['avg_intro_outpatient'])
        avg_er = float(data['avg_er'])
        avg_bed_count = float(data['avg_bed_count'])
        
        # モデルを読み込む
        model = load_model()
        
        # 月の日数を取得
        _, days_in_month = calendar.monthrange(year, month)
        
        # 月間予測結果を格納するリスト
        monthly_predictions = []
        
        # 各日の予測を実行
        for day in range(1, days_in_month + 1):
            current_date = datetime(year, month, day)
            
            # 曜日取得
            day_of_week = get_day_of_week_from_date(current_date)
            
            # 曜日係数（外来患者数の変動要素）
            day_factor = {
                "月曜日": 1.1,  # 月曜は多め
                "火曜日": 1.0,
                "水曜日": 1.0,
                "木曜日": 0.9,
                "金曜日": 0.9,
                "土曜日": 0.5,  # 土曜は少なめ
                "日曜日": 0.3,  # 日曜はさらに少なめ
            }
            
            # 祝日判定
            is_current_holiday = is_holiday(current_date)
            is_prev_holiday = is_previous_day_holiday(current_date)
            
            # 祝日の場合は日曜日と同様の係数を使用
            if is_current_holiday:
                patient_factor = day_factor["日曜日"]
            else:
                patient_factor = day_factor[day_of_week]
            
            # 曜日の one-hot エンコーディング
            day_encoding = DAYS_DICT[day_of_week]
            
            # 外来患者数を曜日と祝日に応じて調整（明示的に浮動小数点数に変換、iloc[0]は不要）
            adjusted_outpatient = float(avg_total_outpatient) * patient_factor
            adjusted_intro = float(avg_intro_outpatient) * patient_factor
            adjusted_er = float(avg_er) * (0.9 + 0.2 * patient_factor)
            
            # 入力データの作成
            input_data = pd.DataFrame({
                'mon': [day_encoding["mon"]],
                'tue': [day_encoding["tue"]],
                'wed': [day_encoding["wed"]],
                'thu': [day_encoding["thu"]],
                'fri': [day_encoding["fri"]],
                'sat': [day_encoding["sat"]],
                'sun': [day_encoding["sun"]],
                'public_holiday': [1 if is_current_holiday else 0],
                'public_holiday_previous_day': [1 if is_prev_holiday else 0],
                'total_outpatient': [adjusted_outpatient],
                'intro_outpatient': [adjusted_intro],
                'ER': [adjusted_er],
                'bed_count': [avg_bed_count]
            })
            
            # 予測実行
            prediction = predict_admission(model, input_data)
            
            monthly_predictions.append({
                "date": current_date.strftime("%Y-%m-%d"),
                "day_of_week": day_of_week,
                "is_holiday": is_current_holiday,
                "prediction": prediction
            })
        
        # 予測値の四分位を計算
        prediction_values = [item["prediction"] for item in monthly_predictions]
        quartiles = np.percentile(prediction_values, [25, 50, 75])
        
        # 混雑度を追加
        for item in monthly_predictions:
            value = item["prediction"]
            if value <= quartiles[0]:
                item["busyness_level"] = "少ない"
            elif value <= quartiles[1]:
                item["busyness_level"] = "やや少ない"
            elif value <= quartiles[2]:
                item["busyness_level"] = "やや多い"
            else:
                item["busyness_level"] = "多い"
        
        return jsonify({"monthly_predictions": monthly_predictions})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)

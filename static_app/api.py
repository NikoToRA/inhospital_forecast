from flask import Flask, request, jsonify
import pandas as pd
import numpy as np
import joblib
import os
from datetime import datetime, timedelta
import jpholiday
import calendar
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # すべてのドメインからのリクエストを許可

# 曜日の定義
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

# モデル読み込み関数
def load_model():
    try:
        model = joblib.load('../fixed_rf_model.joblib')
        print("モデルを読み込みました")
        return model
    except Exception as e:
        print(f"モデルの読み込みに失敗しました: {e}")
        return None

# CSVデータ読み込み関数
def load_data():
    try:
        df = pd.read_csv('../ultimate_pickup_data.csv')
        df = df.dropna()
        return df
    except Exception as e:
        print(f"CSVファイルの読み込みに失敗しました: {e}")
        return None

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

# 次の日付を計算する関数
def get_next_date(current_date):
    return current_date + timedelta(days=1)

# 単一予測のためのエンドポイント
@app.route('/api/predict', methods=['POST'])
def predict():
    try:
        data = request.json
        model = load_model()
        
        if model is None:
            return jsonify({"error": "モデルを読み込めませんでした"}), 500
        
        # フロントエンドから送られてきたデータを取得
        date_str = data.get('date')
        total_outpatient = int(data.get('total_outpatient'))
        intro_outpatient = int(data.get('intro_outpatient'))
        er_count = int(data.get('er_count'))
        bed_count = int(data.get('bed_count'))
        
        # 日付を解析
        date = datetime.strptime(date_str, '%Y-%m-%d')
        
        # 曜日を取得
        day_of_week = get_day_of_week_from_date(date)
        
        # 曜日のone-hotエンコーディングを取得
        day_encoding = DAYS_DICT[day_of_week]
        
        # 祝日判定
        is_holiday_flag = is_holiday(date)
        is_prev_holiday = is_previous_day_holiday(date)
        
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
            'total_outpatient': [total_outpatient],
            'intro_outpatient': [intro_outpatient],
            'ER': [er_count],
            'bed_count': [bed_count]
        })
        
        # 予測を実行
        prediction = model.predict(input_data)[0]
        
        # 次の7日間の予測を行う
        weekly_forecast = []
        current_date = date
        base_data = input_data.copy()
        
        for i in range(7):
            # 曜日取得
            day_name = get_day_of_week_from_date(current_date)
            
            # 祝日かどうかを判定
            is_current_holiday = is_holiday(current_date)
            is_prev_holiday = is_previous_day_holiday(current_date)
            
            # 曜日のone-hotエンコーディングを更新
            for day_key in ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]:
                base_data[day_key] = 0
            
            day_encoding = DAYS_DICT[day_name]
            for day_key, value in day_encoding.items():
                base_data[day_key] = value
            
            # 外来患者数は曜日によって変動（実際には過去データから学習した方がよい）
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
            
            # 外来患者数を曜日係数で調整
            base_data['total_outpatient'] = total_outpatient * patient_factor
            # 紹介患者数も同様に調整
            base_data['intro_outpatient'] = intro_outpatient * patient_factor
            # 救急患者数は曜日の影響が少ないため、小さな変動にする
            base_data['ER'] = er_count * (0.9 + 0.2 * patient_factor)
            # 祝日フラグを更新
            base_data['public_holiday'] = 1 if is_current_holiday else 0
            base_data['public_holiday_previous_day'] = 1 if is_prev_holiday else 0
            
            # 予測実行
            day_prediction = model.predict(base_data)[0]
            
            # 日付をフォーマット
            formatted_date = current_date.strftime("%Y-%m-%d")
            
            weekly_forecast.append({
                "date": formatted_date,
                "day_of_week": day_name,
                "is_holiday": is_current_holiday,
                "predicted_admission": float(day_prediction)
            })
            
            # 日付を更新
            current_date = get_next_date(current_date)
        
        # レスポンスを返す
        return jsonify({
            "prediction": float(prediction),
            "weekly_forecast": weekly_forecast,
            "date_info": {
                "date": date_str,
                "day_of_week": day_of_week,
                "is_holiday": is_holiday_flag,
                "holiday_name": jpholiday.is_holiday_name(date) if is_holiday_flag else None
            }
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 月間カレンダー予測のエンドポイント
@app.route('/api/calendar', methods=['POST'])
def calendar_prediction():
    try:
        data = request.json
        model = load_model()
        
        if model is None:
            return jsonify({"error": "モデルを読み込めませんでした"}), 500
        
        # リクエストデータを取得
        year = int(data.get('year'))
        month = int(data.get('month'))
        avg_total_outpatient = int(data.get('avg_total_outpatient'))
        avg_intro_outpatient = int(data.get('avg_intro_outpatient'))
        avg_er = int(data.get('avg_er'))
        avg_bed_count = int(data.get('avg_bed_count'))
        
        # 月の日数を取得
        _, days_in_month = calendar.monthrange(year, month)
        
        # 結果を格納する配列
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
            is_holiday_flag = is_holiday(current_date)
            is_prev_holiday = is_previous_day_holiday(current_date)
            
            # 祝日の場合は日曜日と同様の係数を使用
            if is_holiday_flag:
                patient_factor = day_factor["日曜日"]
            else:
                patient_factor = day_factor[day_of_week]
            
            # 曜日のone-hotエンコーディングを取得
            day_encoding = DAYS_DICT[day_of_week]
            
            # 外来患者数を曜日係数で調整
            adjusted_outpatient = avg_total_outpatient * patient_factor
            adjusted_intro = avg_intro_outpatient * patient_factor
            adjusted_er = avg_er * (0.9 + 0.2 * patient_factor)
            
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
                'total_outpatient': [adjusted_outpatient],
                'intro_outpatient': [adjusted_intro],
                'ER': [adjusted_er],
                'bed_count': [avg_bed_count]
            })
            
            # 予測を実行
            prediction = model.predict(input_data)[0]
            
            # 結果を追加
            monthly_predictions.append({
                "date": current_date.strftime("%Y-%m-%d"),
                "day": day,
                "day_of_week": day_of_week,
                "is_holiday": is_holiday_flag,
                "holiday_name": jpholiday.is_holiday_name(current_date) if is_holiday_flag else None,
                "predicted_admission": float(prediction)
            })
        
        # 予測値の四分位数を計算して混雑度を割り当て
        predictions = [item["predicted_admission"] for item in monthly_predictions]
        quartiles = np.percentile(predictions, [25, 50, 75])
        
        for item in monthly_predictions:
            value = item["predicted_admission"]
            if value <= quartiles[0]:
                item["busyness_level"] = "少ない"
                item["busyness_color"] = "#a1d99b"  # 薄い緑
            elif value <= quartiles[1]:
                item["busyness_level"] = "やや少ない"
                item["busyness_color"] = "#fee391"  # 薄い黄色
            elif value <= quartiles[2]:
                item["busyness_level"] = "やや多い"
                item["busyness_color"] = "#fc9272"  # オレンジ
            else:
                item["busyness_level"] = "多い"
                item["busyness_color"] = "#de2d26"  # 赤
        
        return jsonify({
            "monthly_predictions": monthly_predictions,
            "quartiles": {
                "q1": float(quartiles[0]),
                "q2": float(quartiles[1]),
                "q3": float(quartiles[2])
            }
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# シナリオ比較のエンドポイント
@app.route('/api/compare', methods=['POST'])
def compare_scenarios():
    try:
        data = request.json
        model = load_model()
        
        if model is None:
            return jsonify({"error": "モデルを読み込めませんでした"}), 500
        
        scenarios = data.get('scenarios', [])
        results = []
        
        for scenario in scenarios:
            # シナリオデータを取得
            name = scenario.get('name')
            date_str = scenario.get('date')
            total_outpatient = int(scenario.get('total_outpatient'))
            intro_outpatient = int(scenario.get('intro_outpatient'))
            er_count = int(scenario.get('er_count'))
            bed_count = int(scenario.get('bed_count'))
            
            # 日付を解析
            date = datetime.strptime(date_str, '%Y-%m-%d')
            
            # 曜日を取得
            day_of_week = get_day_of_week_from_date(date)
            
            # 曜日のone-hotエンコーディングを取得
            day_encoding = DAYS_DICT[day_of_week]
            
            # 祝日判定
            is_holiday_flag = is_holiday(date)
            is_prev_holiday = is_previous_day_holiday(date)
            
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
                'total_outpatient': [total_outpatient],
                'intro_outpatient': [intro_outpatient],
                'ER': [er_count],
                'bed_count': [bed_count]
            })
            
            # 予測を実行
            prediction = model.predict(input_data)[0]
            
            # 結果を追加
            results.append({
                "name": name,
                "date": date_str,
                "day_of_week": day_of_week,
                "is_holiday": is_holiday_flag,
                "predicted_admission": float(prediction)
            })
        
        return jsonify({"results": results})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# データ分析のエンドポイント
@app.route('/api/data', methods=['GET'])
def get_data():
    try:
        df = load_data()
        
        if df is None:
            return jsonify({"error": "データを読み込めませんでした"}), 500
        
        # 基本統計量
        stats = df.describe().reset_index().rename(columns={'index': 'stat'})
        stats_dict = stats.to_dict(orient='records')
        
        # 最初の5行のデータ
        sample = df.head().to_dict(orient='records')
        
        # 曜日別の平均入院患者数
        days = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
        day_means = []
        
        for day in days:
            day_mean = df[df[day] == 1]['y'].mean()
            day_means.append({
                "day": ["月", "火", "水", "木", "金", "土", "日"][days.index(day)],
                "mean": float(day_mean)
            })
        
        # 時系列データの準備
        df['date'] = pd.to_datetime(df['date'])
        time_series = df[['date', 'y']].sort_values('date').to_dict(orient='records')
        time_series = [{"date": item["date"].strftime("%Y-%m-%d"), "value": float(item["y"])} for item in time_series]
        
        # 外来患者数と入院患者数の関係
        scatter_data = df[['total_outpatient', 'y']].to_dict(orient='records')
        scatter_data = [{"x": float(item["total_outpatient"]), "y": float(item["y"])} for item in scatter_data]
        
        return jsonify({
            "sample": sample,
            "stats": stats_dict,
            "day_means": day_means,
            "time_series": time_series,
            "scatter_data": scatter_data
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# データ保存のエンドポイント
@app.route('/api/save', methods=['POST'])
def save_data():
    try:
        data = request.json
        
        # 送信されたデータを取得
        date_str = data.get('date')
        day_of_week = data.get('day_of_week')
        total_outpatient = int(data.get('total_outpatient'))
        intro_outpatient = int(data.get('intro_outpatient'))
        er_count = int(data.get('er_count'))
        bed_count = int(data.get('bed_count'))
        actual_admission = float(data.get('actual_admission'))
        
        # 曜日のone-hotエンコーディングを取得
        day_encoding = DAYS_DICT[day_of_week]
        
        # 日付を解析
        date = datetime.strptime(date_str, '%Y-%m-%d')
        
        # 祝日判定
        is_holiday_flag = is_holiday(date)
        is_prev_holiday = is_previous_day_holiday(date)
        
        # CSVファイルを読み込む
        try:
            df = pd.read_csv('../ultimate_pickup_data.csv')
        except FileNotFoundError:
            # ファイルが存在しない場合は、新しいDataFrameを作成
            df = pd.DataFrame(columns=['date', 'mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun', 
                                       'public_holiday', 'public_holiday_previous_day', 
                                       'total_outpatient', 'intro_outpatient', 'ER', 'bed_count', 'y'])
        
        # 日付が既に存在するかチェック
        if date_str in df['date'].values:
            # 既存のデータを削除
            df = df[df['date'] != date_str]
        
        # 新しいデータを作成
        new_data = {
            'date': date_str,
            'mon': day_encoding["mon"],
            'tue': day_encoding["tue"],
            'wed': day_encoding["wed"],
            'thu': day_encoding["thu"],
            'fri': day_encoding["fri"],
            'sat': day_encoding["sat"],
            'sun': day_encoding["sun"],
            'public_holiday': 1 if is_holiday_flag else 0,
            'public_holiday_previous_day': 1 if is_prev_holiday else 0,
            'total_outpatient': total_outpatient,
            'intro_outpatient': intro_outpatient,
            'ER': er_count,
            'bed_count': bed_count,
            'y': actual_admission
        }
        
        # 新しいデータをデータフレームに追加
        df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
        
        # CSVファイルに保存
        df.to_csv('../ultimate_pickup_data.csv', index=False)
        
        return jsonify({"success": True, "message": "データが正常に保存されました。"})
    
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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 
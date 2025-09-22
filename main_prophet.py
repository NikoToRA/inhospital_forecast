import pandas as pd
from prophet import Prophet
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import joblib

# 今日の日付を取得
today = datetime.today()

# 翌日と7日後の日付を計算
start_date = (today + timedelta(days=1)).strftime('%Y-%m-%d')
end_date = (today + timedelta(days=7)).strftime('%Y-%m-%d')

print("=== Prophet時系列予測モデルの学習 ===")

# データの読み込み
data = pd.read_csv('ultimate_pickup_data.csv')
print(f"データ読み込み完了: {len(data)}行")

# 日付の前処理
data['date'] = pd.to_datetime(data['date'])
data = data.rename(columns={'date': 'ds'})
data = data[['ds', 'y']].sort_values('ds')
print(f"日付範囲: {data['ds'].min()} - {data['ds'].max()}")

# Prophetモデルの作成と学習
print("Prophetモデルを学習中...")
model = Prophet(
    yearly_seasonality=True,
    weekly_seasonality=True,
    daily_seasonality=False,
    seasonality_mode='multiplicative'
)
model.fit(data)
print("学習完了")

# モデルを保存
model_path = 'prophet_model.joblib'
joblib.dump(model, model_path)
print(f"モデルを保存: {model_path}")

# 未来の日付を予測（60日分）
print("60日分の予測を生成中...")
future = model.make_future_dataframe(periods=60)
forecast = model.predict(future)

# 翌日から7日後までの予測結果を表示
filtered_forecast = forecast[(forecast['ds'] >= start_date) & (forecast['ds'] <= end_date)]
print("\n=== 7日間予測結果 ===")
for _, row in filtered_forecast.iterrows():
    print(f"{row['ds'].strftime('%Y-%m-%d')}: {row['yhat']:.1f}人 (下限: {row['yhat_lower']:.1f}, 上限: {row['yhat_upper']:.1f})")

print(f"\nProphetモデルが正常に学習・保存されました: {model_path}")

# プロットは無効化（サーバー環境用）
# fig = model.plot(forecast)
# plt.show()
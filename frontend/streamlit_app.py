import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import platform
import matplotlib.dates as mdates
import jpholiday
import calendar
import matplotlib.colors as mcolors
import matplotlib.patches as mpatches
from datetime import datetime, timedelta, date as date_type
import requests
import io
import json

# ページ設定
st.set_page_config(
    page_title="BED: Bed Entry and Discharge Predictor",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# カスタムCSS追加
st.markdown("""
<style>
    /* 全体のカラーテーマ */
    :root {
        --primary-color: #00467F;
        --secondary-color: #A5CC82;
        --background-color: #f8f9fa;
        --highlight-color: #1E88E5;
        --text-color: #333333;
    }
    
    /* ベースとなるスタイル */
    .main {
        background-color: var(--background-color);
        font-family: 'Helvetica', 'Arial', sans-serif;
        color: var(--text-color);
    }
    
    /* ヘッダーのスタイル */
    .stTitleContainer {
        background: linear-gradient(90deg, var(--primary-color), var(--secondary-color));
        padding: 1.5rem 1rem;
        border-radius: 10px;
        margin-bottom: 1.5rem;
    }
    
    h1 {
        color: white !important;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
    }
    
    /* ボタンのスタイル強化 */
    .stButton>button {
        background: linear-gradient(90deg, var(--primary-color), var(--secondary-color)) !important;
        color: white !important;
        border: none !important;
        border-radius: 5px !important;
        transition: all 0.3s ease !important;
        font-size: 1.2em !important;
        padding: 0.8em 1.6em !important;
        height: auto !important;
        min-height: 3em !important;
        width: 100% !important;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1) !important;
    }
</style>
""", unsafe_allow_html=True)

# APIエンドポイント（Azure Functions）
API_URL = "/api"  # Static Web Appsでは相対パスが自動的にAPIにルーティングされる

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

# 日本語フォント設定
def set_japanese_font():
    try:
        plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Noto Sans CJK JP', 'IPAPGothic', 'sans-serif']
        plt.rcParams['font.family'] = 'sans-serif'
        plt.rcParams['axes.unicode_minus'] = False
        
        # 警告を抑制
        import warnings
        warnings.filterwarnings("ignore", category=UserWarning, message="Glyph.*missing from current font")
    except Exception as e:
        st.warning(f"日本語フォント設定エラー: {e}")

# 日付から曜日を取得する関数
def get_day_of_week_from_date(date):
    weekday = date.weekday()
    return WEEKDAY_MAP[weekday]

# 日付が祝日かどうか判定する関数
def is_holiday(date):
    return jpholiday.is_holiday(date)

# 前日が祝日かどうか判定する関数
def is_previous_day_holiday(date):
    previous_day = date - timedelta(days=1)
    return is_holiday(previous_day)

# 予測APIを呼び出す関数
def predict_admission(input_data):
    try:
        response = requests.post(f"{API_URL}/predict", json=input_data)
        if response.status_code == 200:
            return response.json()["prediction"]
        else:
            st.error(f"予測APIエラー: {response.status_code} - {response.text}")
            return 0
    except Exception as e:
        st.error(f"予測API呼び出しエラー: {e}")
        return 0

# データを保存するAPI呼び出し
def save_data(date, day_data, input_data, real_admission):
    try:
        data = {
            "date": date,
            "day_data": day_data,
            "input_data": input_data,
            "real_admission": real_admission
        }
        response = requests.post(f"{API_URL}/save_data", json=data)
        if response.status_code == 200:
            return True, "データが正常に保存されました。"
        else:
            return False, f"データ保存APIエラー: {response.status_code} - {response.text}"
    except Exception as e:
        return False, f"データ保存API呼び出しエラー: {e}"

# データを読み込むAPI呼び出し
@st.cache_data
def load_data():
    try:
        response = requests.get(f"{API_URL}/load_data")
        if response.status_code == 200:
            data = response.json()
            return pd.DataFrame(data["data"])
        else:
            st.error(f"データ読み込みAPIエラー: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"データ読み込みAPI呼び出しエラー: {e}")
        return None

# 複数日の予測を行う関数
def predict_multiple_days(base_data, start_date, num_days=7):
    forecasts = []
    current_date = start_date
    
    for i in range(num_days):
        day_name = get_day_of_week_from_date(current_date)
        day_encoding = DAYS_DICT[day_name]
        
        is_current_holiday = is_holiday(current_date)
        is_prev_holiday = is_previous_day_holiday(current_date)
        
        # 曜日のone-hotエンコーディングを更新
        prediction_data = base_data.copy()
        for day_key in ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]:
            prediction_data[day_key] = 0
        
        for day_key, value in day_encoding.items():
            prediction_data[day_key] = value
        
        # 外来患者数は曜日によって変動させる
        day_factor = {
            "月曜日": 1.1,  # 月曜は多め
            "火曜日": 1.0,
            "水曜日": 1.0,
            "木曜日": 0.9,
            "金曜日": 0.9,
            "土曜日": 0.5,  # 土曜は少なめ
            "日曜日": 0.3,  # 日曜はさらに少なめ
        }
        
        patient_factor = day_factor["日曜日"] if is_current_holiday else day_factor[day_name]
        
        prediction_data['total_outpatient'] = prediction_data['total_outpatient'] * patient_factor
        prediction_data['intro_outpatient'] = prediction_data['intro_outpatient'] * patient_factor
        prediction_data['ER'] = prediction_data['ER'] * (0.9 + 0.2 * patient_factor)
        
        # 予測実行
        prediction = predict_admission(prediction_data)
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

# データ可視化関数
def visualize_data(df):
    if df is not None:
        st.subheader("データ分析")
        
        # 日本語フォント設定
        set_japanese_font()
        
        # 入院患者数の時系列表示
        fig, ax = plt.subplots(figsize=(10, 5))
        fig.patch.set_facecolor('#f8f9fa')
        ax.set_facecolor('#f8f9fa')
        
        df['date'] = pd.to_datetime(df['date'])
        ax.plot(df['date'], df['y'], color='#00467F')
        ax.set_title('入院患者数の推移', fontsize=16)
        ax.set_xlabel('日付', fontsize=12)
        ax.set_ylabel('入院患者数', fontsize=12)
        st.pyplot(fig)
        
        # 曜日と入院患者数の関係
        fig, ax = plt.subplots(figsize=(10, 5))
        fig.patch.set_facecolor('#f8f9fa')
        ax.set_facecolor('#f8f9fa')
        
        days = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
        day_means = []
        
        for day in days:
            day_mean = df[df[day] == 1]['y'].mean()
            day_means.append(day_mean)
        
        sns.barplot(x=['月', '火', '水', '木', '金', '土', '日'], y=day_means, ax=ax, palette='Blues_d')
        ax.set_title('曜日別の平均入院患者数', fontsize=16)
        ax.set_xlabel('曜日', fontsize=12)
        ax.set_ylabel('平均入院患者数', fontsize=12)
        st.pyplot(fig)

# メイン処理
def main():
    # アプリ名を表示（カスタムスタイル適用）
    st.markdown("""
    <div style="text-align: center; background: linear-gradient(to right, #00467F, #A5CC82); padding: 1.2rem; border-radius: 10px; margin-bottom: 1rem; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
        <h1 style="color: white; margin: 0; font-weight: 700; font-size: 2.5rem;">🏥 BED: Bed Entry and Discharge Predictor</h1>
        <p style="color: white; opacity: 0.8; margin-top: 0.5rem; font-size: 1.2rem;">入院患者数予測システム</p>
    </div>
    """, unsafe_allow_html=True)
    
    # サイドバーにアプリ情報
    st.sidebar.title("BED: Bed Entry and Discharge Predictor")
    st.sidebar.info(
        "このアプリは、病院の入院患者数を予測するためのツールです。"
        "様々な条件をパラメータとして入力し、予測結果を確認できます。"
    )
    
    # 使い方説明
    st.sidebar.title("使い方")
    st.sidebar.markdown("""
    1. 「単一予測」タブで1つのシナリオを予測
    2. 「月間カレンダー」タブで一ヶ月分のカレンダー表示
    3. 「シナリオ比較」タブで複数条件を比較
    4. 「データ分析」タブでデータを分析
    """)
    
    # データの読み込み
    df = load_data()
    
    if df is None:
        st.error("データの読み込みに失敗しました。APIが正しく設定されているか確認してください。")
        return
    
    # タブを作成
    tab1, tab2, tab3, tab4 = st.tabs(["単一予測", "月間カレンダー", "シナリオ比較", "データ分析"])
    
    with tab1:
        st.markdown('<h2 style="color: #00467F; border-bottom: 2px solid #A5CC82; padding-bottom: 0.3rem;">今日の入院患者数を予測</h2>', unsafe_allow_html=True)
        
        st.write("👇 以下に今日のデータを入力して「予測実行」ボタンをクリックしてください")
        
        with st.form("single_prediction_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                selected_date = st.date_input(
                    "日付を選択",
                    value=datetime.now(),
                    format="YYYY/MM/DD"
                )
                
                selected_day = get_day_of_week_from_date(selected_date)
                
                is_holiday_flag = is_holiday(selected_date)
                
                if is_holiday_flag:
                    holiday_name = jpholiday.is_holiday_name(selected_date)
                    st.markdown(f"**{selected_date.strftime('%Y年%m月%d日')}（{selected_day}）- 祝日: {holiday_name}**")
                    st.markdown('<div style="background-color: #ffebee; padding: 8px; border-radius: 5px; color: #c62828;">祝日です</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f"**{selected_date.strftime('%Y年%m月%d日')}（{selected_day}）**")
                
            with col2:
                if df is not None:
                    default_out = int(df['total_outpatient'].mean())
                    default_intro = int(df['intro_outpatient'].mean())
                    default_er = int(df['ER'].mean())
                    default_bed = int(df['bed_count'].mean())
                else:
                    default_out = 500
                    default_intro = 20
                    default_er = 15
                    default_bed = 280
                
                total_outpatient = st.number_input("前日総外来患者数", min_value=0, max_value=2000, value=default_out, step=1)
                intro_outpatient = st.number_input("前日紹介外来患者数", min_value=0, max_value=200, value=default_intro, step=1)
                er_count = st.number_input("前日救急搬送患者数", min_value=0, max_value=100, value=default_er, step=1)
                bed_count = st.number_input("現在の病床利用数", min_value=100, max_value=1000, value=default_bed, step=1)
            
            # 予測実行ボタン
            predict_button = st.form_submit_button("予測実行", type="primary", use_container_width=True)
        
        if predict_button or "last_prediction" in st.session_state:
            # 入力データの作成
            day_encoding = DAYS_DICT[selected_day]
            
            # 祝日判定
            is_holiday_flag = is_holiday(selected_date)
            is_prev_holiday = is_previous_day_holiday(selected_date)
            
            input_data = {
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
                'bed_count': bed_count
            }
            
            # 予測を実行
            with st.spinner("予測を実行中..."):
                if predict_button:
                    prediction = predict_admission(input_data)
                    st.session_state.last_prediction = prediction
                    st.session_state.last_input_data = input_data
                    st.session_state.last_day_encoding = day_encoding
                    st.session_state.last_selected_day = selected_day
                else:
                    prediction = st.session_state.last_prediction
                    input_data = st.session_state.last_input_data
                    day_encoding = st.session_state.last_day_encoding
                    selected_day = st.session_state.last_selected_day
            
            # 結果表示
            st.success(f"### 予測入院患者数: {prediction:.1f} 人")
            
            # 1週間の予測を表示
            st.subheader("今後1週間の予測")
            
            # 複数日の予測を実行
            with st.spinner('1週間分の予測を計算中...'):
                weekly_forecast = predict_multiple_days(input_data, datetime.now())
            
            # 表形式で表示
            weekly_df = pd.DataFrame(weekly_forecast)
            weekly_df['予測入院患者数'] = weekly_df['予測入院患者数'].round(1)
            st.dataframe(weekly_df)
            
            # 実測値入力と保存
            st.subheader("実測値の記録")
            
            save_col1, save_col2 = st.columns([2, 1])
            
            with save_col1:
                st.markdown("""
                **1日1回の正確なデータ保存**
                
                - 予測した日の実際の入院患者数を記録します
                - 1日1回のみ保存可能です
                - 正確な実数を入力してください
                - 保存したデータは予測精度向上に使用されます
                """)
            
            with save_col2:
                real_admission = st.number_input(
                    "実際の入院患者数",
                    min_value=0.0,
                    max_value=1000.0,
                    value=float(prediction),
                    step=0.1,
                    key="real_admission_input"
                )
                
                if st.button("データを保存", key="save_prediction", type="primary", use_container_width=True):
                    today_date = datetime.now().strftime("%Y-%m-%d")
                    success, message = save_data(
                        today_date,
                        day_encoding,
                        input_data,
                        real_admission
                    )
                    
                    if success:
                        st.success(f"✅ {message}")
                        st.cache_data.clear()
                        if "last_prediction" in st.session_state:
                            del st.session_state.last_prediction
                        st.rerun()
                    else:
                        st.error(message)
    
    with tab4:
        st.markdown('<h2 style="color: #00467F; border-bottom: 2px solid #A5CC82; padding-bottom: 0.3rem;">データ分析</h2>', unsafe_allow_html=True)
        visualize_data(df)

if __name__ == "__main__":
    main() 
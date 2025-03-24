import streamlit as st
import pandas as pd
import numpy as np
import joblib
import os
import sys
from datetime import datetime, timedelta, date as date_type
import matplotlib.pyplot as plt
import seaborn as sns
import platform
import matplotlib.dates as mdates
import jpholiday  # 日本の祝日判定用ライブラリ
import calendar
import matplotlib.colors as mcolors
import matplotlib.patches as mpatches

# 日本語フォントのインポートを確認
try:
    import japanize_matplotlib
    JAPANIZE_AVAILABLE = True
except ImportError:
    JAPANIZE_AVAILABLE = False

# 日本語フォントの設定
import matplotlib
if platform.system() == 'Darwin':  # macOS
    matplotlib.rc('font', family='Hiragino Sans')
elif platform.system() == 'Windows':
    matplotlib.rc('font', family='MS Gothic')
else:  # Linux
    matplotlib.rc('font', family='IPAGothic')

# フォントのフォールバックを設定
plt.rcParams['font.sans-serif'] = ['Hiragino Sans', 'Hiragino Sans GB', 'Hiragino Maru Gothic Pro', 
                                   'MS Gothic', 'Yu Gothic', 'IPAPGothic', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# Streamlitの初期設定をスキップするための環境変数
if 'STREAMLIT_EMAIL' not in os.environ:
    os.environ['STREAMLIT_EMAIL'] = ""

# 接続エラー対策（再接続のためのSession Stateを管理）
if "connection_attempts" not in st.session_state:
    st.session_state.connection_attempts = 0

# ページ設定
st.set_page_config(
    page_title="BED: Bed Entry and Discharge Predictor",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# カスタムCSS追加 - ボタンのテーマカラー設定
st.markdown("""
<style>
    /* 注: メインスタイルはすでにcustom_cssで定義されているためこのセクションは削除 */
</style>
""", unsafe_allow_html=True)

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

# モバイルデバイス検出用のJavaScript
device_detection_js = """
<script>
    // デバイスの幅を取得して、モバイルかどうかを判定
    function detectDeviceType() {
        const width = window.innerWidth;
        const isMobile = width < 768; // 768px未満をモバイルと判定
        
        // 検出結果をセッションストレージに保存
        sessionStorage.setItem('isMobile', isMobile);
        
        // Streamlitのセッションステートに値を渡すためにクエリパラメータを設定
        const currentUrl = new URL(window.location.href);
        currentUrl.searchParams.set('mobile_detected', isMobile);
        
        // ページをリロードせずにクエリパラメータを更新
        window.history.replaceState({}, '', currentUrl);
        
        return isMobile;
    }
    
    // ページ読み込み時に実行
    window.addEventListener('load', detectDeviceType);
    
    // 画面サイズ変更時にも再検出
    window.addEventListener('resize', detectDeviceType);
    
    // 初期検出を即時実行
    detectDeviceType();
</script>
"""

st.markdown(device_detection_js, unsafe_allow_html=True)

# モバイルデバイスの検出をセッションステートで管理
if 'is_mobile' not in st.session_state:
    st.session_state.is_mobile = False

# 画面幅の検出
def is_mobile_device():
    # SessionStateにモバイル検出フラグがなければ初期化
    if 'is_mobile' not in st.session_state:
        st.session_state.is_mobile = False
    return st.session_state.is_mobile

# モバイル検出後にカスタムCSSを適用
custom_css = """
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
    
    /* ボタンのスタイル強化 - テーマカラーを統一 */
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
    
    /* プライマリボタン（予測開始など）をさらに大きく */
    button[kind="primary"] {
        font-size: 1.2em !important;
        padding: 0.8em 1.5em !important;
        font-weight: bold !important;
        min-height: 3em !important;
        background: linear-gradient(90deg, #00467F, #A5CC82) !important;
    }
    
    /* フォームのサブミットボタンもグラデーションに統一 */
    button[kind="primaryFormSubmit"] {
        font-size: 1.2em !important;
        padding: 0.8em 1.5em !important;
        font-weight: bold !important;
        min-height: 3em !important;
        background: linear-gradient(90deg, #00467F, #A5CC82) !important;
        color: white !important;
        border: none !important;
    }
    
    /* Streamlitのform要素内のボタンにも適用 */
    div[data-testid="stForm"] button[kind="formSubmit"] {
        background: linear-gradient(90deg, #00467F, #A5CC82) !important;
        color: white !important;
        border: none !important;
        font-weight: bold !important;
    }
    
    /* フォームボタンのホバー効果 */
    button[kind="primaryFormSubmit"]:hover, div[data-testid="stForm"] button[kind="formSubmit"]:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 5px 10px rgba(0,0,0,0.15) !important;
        opacity: 0.95 !important;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 5px 10px rgba(0,0,0,0.15) !important;
        opacity: 0.95 !important;
    }
    
    /* データフレームのスタイル */
    .dataframe {
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    
    /* 入力フィールドのスタイル */
    .stNumberInput, .stTextInput, .stSelectbox {
        border-radius: 5px;
    }
    
    /* タブのスタイル */
    .stTabs [data-baseweb="tab-list"] {
        gap: 1px;
        display: flex;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        background-color: #f0f2f6;
        border-radius: 5px 5px 0 0;
        color: var(--text-color);
        font-weight: 500;
        flex: 1;
        text-align: center;
        display: flex;
        align-items: center;
        justify-content: center;
        min-width: 80px;
        padding: 0 10px;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(180deg, #ffffff, #f8f9fa);
        border-top: 3px solid var(--primary-color);
    }
    
    /* タブのテキストサイズを均一にする */
    .stTabs [data-baseweb="tab"] p {
        font-size: 16px !important;
        margin: 0;
        white-space: nowrap;
    }
    
    /* サイドバーのスタイル */
    [data-testid="stSidebar"] {
        background-color: #f5f7f9;
        border-right: 1px solid #e0e0e0;
    }
    
    /* メトリクスのスタイル */
    [data-testid="stMetric"] {
        background-color: white;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    
    [data-testid="stMetricLabel"] {
        color: var(--primary-color);
    }
    
    [data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
        font-weight: bold;
        color: var(--highlight-color);
    }
    
    /* モバイル表示のとき */
    @media (max-width: 640px) {
        .stTabs [data-baseweb="tab"] {
            height: 45px;
            padding: 0 5px;
            font-size: 12px;
            flex: 1;
            min-width: unset;
        }
        
        .stTabs [data-baseweb="tab"] p {
            font-size: 14px !important;
        }
        
        [data-testid="stMetricValue"] {
            font-size: 1.5rem !important;
        }
        
        /* モバイルでもボタンを大きく保つ */
        .stButton>button {
            font-size: 1.2em !important;
            padding: 0.8em 1em !important;
        }
        
        button[kind="primary"] {
            font-size: 1.3em !important;
        }
    }
</style>
"""

st.markdown(custom_css, unsafe_allow_html=True)

# 接続エラーが起きた場合のハンドリング
try:
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

    # 現在の曜日から翌日の曜日を計算する関数
    def get_next_day_of_week(current_day):
        days = DAYS_OF_WEEK
        current_index = days.index(current_day)
        next_index = (current_index + 1) % 7
        return days[next_index]

    # モデルを修正して保存する関数
    def fix_model_compatibility():
        try:
            model = joblib.load('fixed_rf_model.joblib')
            return model
        except Exception as e:
            st.error(f"モデルの読み込みに失敗しました: {str(e)}")
            return None

    # モデルを読み込む関数
    @st.cache_resource
    def load_model():
        try:
            model = fix_model_compatibility()
            if model is None:
                st.error("モデルの読み込みに失敗しました。")
                return None
            return model
        except Exception as e:
            st.error(f"モデルの読み込み中にエラーが発生しました: {str(e)}")
            return None

    # CSVデータを読み込む関数
    @st.cache_data
    def load_data():
        try:
            df = pd.read_csv('ultimate_pickup_data.csv')
            return df
        except Exception as e:
            st.error(f"データの読み込みに失敗しました: {str(e)}")
            return None
    
    # ユーザーデータをCSVに追加する関数（キャッシュなし）
    def append_data_to_csv(date, day_data, input_data, admission_result):
        try:
            # CSVファイルを読み込む
            try:
                df = pd.read_csv('ultimate_pickup_data.csv')
            except FileNotFoundError:
                # ファイルが存在しない場合は、新しいDataFrameを作成
                df = pd.DataFrame(columns=['date', 'mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun', 
                                           'public_holiday', 'public_holiday_previous_day', 
                                           'total_outpatient', 'intro_outpatient', 'ER', 'bed_count', 'y'])
            
            # 日付が既に存在するかチェック
            if date in df['date'].values:
                # 上書き確認
                st.warning(f"日付 {date} のデータは既に存在します。既存のデータを更新します。")
                # 既存のデータを削除
                df = df[df['date'] != date]
            
            # 新しいデータを作成
            new_data = {
                'date': date,
                'mon': day_data['mon'],
                'tue': day_data['tue'],
                'wed': day_data['wed'],
                'thu': day_data['thu'],
                'fri': day_data['fri'],
                'sat': day_data['sat'],
                'sun': day_data['sun'],
                'public_holiday': input_data['public_holiday'].values[0],
                'public_holiday_previous_day': input_data['public_holiday_previous_day'].values[0],
                'total_outpatient': input_data['total_outpatient'].values[0],
                'intro_outpatient': input_data['intro_outpatient'].values[0],
                'ER': input_data['ER'].values[0],
                'bed_count': input_data['bed_count'].values[0],
                'y': admission_result
            }
            
            # 新しいデータをデータフレームに追加
            df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
            
            # CSVファイルに保存
            df.to_csv('ultimate_pickup_data.csv', index=False)
            
            # セッションステートでキャッシュを無効化
            st.session_state['data_updated'] = True
            
            return True, "データが正常に保存されました。"
        except Exception as e:
            return False, f"データの保存に失敗しました: {e}"

    # 予測を実行する関数
    def predict_admission(model, input_data):
        try:
            # 予測を実行
            prediction = model.predict(input_data)
            return prediction[0]
        except Exception as e:
            st.error(f"予測に失敗しました: {e}")
            return 0

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
            
            # 外来患者数と入院患者数の相関
            fig, ax = plt.subplots(figsize=(10, 5))
            fig.patch.set_facecolor('#f8f9fa')
            ax.set_facecolor('#f8f9fa')
            
            sns.scatterplot(x='total_outpatient', y='y', data=df, ax=ax, color='#00467F')
            ax.set_title('外来患者数と入院患者数の関係', fontsize=16)
            ax.set_xlabel('外来患者数', fontsize=12)
            ax.set_ylabel('入院患者数', fontsize=12)
            st.pyplot(fig)

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
            
            # 外来患者数を曜日係数で調整
            base_data['total_outpatient'] = base_data['total_outpatient'] * patient_factor
            # 紹介患者数も同様に調整
            base_data['intro_outpatient'] = base_data['intro_outpatient'] * patient_factor
            # 救急患者数は曜日の影響が少ないため、小さな変動にする
            base_data['ER'] = base_data['ER'] * (0.9 + 0.2 * patient_factor)
            
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
            current_date = get_next_date(current_date)
        
        return forecasts

    # 日本語フォント設定（警告対策）
    def set_japanese_font():
        try:
            import matplotlib
            
            # フォントの設定
            if platform.system() == 'Darwin':  # macOS
                matplotlib.rc('font', family='AppleGothic')
            elif platform.system() == 'Windows':
                matplotlib.rc('font', family='MS Gothic')
            else:  # Linux
                matplotlib.rc('font', family='IPAGothic')
            
            # 文字化け防止のための追加設定
            plt.rcParams['axes.unicode_minus'] = False
            
        except Exception as e:
            print(f"フォント設定エラー: {e}")
            # エラーが発生しても処理を継続

    # 複数日予測の結果をグラフ表示
    def plot_weekly_forecast(forecast_data):
        # 日本語フォント設定を呼び出し
        set_japanese_font()
        
        fig, ax = plt.subplots(figsize=(10, 5))
        
        # 背景色を設定（見やすさを向上）
        fig.patch.set_facecolor('#f8f9fa')
        ax.set_facecolor('#f8f9fa')
        
        dates = [item["日付"] for item in forecast_data]
        values = [item["予測入院患者数"] for item in forecast_data]
        weekdays = [item["曜日"] for item in forecast_data]
        holidays = [item["祝日"] for item in forecast_data]
        
        # 日付をdatetimeオブジェクトに変換
        x_dates = []
        for date in dates:
            if isinstance(date, str):
                x_dates.append(datetime.strptime(date, "%Y/%m/%d"))
            elif isinstance(date, datetime):
                x_dates.append(date)
        
        # 折れ線グラフ
        ax.plot(range(len(values)), values, marker='o', linewidth=2, markersize=8, color='#00467F')
        
        # x軸の設定
        ax.set_xticks(range(len(values)))
        
        # 日付と曜日のラベルを作成 - 祝日ステータスは表示しない
        date_labels = []
        for d, wd in zip(x_dates, weekdays):
            date_str = d.strftime('%m/%d')
            date_labels.append(f"{date_str}\n({wd})")
        
        ax.set_xticklabels(date_labels, rotation=45, ha='right')
        
        ax.set_title('今後1週間の入院患者数予測', fontsize=16, pad=15)
        ax.set_xlabel('日付', fontsize=12, labelpad=10)
        ax.set_ylabel('予測入院患者数', fontsize=12, labelpad=10)
        ax.grid(True, linestyle='--', alpha=0.7)
        
        # y軸の範囲を調整（最小値は0より少し小さく、最大値は少し大きく）
        min_val = max(0, min(values) * 0.9)
        max_val = max(values) * 1.1
        ax.set_ylim(min_val, max_val)
        
        # 各点に値を表示
        for i, val in enumerate(values):
            ax.annotate(f'{val:.1f}', (i, val), textcoords="offset points", 
                        xytext=(0, 10), ha='center', fontweight='bold')
        
        fig.tight_layout()
        return fig

    # メイン処理
    def main():
        # アプリ名を表示（カスタムスタイル適用）
        st.markdown("""
        <div style="text-align: center; background: linear-gradient(to right, #00467F, #A5CC82); padding: 1.2rem; border-radius: 10px; margin-bottom: 1rem; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
            <h1 style="color: white; margin: 0; font-weight: 700; font-size: 2.5rem;">🏥 BED: Bed Entry and Discharge Predictor</h1>
            <p style="color: white; opacity: 0.8; margin-top: 0.5rem; font-size: 1.2rem;">入院患者数予測システム</p>
        </div>
        """, unsafe_allow_html=True)
        
        # モバイル表示の切り替え機能
        st.sidebar.title("表示設定")
        if 'mobile_mode' not in st.session_state:
            st.session_state.mobile_mode = False
        
        st.session_state.mobile_mode = st.sidebar.checkbox(
            "モバイル画面に最適化", 
            value=st.session_state.mobile_mode,
            help="スマートフォンで閲覧している場合はチェックしてください"
        )
        
        # モバイルモードの場合、より小さなフォントサイズとレイアウトを使用
        if is_mobile_device():
            st.markdown("""
            <style>
            .main .block-container {
                padding-top: 1rem;
                padding-bottom: 1rem;
                padding-left: 1rem;
                padding-right: 1rem;
            }
            .stTitle {
                font-size: 1.5rem !important;
            }
            .stHeader {
                font-size: 1.3rem !important;
            }
            .stSubheader {
                font-size: 1.1rem !important;
            }
            </style>
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
        
        # 接続トラブルシューティング情報
        st.sidebar.title("トラブルシューティング")
        st.sidebar.info("""
        接続エラーが発生した場合:
        - ブラウザをリフレッシュしてください
        - 別のブラウザを試してください
        - アプリケーションを再起動してください
        """)
        
        # モデルとデータの読み込み
        model = load_model()
        df = load_data()
        
        if model is None or df is None:
            st.error("アプリケーションの初期化に失敗しました。必要なファイルが存在することを確認してください。")
            return
        
        # タブを作成（ラベル名を簡潔に統一）
        tab1, tab2, tab3, tab4 = st.tabs(["単一予測", "月間カレンダー", "シナリオ比較", "データ分析"])
        
        with tab1:
            st.markdown('<h2 style="color: #00467F; border-bottom: 2px solid #A5CC82; padding-bottom: 0.3rem;">今日の入院患者数を予測</h2>', unsafe_allow_html=True)
            
            st.write("👇 以下に今日のデータを入力して「予測実行」ボタンをクリックしてください")
            
            with st.form("single_prediction_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    # 曜日選択を日付選択に変更
                    selected_date = st.date_input(
                        "日付を選択",
                        value=datetime.now(),  # 今日の日付をデフォルト選択
                        format="YYYY/MM/DD"
                    )
                    
                    # 選択された日付から曜日を自動設定
                    selected_day = get_day_of_week_from_date(selected_date)
                    
                    # 祝日判定
                    is_holiday_flag = is_holiday(selected_date)
                    
                    # 日付情報を表示（曜日と祝日情報）
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
                with st.spinner("予測を実行中..."):
                    prediction = predict_admission(model, input_data)
                    
                    # セッションステートに予測結果を保存
                    if predict_button:
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
                
                # 現在の日付を取得
                today_date = datetime.now().strftime("%Y-%m-%d")
                
                # 1週間の予測を表示
                st.subheader("今後1週間の予測")
                
                # 複数日の予測を実行
                with st.spinner('1週間分の予測を計算中...'):
                    weekly_forecast = predict_multiple_days(model, input_data, datetime.now())
                
                # 表形式で表示
                weekly_df = pd.DataFrame(weekly_forecast)
                weekly_df['予測入院患者数'] = weekly_df['予測入院患者数'].round(1)
                
                # モバイル表示の場合はデータフレームのカラムを調整
                if is_mobile_device():
                    # モバイル向けに表示を最適化
                    mobile_df = weekly_df.copy()
                    mobile_df["日付（曜日）"] = mobile_df.apply(
                        lambda row: f"{row['日付']}（{row['曜日']}）", axis=1
                    )
                    mobile_df = mobile_df[["日付（曜日）", "予測入院患者数"]]
                    st.dataframe(mobile_df, use_container_width=True)
                else:
                    # PC表示の場合も祝日カラムを除外
                    st.dataframe(weekly_df[["日付", "曜日", "予測入院患者数"]], use_container_width=True)
                
                # グラフで表示 - モバイルの場合は小さめに
                weekly_chart = plot_weekly_forecast(weekly_forecast)
                st.pyplot(weekly_chart)
                
                # データ保存オプション
                st.divider()
                st.subheader("データの保存")
                
                save_col1, save_col2 = st.columns([3, 1])
                with save_col1:
                    st.markdown("""
                    **1日1回の正確なデータ保存**
                    
                    - 予測した日の実際の入院患者数を記録します
                    - 1日1回のみ保存可能です
                    - 正確な実数を入力してください
                    - 保存したデータは予測精度向上に使用されます
                    """)
                
                with save_col2:
                    if st.button("実数データを保存", key="save_prediction", type="primary", use_container_width=True):
                        # 実際の入院患者数をユーザーに入力してもらう
                        real_admission = st.number_input(
                            "実際の入院患者数（小数点以下も正確に入力）",
                            min_value=0.0,
                            max_value=1000.0,
                            value=float(prediction),
                            step=0.1,
                            key="real_admission_input"
                        )
                        
                        if st.button("確定して保存", key="confirm_save", use_container_width=True):
                            # CSVにデータを追加
                            success, message = append_data_to_csv(
                                today_date,
                                day_encoding,
                                input_data,
                                real_admission
                            )
                            
                            if success:
                                st.success("""
                                ✅ データを保存しました
                                
                                - 保存日時: {datetime.now().strftime('%Y年%m月%d日 %H:%M')}
                                - 保存データ: {real_admission:.1f}人
                                """)
                                # データの再読み込みを強制
                                st.cache_data.clear()
                                # セッションからデータをクリア
                                if "last_prediction" in st.session_state:
                                    del st.session_state.last_prediction
                                if "last_input_data" in st.session_state:
                                    del st.session_state.last_input_data
                                if "last_day_encoding" in st.session_state:
                                    del st.session_state.last_day_encoding
                                if "last_selected_day" in st.session_state:
                                    del st.session_state.last_selected_day
                                st.rerun()
                            else:
                                st.error(message)
        
        with tab2:
            st.markdown('<h2 style="color: #00467F; border-bottom: 2px solid #A5CC82; padding-bottom: 0.3rem;">月間混雑予想カレンダー</h2>', unsafe_allow_html=True)
            
            # 月選択
            today = datetime.now()
            current_year = today.year
            current_month = today.month
            
            col1, col2 = st.columns([1, 2])
            with col1:
                selected_month = st.selectbox(
                    "月を選択",
                    options=list(range(1, 13)),
                    index=current_month - 1
                )
            
            with col2:
                selected_year = st.selectbox(
                    "年を選択",
                    options=list(range(current_year - 1, current_year + 2)),
                    index=1  # 現在の年をデフォルト選択
                )
            
            # 病院パラメータ（平均値）
            st.subheader("病院平均パラメータ")
            
            col1, col2 = st.columns(2)
            with col1:
                if df is not None:
                    default_out = int(df['total_outpatient'].mean())
                    default_intro = int(df['intro_outpatient'].mean())
                else:
                    default_out = 500
                    default_intro = 20
                
                avg_total_outpatient = st.number_input("平均前日総外来患者数", min_value=0, max_value=2000, value=default_out, step=1)
                avg_intro_outpatient = st.number_input("平均前日紹介外来患者数", min_value=0, max_value=200, value=default_intro, step=1)
            
            with col2:
                if df is not None:
                    default_er = int(df['ER'].mean())
                    default_bed = int(df['bed_count'].mean())
                else:
                    default_er = 15
                    default_bed = 280
                
                avg_er = st.number_input("平均前日救急搬送患者数", min_value=0, max_value=100, value=default_er, step=1)
                avg_bed_count = st.number_input("平均現在の病床利用数", min_value=100, max_value=1000, value=default_bed, step=1)
            
            # 月間予測ボタン
            if st.button("カレンダーを表示", type="primary", use_container_width=True):
                with st.spinner("月間カレンダーを作成中..."):
                    # 選択された月の日数を取得
                    _, days_in_month = calendar.monthrange(selected_year, selected_month)
                    
                    # 月の初日から最終日までの日付リストを作成
                    month_dates = [date_type(selected_year, selected_month, day) for day in range(1, days_in_month + 1)]
                    
                    # 月間予測結果を格納する辞書
                    monthly_predictions = {}
                    
                    # 各日の予測を実行
                    for current_date in month_dates:
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
                        
                        # 予測用データの作成
                        # 曜日の one-hot エンコーディング
                        day_encoding = DAYS_DICT[day_of_week]
                        
                        # 外来患者数を曜日と祝日に応じて調整
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
                            'public_holiday': [1 if is_current_holiday else 0],
                            'public_holiday_previous_day': [1 if is_prev_holiday else 0],
                            'total_outpatient': [adjusted_outpatient],
                            'intro_outpatient': [adjusted_intro],
                            'ER': [adjusted_er],
                            'bed_count': [avg_bed_count]
                        })
                        
                        # 予測実行
                        prediction = predict_admission(model, input_data)
                        
                        # 結果を格納
                        monthly_predictions[current_date] = {
                            "予測入院患者数": prediction,
                            "曜日": day_of_week,
                            "祝日": is_current_holiday
                        }
                    
                    # 月間カレンダー表示関数の呼び出し
                    calendar_fig = plot_monthly_calendar(selected_year, selected_month, monthly_predictions)
                    st.pyplot(calendar_fig)
                    
                    # 混雑度を判定する関数（既存のget_busyness_level関数と同様）
                    def get_busyness_for_df(value, quartiles):
                        if value <= quartiles[0]:
                            return "少ない"
                        elif value <= quartiles[1]:
                            return "やや少ない"
                        elif value <= quartiles[2]:
                            return "やや多い"
                        else:
                            return "多い"
                    
                    # 予測値の四分位を計算
                    prediction_values = [monthly_predictions[d]["予測入院患者数"] for d in monthly_predictions.keys()]
                    quartiles = np.percentile(prediction_values, [25, 50, 75])
                    
                    # データテーブルとしても表示
                    predictions_df = pd.DataFrame({
                        "日付": [d.strftime("%Y/%m/%d") for d in monthly_predictions.keys()],
                        "曜日": [monthly_predictions[d]["曜日"] for d in monthly_predictions.keys()],
                        "祝日": ["はい" if monthly_predictions[d]["祝日"] else "いいえ" for d in monthly_predictions.keys()],
                        "混雑度": [get_busyness_for_df(monthly_predictions[d]["予測入院患者数"], quartiles) for d in monthly_predictions.keys()]
                    })
                    
                    # テーブル表示
                    st.write("※ 予測値は混雑度の目安として表示しています。実際の入院患者数とは異なる場合があります。")
                    st.dataframe(predictions_df, use_container_width=True)
        
        with tab3:
            st.markdown('<h2 style="color: #00467F; border-bottom: 2px solid #A5CC82; padding-bottom: 0.3rem;">シナリオ比較</h2>', unsafe_allow_html=True)
            
            st.write("👇 複数の条件で入院患者数を予測し、比較することができます")
            
            # 事前定義シナリオを使用するかカスタムシナリオを作成するか選択
            scenario_choice = st.radio(
                "シナリオ選択",
                ["事前定義シナリオを使用", "カスタムシナリオを作成"]
            )
            
            if scenario_choice == "事前定義シナリオを使用":
                # 事前定義シナリオ
                today = datetime.now()
                predefined_scenarios = [
                    {
                        "name": "月曜日、外来患者数が多い",
                        "date": (today + timedelta(days=(0 - today.weekday()) % 7)).strftime("%Y/%m/%d"),  # 次の月曜日
                        "public_holiday": 0, "public_holiday_previous_day": 0,
                        "total_outpatient": 800, "intro_outpatient": 30, "ER": 20, "bed_count": 280
                    },
                    {
                        "name": "火曜日、通常の外来患者数",
                        "date": (today + timedelta(days=(1 - today.weekday()) % 7)).strftime("%Y/%m/%d"),  # 次の火曜日
                        "public_holiday": 0, "public_holiday_previous_day": 0,
                        "total_outpatient": 600, "intro_outpatient": 20, "ER": 15, "bed_count": 280
                    },
                    {
                        "name": "水曜日、外来患者数が多い",
                        "date": (today + timedelta(days=(2 - today.weekday()) % 7)).strftime("%Y/%m/%d"),  # 次の水曜日
                        "public_holiday": 0, "public_holiday_previous_day": 0,
                        "total_outpatient": 750, "intro_outpatient": 25, "ER": 15, "bed_count": 280
                    },
                    {
                        "name": "土曜日、少ない外来患者数",
                        "date": (today + timedelta(days=(5 - today.weekday()) % 7)).strftime("%Y/%m/%d"),  # 次の土曜日
                        "public_holiday": 0, "public_holiday_previous_day": 0,
                        "total_outpatient": 200, "intro_outpatient": 5, "ER": 15, "bed_count": 280
                    },
                    {
                        "name": "祝日（平日想定）",
                        "date": (today + timedelta(days=1)).strftime("%Y/%m/%d"),  # 翌日
                        "public_holiday": 1, "public_holiday_previous_day": 0,
                        "total_outpatient": 100, "intro_outpatient": 3, "ER": 15, "bed_count": 280
                    }
                ]
                
                # シナリオを選択
                selected_scenarios = st.multiselect(
                    "比較するシナリオを選択",
                    [scenario["name"] for scenario in predefined_scenarios],
                    default=[scenario["name"] for scenario in predefined_scenarios]
                )
                
                # シナリオ比較実行ボタン
                if st.button("シナリオ比較実行", type="primary", use_container_width=True):
                    # 結果を格納するリスト
                    results = []
                    
                    # 選択されたシナリオで予測
                    with st.spinner('シナリオ予測を計算中...'):
                        for scenario_name in selected_scenarios:
                            # シナリオデータを取得
                            scenario_data = next(s for s in predefined_scenarios if s["name"] == scenario_name)
                            
                            # 名前と日付を除外してDataFrameに変換
                            name = scenario_data["name"]
                            date = scenario_data["date"]
                            
                            # 日付から曜日を取得
                            scenario_date = datetime.strptime(date, "%Y/%m/%d")
                            actual_day = get_day_of_week_from_date(scenario_date)
                            
                            # 曜日の one-hot エンコーディング
                            day_encoding = DAYS_DICT[actual_day]
                            
                            # 予測用データを作成
                            df_scenario = pd.DataFrame({
                                'mon': [day_encoding["mon"]],
                                'tue': [day_encoding["tue"]],
                                'wed': [day_encoding["wed"]],
                                'thu': [day_encoding["thu"]],
                                'fri': [day_encoding["fri"]],
                                'sat': [day_encoding["sat"]],
                                'sun': [day_encoding["sun"]],
                                'public_holiday': [scenario_data["public_holiday"]],
                                'public_holiday_previous_day': [scenario_data["public_holiday_previous_day"]],
                                'total_outpatient': [scenario_data["total_outpatient"]],
                                'intro_outpatient': [scenario_data["intro_outpatient"]],
                                'ER': [scenario_data["ER"]],
                                'bed_count': [scenario_data["bed_count"]]
                            })
                            
                            # 予測
                            prediction = predict_admission(model, df_scenario)
                            results.append({
                                "シナリオ": name, 
                                "日付": date, 
                                "曜日": actual_day, 
                                "予測入院患者数": prediction
                            })
                    
                    # 結果をDataFrameに変換して表示
                    results_df = pd.DataFrame(results)
                    
                    # モバイル表示の場合はデータフレームのカラムを調整
                    if is_mobile_device():
                        # モバイル向けに表示を最適化
                        mobile_results_df = results_df.copy()
                        mobile_results_df["シナリオ説明"] = mobile_results_df.apply(
                            lambda row: f"{row['シナリオ']}\n{row['日付']}（{row['曜日']}）", axis=1
                        )
                        mobile_results_df = mobile_results_df[["シナリオ説明", "予測入院患者数"]]
                        st.dataframe(mobile_results_df, use_container_width=True)
                    else:
                        st.dataframe(results_df, use_container_width=True)
                    
                    # グラフ表示 - モバイルの場合は高さを調整
                    fig_height = 4 if is_mobile_device() else 6
                    fig, ax = plt.subplots(figsize=(10, fig_height))
                    sns.barplot(x=[i for i in range(len(results_df))], y="予測入院患者数", data=results_df, ax=ax)
                    
                    # X軸のラベルに日付情報を追加
                    if len(results) > 0:
                        x_labels = [f"{row['シナリオ']}\n{row['日付']}\n({row['曜日']})" 
                                  for _, row in results_df.iterrows()]
                        ax.set_xticks(range(len(x_labels)))
                        ax.set_xticklabels(x_labels, rotation=45, ha="right")
                    
                    ax.set_title("シナリオ別予測入院患者数")
                    st.pyplot(fig)
                    
            else:  # カスタムシナリオを作成
                st.subheader("カスタムシナリオの作成")
                
                # シナリオの数を選択
                num_scenarios = st.number_input("作成するシナリオの数", min_value=1, max_value=5, value=2)
                
                custom_scenarios = []
                
                # シナリオごとに入力フォームを表示
                for i in range(num_scenarios):
                    st.markdown(f"### シナリオ {i+1}")
                    
                    # モバイルの場合は縦並び、PCの場合は横並び
                    if is_mobile_device():
                        col1 = st.container()
                        col2 = st.container()
                    else:
                        col1, col2 = st.columns(2)
                    
                    with col1:
                        scenario_name = st.text_input(f"シナリオ{i+1}の名前", value=f"シナリオ {i+1}")
                        
                        # 日付選択
                        scenario_date = st.date_input(
                            f"日付 (シナリオ{i+1})",
                            value=datetime.now() + timedelta(days=i),  # それぞれ異なる日付
                            key=f"scenario_date_{i}"
                        )
                        
                        # 日付から曜日を自動設定
                        day = get_day_of_week_from_date(scenario_date)
                        
                        st.write(f"選択日の曜日: **{day}**")
                        
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
                        
                        total_out = st.number_input(f"前日総外来患者数 (シナリオ{i+1})", min_value=0, value=default_out, step=1, key=f"out_{i}")
                        intro_out = st.number_input(f"前日紹介外来患者数 (シナリオ{i+1})", min_value=0, value=default_intro, step=1, key=f"intro_{i}")
                        er_count = st.number_input(f"前日救急搬送患者数 (シナリオ{i+1})", min_value=0, value=default_er, step=1, key=f"er_{i}")
                        bed = st.number_input(f"現在の病床利用数 (シナリオ{i+1})", min_value=0, value=default_bed, step=1, key=f"bed_{i}")
                    
                    # シナリオデータを作成
                    scenario = {
                        "name": scenario_name,
                        "date": scenario_date.strftime("%Y/%m/%d"),
                        "day": day,
                        "public_holiday": 1 if is_holiday(scenario_date) else 0,
                        "public_holiday_previous_day": 1 if is_previous_day_holiday(scenario_date) else 0,
                        "total_outpatient": total_out,
                        "intro_outpatient": intro_out,
                        "ER": er_count,
                        "bed_count": bed
                    }
                    
                    custom_scenarios.append(scenario)
                
                if st.button("カスタムシナリオ比較実行", type="primary", use_container_width=True):
                    # 結果を格納するリスト
                    results = []
                    
                    # 作成したシナリオで予測
                    with st.spinner('カスタムシナリオ予測を計算中...'):
                        for scenario in custom_scenarios:
                            # 基本データの抽出
                            name = scenario["name"]
                            date = scenario["date"]
                            day = scenario["day"]
                            
                            # 曜日のone-hotエンコーディング
                            day_encoding = DAYS_DICT[day]
                            
                            # 予測用のデータフレームを作成
                            df_scenario = pd.DataFrame({
                                'mon': [day_encoding["mon"]],
                                'tue': [day_encoding["tue"]],
                                'wed': [day_encoding["wed"]],
                                'thu': [day_encoding["thu"]],
                                'fri': [day_encoding["fri"]],
                                'sat': [day_encoding["sat"]],
                                'sun': [day_encoding["sun"]],
                                'public_holiday': [scenario["public_holiday"]],
                                'public_holiday_previous_day': [scenario["public_holiday_previous_day"]],
                                'total_outpatient': [scenario["total_outpatient"]],
                                'intro_outpatient': [scenario["intro_outpatient"]],
                                'ER': [scenario["ER"]],
                                'bed_count': [scenario["bed_count"]]
                            })
                            
                            # 予測
                            prediction = predict_admission(model, df_scenario)
                            results.append({
                                "シナリオ": name, 
                                "日付": date, 
                                "曜日": day, 
                                "予測入院患者数": prediction
                            })
                    
                    # 結果をDataFrameに変換して表示
                    results_df = pd.DataFrame(results)
                    
                    # モバイル表示の場合はデータフレームのカラムを調整
                    if is_mobile_device():
                        # モバイル向けに表示を最適化
                        mobile_results_df = results_df.copy()
                        mobile_results_df["シナリオ説明"] = mobile_results_df.apply(
                            lambda row: f"{row['シナリオ']}\n{row['日付']}（{row['曜日']}）", axis=1
                        )
                        mobile_results_df = mobile_results_df[["シナリオ説明", "予測入院患者数"]]
                        st.dataframe(mobile_results_df, use_container_width=True)
                    else:
                        st.dataframe(results_df, use_container_width=True)
                    
                    # グラフ表示 - モバイルの場合は高さを調整
                    fig_height = 4 if is_mobile_device() else 6
                    fig, ax = plt.subplots(figsize=(10, fig_height))
                    sns.barplot(x=[i for i in range(len(results_df))], y="予測入院患者数", data=results_df, ax=ax)
                    
                    # X軸のラベルに日付情報を追加
                    if len(results) > 0:
                        x_labels = [f"{row['シナリオ']}\n{row['日付']}\n({row['曜日']})" 
                                  for _, row in results_df.iterrows()]
                        ax.set_xticks(range(len(x_labels)))
                        ax.set_xticklabels(x_labels, rotation=45, ha="right")
                    
                    ax.set_title("シナリオ別予測入院患者数")
                    st.pyplot(fig)
        
        with tab4:
            st.markdown('<h2 style="color: #00467F; border-bottom: 2px solid #A5CC82; padding-bottom: 0.3rem;">データ分析</h2>', unsafe_allow_html=True)
            
            # CSVデータが読み込めた場合のみ分析を表示
            if df is not None:
                # データサンプルを表示
                st.subheader("データサンプル")
                
                # モバイル表示の場合はデータフレームの表示行数を減らす
                if is_mobile_device():
                    st.dataframe(df.head(3), use_container_width=True)
                else:
                    st.dataframe(df.head(), use_container_width=True)
                
                # データの基本統計量
                st.subheader("基本統計量")
                
                # モバイル表示の場合は統計量を選択的に表示
                if is_mobile_device():
                    # 重要な統計だけを表示
                    selected_stats = df.describe().loc[['mean', 'min', 'max'], :]
                    st.dataframe(selected_stats, use_container_width=True)
                else:
                    st.dataframe(df.describe(), use_container_width=True)
                
                # データの可視化
                with st.spinner('データ分析を実行中...'):
                    visualize_data(df)
            else:
                st.warning("CSVデータが読み込めないため、データ分析を表示できません。")

    # 月間カレンダー表示関数
    def plot_monthly_calendar(year, month, predictions):
        # 日本語フォント設定
        set_japanese_font()
        
        # 月の日数と最初の日の曜日（0=月曜日）を取得
        first_day, days_in_month = calendar.monthrange(year, month)
        
        # カレンダーの行数を計算（月の最初の日が日曜日でなければ追加の行が必要）
        num_rows = (days_in_month + first_day + 6) // 7
        
        # 予測値のリストから統計量を計算
        prediction_values = [data["予測入院患者数"] for data in predictions.values()]
        quartiles = np.percentile(prediction_values, [25, 50, 75])
        
        # 各日付のセルの色を決定する関数
        def get_cell_color(value):
            if value <= quartiles[0]:
                return "#a1d99b"  # 薄い緑（少ない）
            elif value <= quartiles[1]:
                return "#fee391"  # 薄い黄色（やや少ない）
            elif value <= quartiles[2]:
                return "#fc9272"  # オレンジ（やや多い）
            else:
                return "#de2d26"  # 赤（多い）
        
        # 混雑度の文字表現
        def get_busyness_level(value):
            if value <= quartiles[0]:
                return "少ない"
            elif value <= quartiles[1]:
                return "やや少ない"
            elif value <= quartiles[2]:
                return "やや多い"
            else:
                return "多い"
        
        # カレンダー表示用のプロット設定
        fig, ax = plt.subplots(figsize=(12, 8))
        fig.patch.set_facecolor('#f8f9fa')
        ax.set_facecolor('#f8f9fa')
        
        # プロットの設定
        ax.set_xlim(0, 7)
        ax.set_ylim(0, num_rows)
        ax.set_xticks(np.arange(0.5, 7.5))
        ax.set_yticks(np.arange(0.5, num_rows + 0.5))
        
        # 曜日ラベルの設定（日本語で表示）
        weekday_labels = ['月', '火', '水', '木', '金', '土', '日']
        ax.set_xticklabels(weekday_labels, fontsize=12, fontweight='bold')
        ax.set_yticklabels([])
        
        # グリッド線の設定
        ax.grid(True, color='#cccccc', linestyle='-', linewidth=0.5)
        
        # タイトルの設定
        month_name = ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月'][month - 1]
        ax.set_title(f"{year}年 {month_name} 入院患者数予測", fontsize=16, pad=20, fontweight='bold')
        
        # カレンダーの日付とデータを配置
        for day in range(1, days_in_month + 1):
            current_date = date_type(year, month, day)
            
            # カレンダー上の位置を計算
            weekday = (current_date.weekday() + 7) % 7
            week = (day + first_day - 1) // 7
            
            # first_day調整（月曜日を0とする）
            adjusted_weekday = (current_date.weekday()) % 7
            
            # セルの位置
            x = adjusted_weekday
            y = num_rows - 1 - week
            
            # 予測データ取得
            prediction_data = predictions[current_date]
            value = prediction_data["予測入院患者数"]
            is_holiday = prediction_data["祝日"]
            
            # セルの背景色
            cell_color = get_cell_color(value)
            
            # セルの描画
            rect = plt.Rectangle((x, y), 1, 1, facecolor=cell_color, alpha=0.7, edgecolor='black', linewidth=1)
            ax.add_patch(rect)
            
            # 日付表示（祝日なら赤字）
            if is_holiday:
                date_color = 'red'
            elif adjusted_weekday == 6:  # 日曜日
                date_color = 'red'
            elif adjusted_weekday == 5:  # 土曜日
                date_color = 'blue'
            else:
                date_color = 'black'
            
            # 日付の表示
            ax.text(x + 0.05, y + 0.75, f"{day}", fontsize=12, fontweight='bold', color=date_color)
            
            # 混雑度の表示（中央に配置）
            busyness_level = get_busyness_level(value)
            ax.text(x + 0.5, y + 0.3, busyness_level, fontsize=10, ha='center', fontweight='bold')
        
        # 凡例の追加
        legend_labels = ["少ない", "やや少ない", "やや多い", "多い"]
        legend_colors = ["#a1d99b", "#fee391", "#fc9272", "#de2d26"]
        patches = [mpatches.Patch(color=color, label=label) for color, label in zip(legend_colors, legend_labels)]
        ax.legend(handles=patches, loc="upper right", title="混雑度")
        
        # レイアウトの調整
        plt.tight_layout()
        plt.subplots_adjust(top=0.9)
        
        return fig

    if __name__ == "__main__":
        main()

except Exception as conn_error:
    # 接続エラー時の処理
    st.error(f"接続エラーが発生しました: {conn_error}")
    st.session_state.connection_attempts += 1
    
    if st.session_state.connection_attempts <= 3:
        st.warning(f"再接続を試みています... (試行: {st.session_state.connection_attempts}/3)")
        st.rerun()
    else:
        st.error("接続の再試行に失敗しました。以下の対処法を試してください:")
        st.code("""
        1. ブラウザの更新ボタンをクリックする
        2. 別のブラウザを試してください
        3. アプリケーションを再起動する:
           - ターミナルで Ctrl+C を押してアプリケーションを終了
           - 再度 ./run_app.sh または python run_app.py を実行
        """) 
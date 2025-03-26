import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import jpholiday
from hospital_data_manager import HospitalDataManager
import os
from dotenv import load_dotenv

# 環境変数の読み込み
load_dotenv()

# データ管理クラスの初期化
data_manager = HospitalDataManager()

# 病院リストの取得
hospital_list = data_manager.get_hospital_list()
if not hospital_list:
    # 初期データの設定
    initial_hospital = {
        "hospital_id": "h001",
        "name": "サンプル病院",
        "location": "東京都",
        "beds": 200
    }
    data_manager.update_hospital_metadata("h001", initial_hospital)
    data_manager.update_hospital_list([initial_hospital])
    hospital_list = [initial_hospital]

# Streamlitアプリケーションの設定
st.set_page_config(
    page_title="BED: Bed Entry and Discharge Predictor",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# アプリケーションのメイン関数
    def main():
        # アプリ名を表示（カスタムスタイル適用）
        st.markdown("""
        <div style="text-align: center; background: linear-gradient(to right, #00467F, #A5CC82); padding: 1.2rem; border-radius: 10px; margin-bottom: 1rem; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
            <h1 style="color: white; margin: 0; font-weight: 700; font-size: 2.5rem;">🏥 BED: Bed Entry and Discharge Predictor</h1>
            <p style="color: white; opacity: 0.8; margin-top: 0.5rem; font-size: 1.2rem;">入院患者数予測システム</p>
        </div>
        """, unsafe_allow_html=True)
        
    # 病院選択
    hospital_id = st.selectbox(
        "病院を選択",
        [h["hospital_id"] for h in hospital_list],
        format_func=lambda x: next(h["name"] for h in hospital_list if h["hospital_id"] == x)
    )
    
    # 病院情報の表示
    metadata = data_manager.get_hospital_metadata(hospital_id)
    st.sidebar.title(f"{metadata['name']} 情報")
    st.sidebar.info(f"所在地: {metadata['location']}\n病床数: {metadata['beds']}")
    
    # データの読み込み
    df = data_manager.get_hospital_data(hospital_id)
    model = data_manager.load_model(hospital_id)
    
    if df.empty or model is None:
        st.error("この病院のデータまたはモデルが存在しません。管理者に連絡してください。")
        return
    
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
        
        # タブを作成（ラベル名を簡潔に統一）
        tab1, tab2, tab3, tab4 = st.tabs(["単一予測", "月間カレンダー", "シナリオ比較", "データ分析"])
        
    # 以下、既存のタブ処理コード
    # ... (既存のコードをそのまま使用)

# アプリケーションのエントリーポイント
app = main

    if __name__ == "__main__":
        main()
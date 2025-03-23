#!/usr/bin/env python3

import os
import sys
import subprocess

# Streamlit初期セットアップをスキップするための環境変数を設定
# 複数の環境変数を設定して確実にスキップ
os.environ['STREAMLIT_EMAIL'] = ""
os.environ['STREAMLIT_SHARING_ANALYTICS_OPT_OUT'] = "true"
os.environ['STREAMLIT_ANALYTICS_OPT_OUT'] = "true"
os.environ['STREAMLIT_BROWSER_GATHER_USAGE_STATS'] = "false"

# アプリケーションが存在するディレクトリに移動
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

# Streamlitコマンドを実行
try:
    print("入院患者数予測システムを起動しています...")
    print("ブラウザが自動的に開かない場合は http://localhost:8501 にアクセスしてください。")
    
    # 接続問題を解決するためにオプションを変更
    # サーバーのホスト設定を修正し、localhostにバインド
    cmd = [
        sys.executable, 
        "-m", 
        "streamlit", 
        "run", 
        "app.py", 
        "--server.enableCORS=false", 
        "--server.enableXsrfProtection=false", 
        "--server.address=127.0.0.1", 
        "--server.port=8501",
        "--browser.serverAddress=localhost",
        "--browser.gatherUsageStats=false",
        "--server.headless=true"
    ]
    subprocess.run(cmd)
except KeyboardInterrupt:
    print("\nアプリケーションを終了しました。")
except Exception as e:
    print(f"エラーが発生しました: {e}")
    print("\n以下のコマンドを直接実行してみてください:")
    print("  streamlit run app.py --server.address=localhost --server.headless=true")
    print("または")
    print("  python -m streamlit run app.py --server.address=localhost --server.headless=true") 
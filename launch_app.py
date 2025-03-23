#!/usr/bin/env python3
"""
簡易起動スクリプト - コネクションエラー解決用
"""

import os
import sys
import subprocess
import time
import signal
import platform

# プロセス終了用のハンドラ
def signal_handler(sig, frame):
    print("\nアプリケーションを終了しています...")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

def main():
    # 現在の作業ディレクトリを取得
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # 環境変数を設定
    os.environ['STREAMLIT_EMAIL'] = ""
    os.environ['STREAMLIT_SHARING_ANALYTICS_OPT_OUT'] = "true"
    os.environ['STREAMLIT_ANALYTICS_OPT_OUT'] = "true"
    os.environ['STREAMLIT_BROWSER_GATHER_USAGE_STATS'] = "false"
    
    # Streamlitプロセスを終了（Windowsとその他のプラットフォームで異なる方法を使用）
    if platform.system() == "Windows":
        try:
            subprocess.run(["taskkill", "/F", "/IM", "streamlit.exe"], stderr=subprocess.DEVNULL)
        except:
            pass
    else:
        try:
            subprocess.run(["pkill", "-f", "streamlit"], stderr=subprocess.DEVNULL)
        except:
            pass
    
    # 少し待機
    time.sleep(1)
    
    print("=== 入院患者数予測システム 簡易起動ツール ===")
    print("接続問題を解決するための特別バージョン")
    print("\n起動中...")
    
    # 使用するポートを決定
    port = 8501
    # ポートが使用中かチェック（シンプルな方法）
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(("localhost", port))
        s.close()
    except socket.error:
        port = 8502
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.bind(("localhost", port))
            s.close()
        except socket.error:
            port = 8503
    
    print(f"アクセス先: http://localhost:{port}")
    print("ブラウザが自動的に開かない場合は上記URLをブラウザに入力してください")
    
    # Streamlitコマンドを実行
    cmd = [
        sys.executable, 
        "-m", 
        "streamlit", 
        "run", 
        "app.py", 
        "--server.enableCORS=false", 
        "--server.enableXsrfProtection=false", 
        "--server.address=localhost", 
        f"--server.port={port}", 
        "--browser.serverAddress=localhost", 
        "--browser.gatherUsageStats=false",
        "--server.headless=true"
    ]
    
    process = None
    try:
        process = subprocess.Popen(cmd)
        # ユーザーが Ctrl+C を押すまで待機
        process.wait()
    except KeyboardInterrupt:
        if process:
            process.terminate()
        print("\nアプリケーションを終了しました。")
    except Exception as e:
        print(f"\nエラーが発生しました: {e}")
        print("\n問題が解決しない場合は、以下の対処法を試してください:")
        print("1. 別のブラウザ（Chrome、Firefox、Safariなど）でアクセスする")
        print("2. ファイアウォール設定を確認する")
        print(f"3. 直接 http://localhost:{port} にアクセスする")
        print("\nまたは以下のコマンドを直接実行してみてください:")
        print(f"  streamlit run app.py --server.address=localhost --server.port={port} --server.headless=true")

if __name__ == "__main__":
    main() 
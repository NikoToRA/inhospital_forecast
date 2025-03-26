import streamlit.web.bootstrap as bootstrap
import os
import sys

def run_streamlit():
    # Streamlitアプリのパスを設定
    app_path = "app.py"
    
    # コマンドライン引数を設定
    args = [
        "--server.port", str(os.environ.get("PORT", 8501)),
        "--server.headless", "true",
        "--browser.serverAddress", "0.0.0.0",
        "--server.enableCORS", "false",
        "--browser.serverPort", str(os.environ.get("PORT", 8501)),
        "--browser.gatherUsageStats", "false"
    ]
    
    # Streamlitアプリを起動
    sys.argv = ["streamlit", "run", app_path] + args
    bootstrap.run(app_path, "", args, flag_options={})

if __name__ == "__main__":
    run_streamlit() 
import streamlit as st
from app import main
import os
import sys

# Streamlitアプリをwebサーバモードで実行
if __name__ == "__main__":
    # 環境変数を設定
    os.environ["STREAMLIT_SERVER_PORT"] = str(os.environ.get("PORT", 8000))
    os.environ["STREAMLIT_SERVER_HEADLESS"] = "true"
    
    # Streamlitアプリを実行
    sys.argv = ["streamlit", "run", "app.py"]
    main() 
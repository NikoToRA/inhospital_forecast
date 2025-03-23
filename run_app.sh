#!/bin/bash

# スクリプトの場所を取得
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Streamlit初期セットアップをスキップする環境変数を設定 - 複数の変数を設定
export STREAMLIT_EMAIL=""
export STREAMLIT_SHARING_ANALYTICS_OPT_OUT="true"
export STREAMLIT_ANALYTICS_OPT_OUT="true"
export STREAMLIT_BROWSER_GATHER_USAGE_STATS="false"

echo "入院患者数予測システムを起動しています..."
echo "ブラウザが自動的に開かない場合は http://localhost:8501 にアクセスしてください。"

# 実行中のStreamlitプロセスを終了
pkill -f streamlit 2>/dev/null || true
sleep 1

# Pythonの実行パスを確認
PYTHON_PATH=$(which python3)
if [ $? -ne 0 ]; then
    PYTHON_PATH=$(which python)
fi

# ポートが使用されていないか確認し、必要に応じて別のポートを使用
PORT=8501
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null ; then
    echo "ポート $PORT はすでに使用されています。ポート 8502 を使用します。"
    PORT=8502
fi

# Streamlitを実行 - 接続エラー解決のためにオプションを変更
$PYTHON_PATH -m streamlit run app.py \
    --server.enableCORS=false \
    --server.enableXsrfProtection=false \
    --server.address=localhost \
    --server.port=$PORT \
    --browser.serverAddress=localhost \
    --browser.gatherUsageStats=false \
    --server.headless=true

# エラー発生時のメッセージ
if [ $? -ne 0 ]; then
    echo "エラーが発生しました。"
    echo "以下のコマンドを直接実行してみてください:"
    echo "  streamlit run app.py --server.address=localhost --server.headless=true"
    echo "または"
    echo "  python -m streamlit run app.py --server.address=localhost --server.headless=true"
fi 
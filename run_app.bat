@echo off
echo 入院患者数予測システムを起動しています...
echo ブラウザが自動的に開かない場合は http://localhost:8501 にアクセスしてください。

set STREAMLIT_EMAIL=

:: 修正したコマンドで直接streamlitを実行 (接続エラー解決用)
python -m streamlit run app.py --server.enableCORS=false --server.enableXsrfProtection=false --server.address=127.0.0.1 --server.port=8501

if %ERRORLEVEL% NEQ 0 (
    echo エラーが発生しました。
    echo 以下のコマンドを直接実行してみてください:
    echo   streamlit run app.py --server.address=127.0.0.1
    echo または
    echo   python -m streamlit run app.py --server.address=127.0.0.1
    pause
) 
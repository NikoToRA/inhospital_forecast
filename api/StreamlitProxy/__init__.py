import azure.functions as func
import subprocess
import sys
import os
import logging

def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        logging.info('Streamlitアプリケーションを起動します。')
        
        # 現在のディレクトリを取得
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # 環境変数の設定
        streamlit_env = os.environ.copy()
        streamlit_env['STREAMLIT_SERVER_HEADLESS'] = 'true'
        streamlit_env['STREAMLIT_SERVER_PORT'] = '8501'
        
        # Streamlitアプリを実行
        cmd = [sys.executable, '-m', 'streamlit', 'run', os.path.join(current_dir, 'StreamlitApp.py')]
        
        # 応答を返す
        return func.HttpResponse(
            "Streamlitアプリケーションへのリダイレクト用ページです。<script>window.location.href = '/streamlit';</script>",
            mimetype="text/html"
        )
        
    except Exception as e:
        logging.error(f"エラーが発生しました: {str(e)}")
        return func.HttpResponse(
            f"Streamlitアプリケーションの起動に失敗しました: {str(e)}",
            status_code=500
        ) 
# Gunicorn設定ファイル
import multiprocessing
import os

# ワーカー数を設定（CPUコア数×2+1の推奨値）
workers = 1  # Streamlitアプリは通常1つのワーカーで十分

# ワーカークラスをasyncioベースに設定
worker_class = 'uvicorn.workers.UvicornWorker'

# バインドするアドレスとポート
bind = "0.0.0.0:" + str(os.getenv("PORT", 8000))

# タイムアウト設定
timeout = 600  # 予測処理に時間がかかる可能性を考慮して長めに設定

# メモリ使用量制限を緩和（デフォルトは512MB）
worker_tmp_dir = '/dev/shm'  # 共有メモリを使用
worker_max_requests = 1000   # 一定リクエスト後にワーカー再起動

# ログ設定
loglevel = 'info'
accesslog = '-'
errorlog = '-'
capture_output = True        # アプリケーションの出力もログに含める 
#!/bin/bash
# アプリケーション起動スクリプト

# ログディレクトリの作成
mkdir -p /home/LogFiles

# 日付付きで実行ログを記録
echo "起動スクリプト実行開始: $(date)" > /home/LogFiles/startup.log

# 環境変数の設定
export PYTHONPATH=/home/site/wwwroot
export TZ=Asia/Tokyo

# 日本語フォントのインストール（管理者権限が必要な場合はコメントアウト）
# bash /home/site/wwwroot/install_fonts.sh

# アプリケーションの起動
echo "アプリケーションを起動します: $(date)" >> /home/LogFiles/startup.log
cd /home/site/wwwroot
gunicorn asgi:app --config gunicorn.conf.py 
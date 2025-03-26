#!/bin/bash
# 日本語フォントをインストールするスクリプト

# スクリプト実行ログを記録
echo "日本語フォントインストールスクリプトを実行中..." > /home/LogFiles/font_install.log

# 必要なパッケージをインストール
apt-get update >> /home/LogFiles/font_install.log 2>&1
apt-get install -y fonts-ipafont fonts-ipaexfont >> /home/LogFiles/font_install.log 2>&1
apt-get install -y fonts-noto-cjk >> /home/LogFiles/font_install.log 2>&1

# インストールしたフォントの一覧を確認
fc-list | grep -i japanese >> /home/LogFiles/font_install.log 2>&1
fc-list | grep -i ipa >> /home/LogFiles/font_install.log 2>&1
fc-list | grep -i noto >> /home/LogFiles/font_install.log 2>&1

# フォントキャッシュを更新
fc-cache -f -v >> /home/LogFiles/font_install.log 2>&1

echo "日本語フォントのインストールが完了しました" >> /home/LogFiles/font_install.log 
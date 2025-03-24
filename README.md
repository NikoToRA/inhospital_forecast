# BED: Bed Entry and Discharge Predictor

入院患者数予測システム

## 機能

- 単一予測：特定の日の入院患者数を予測
- 月間カレンダー：一ヶ月分の入院患者数予測をカレンダー表示
- シナリオ比較：複数の条件で入院患者数を予測し比較
- データ分析：過去データの分析と可視化

## セットアップ

1. 必要なパッケージのインストール:
```bash
pip install -r requirements.txt
```

2. 環境変数の設定:
- `.env`ファイルを作成し、以下の情報を設定:
```
AZURE_STORAGE_CONNECTION_STRING=your_connection_string_here
AZURE_STORAGE_CONTAINER_NAME=hospital-data
```

3. アプリケーションの起動:
```bash
streamlit run app.py
```

## Azure Web Appへのデプロイ

1. Azure CLIのインストールとログイン:
```bash
# Azure CLIのインストール
brew install azure-cli

# Azureへのログイン
az login
```

2. Azure Web Appの作成:
```bash
# リソースグループの作成
az group create --name bed-predictor-rg --location japaneast

# App Serviceプランの作成
az appservice plan create --name bed-predictor-plan --resource-group bed-predictor-rg --sku B1 --is-linux

# Web Appの作成
az webapp create --resource-group bed-predictor-rg --plan bed-predictor-plan --name bed-predictor --runtime "PYTHON:3.9"
```

3. 環境変数の設定:
```bash
az webapp config appsettings set --name bed-predictor --resource-group bed-predictor-rg --settings \
  AZURE_STORAGE_CONNECTION_STRING="your_connection_string_here" \
  AZURE_STORAGE_CONTAINER_NAME="hospital-data"
```

4. デプロイ:
```bash
# GitHubからのデプロイ
az webapp deployment source config --name bed-predictor --resource-group bed-predictor-rg --repo-url "your_github_repo_url" --branch main
```

## 注意事項

- 本アプリケーションは予測モデルを使用しており、実際の入院患者数とは異なる場合があります
- データの更新は1日1回のみ可能です
- 予測精度を向上させるため、実際の入院患者数を記録することを推奨します

## ライセンス

MIT License 
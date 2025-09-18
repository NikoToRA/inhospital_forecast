# 病院内予測システム (Hospital Forecast System)

機械学習モデルを使用して病院の入院患者数を予測するWebアプリケーションです。

## アーキテクチャ

### Azure クラウドアーキテクチャ
- **Azure App Service**: Flask WebアプリケーションとReactフロントエンドのホスティング
- **Azure Database for PostgreSQL**: 予測履歴とアプリケーションデータの保存
- **Azure Blob Storage**: 機械学習モデルファイルとCSVデータの保存
- **Azure DevOps/GitHub Actions**: CI/CDパイプライン

### アプリケーション構成
- **バックエンド**: Python Flask + scikit-learn
- **フロントエンド**: React.js
- **機械学習**: Random Forest回帰モデル (Prophet代替オプション)
- **データベース**: PostgreSQL
- **ストレージ**: Azure Blob Storage

## 機能

- ✅ 入院患者数の予測 (単日/週間)
- ✅ 予測履歴の記録と表示
- ✅ シナリオベースの予測
- ✅ Azure Blob StorageからのMLモデル自動読み込み
- ✅ PostgreSQLによる予測ログ管理
- ✅ レスポンシブなWeb UI

## Azure デプロイメント

### 前提条件
- Azure CLI インストール済み
- Azure サブスクリプション
- GitHub リポジトリ

### 1. インフラストラクチャのデプロイ

```bash
# Azure CLIでログイン
az login

# リソースグループとインフラをデプロイ
cd azure
./deploy.sh <resource-group-name>
```

### 2. アプリケーションのデプロイ

#### GitHub Actions使用の場合:
1. GitHub リポジトリの Settings > Secrets で以下を設定:
   - `AZURE_WEBAPP_NAME`: Webアプリ名
   - `AZURE_WEBAPP_PUBLISH_PROFILE`: アプリサービスの発行プロファイル

2. `.github/workflows/azure-webapps-python.yml` ワークフローが自動実行

#### Azure DevOps使用の場合:
1. `azure/azure-pipelines.yml` をAzure DevOpsにインポート
2. Azure サービス接続を設定
3. パイプラインを実行

### 3. モデルファイルのアップロード

```bash
# Azure Storage にモデルをアップロード
az storage blob upload \
  --account-name <storage-account-name> \
  --container-name models \
  --name fixed_rf_model.joblib \
  --file fixed_rf_model.joblib

# CSVデータのアップロード
az storage blob upload \
  --account-name <storage-account-name> \
  --container-name models \
  --name ultimate_pickup_data.csv \
  --file ultimate_pickup_data.csv
```

## ローカル開発

### 環境設定

```bash
# Python仮想環境
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt

# Node.js環境
cd frontend
npm install
```

### 環境変数設定

```bash
# backend/.env ファイルを作成
cp backend/.env.example backend/.env
# 必要な値を設定
```

### 実行

```bash
# バックエンド (ターミナル1)
cd backend
python app.py

# フロントエンド (ターミナル2)
cd frontend
npm start
```

## API エンドポイント

### 予測関連
- `POST /api/predict` - 単日予測
- `POST /api/predict_week` - 週間予測
- `GET /api/scenarios` - サンプルシナリオ取得

### 管理機能
- `GET /api/health` - ヘルスチェック
- `GET /api/history?limit=100` - 予測履歴取得
- `GET /api/storage/status` - Azure Storage & DB状態確認

## 設定

### 環境変数
| 変数名 | 説明 | 例 |
|--------|------|-----|
| `AZURE_STORAGE_CONNECTION_STRING` | Azure Storage接続文字列 | `DefaultEndpointsProtocol=https;AccountName=...` |
| `AZURE_STORAGE_CONTAINER` | ストレージコンテナ名 | `models` |
| `DATABASE_URL` | PostgreSQL接続URL | `postgresql://user:pass@host:port/db` |
| `FLASK_ENV` | Flask環境 | `production` |

### Azure App Service設定
- Python Runtime: 3.9
- Startup Command: `gunicorn --bind=0.0.0.0 --timeout 600 app:app`
- Always On: 有効

## トラブルシューティング

### よくある問題

1. **モデルが見つからない**
   - Azure Blob Storageにモデルファイルがアップロードされているか確認
   - ストレージアカウントのアクセス権限を確認

2. **データベース接続エラー**
   - PostgreSQLサーバーのファイアウォール設定を確認
   - 接続文字列の形式を確認

3. **デプロイ失敗**
   - Azure CLI のバージョンを確認
   - リソースグループの権限を確認

### ログの確認

```bash
# Azure App Service ログストリーム
az webapp log tail --name <app-name> --resource-group <resource-group>

# Azure Storage 内容確認
az storage blob list --account-name <storage-account> --container-name models
```

## アーキテクチャ図

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   React Frontend │    │  Flask Backend   │    │  Azure Storage  │
│                 │────│                  │────│                 │
│  - Dashboard    │    │  - ML Prediction │    │  - Model Files  │
│  - Forms        │    │  - API Endpoints │    │  - CSV Data     │
│  - Visualizations│   │  - Database ORM  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                │
                       ┌─────────────────┐
                       │ Azure PostgreSQL│
                       │                 │
                       │ - Prediction Log│
                       │ - App Settings  │
                       │ - Scenario Cache│
                       └─────────────────┘
```

## コントリビューション

1. このリポジトリをフォーク
2. フィーチャーブランチを作成
3. 変更をコミット
4. プルリクエストを作成

## ライセンス

MIT License
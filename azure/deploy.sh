#!/bin/bash

# Azure インフラストラクチャデプロイスクリプト
# 使用方法: ./deploy.sh <resource-group-name> [subscription-id]

set -e

# 色付きの出力のための関数
print_status() {
    echo -e "\033[32m[INFO]\033[0m $1"
}

print_error() {
    echo -e "\033[31m[ERROR]\033[0m $1"
}

print_warning() {
    echo -e "\033[33m[WARNING]\033[0m $1"
}

# パラメータチェック
if [ $# -lt 1 ]; then
    print_error "使用方法: $0 <resource-group-name> [subscription-id]"
    exit 1
fi

RESOURCE_GROUP=$1
SUBSCRIPTION_ID=${2:-""}
LOCATION="Japan East"
DEPLOYMENT_NAME="inhospital-forecast-deployment-$(date +%Y%m%d-%H%M%S)"

print_status "病院内予測システム Azureデプロイを開始します..."

# Azure CLIの確認
if ! command -v az &> /dev/null; then
    print_error "Azure CLI がインストールされていません。"
    print_error "インストール方法: https://docs.microsoft.com/ja-jp/cli/azure/install-azure-cli"
    exit 1
fi

# Azure ログイン確認
print_status "Azure ログイン状態を確認中..."
if ! az account show &> /dev/null; then
    print_warning "Azureにログインしていません。ログインを開始します..."
    az login
fi

# サブスクリプション設定
if [ -n "$SUBSCRIPTION_ID" ]; then
    print_status "サブスクリプションを設定中: $SUBSCRIPTION_ID"
    az account set --subscription "$SUBSCRIPTION_ID"
fi

CURRENT_SUBSCRIPTION=$(az account show --query "name" -o tsv)
print_status "現在のサブスクリプション: $CURRENT_SUBSCRIPTION"

# リソースグループの作成確認
print_status "リソースグループの確認中: $RESOURCE_GROUP"
if ! az group show --name "$RESOURCE_GROUP" &> /dev/null; then
    print_status "リソースグループを作成中: $RESOURCE_GROUP"
    az group create --name "$RESOURCE_GROUP" --location "$LOCATION"
else
    print_status "リソースグループが既に存在します: $RESOURCE_GROUP"
fi

# ARM テンプレートの検証
print_status "ARM テンプレートを検証中..."
if az deployment group validate \
    --resource-group "$RESOURCE_GROUP" \
    --template-file deploy.json \
    --parameters @parameters.json &> /dev/null; then
    print_status "テンプレート検証: 成功"
else
    print_error "テンプレート検証: 失敗"
    print_error "パラメータファイルを確認してください: parameters.json"
    exit 1
fi

# デプロイ実行
print_status "Azureリソースのデプロイを開始中..."
print_status "デプロイ名: $DEPLOYMENT_NAME"

az deployment group create \
    --resource-group "$RESOURCE_GROUP" \
    --name "$DEPLOYMENT_NAME" \
    --template-file deploy.json \
    --parameters @parameters.json \
    --verbose

# デプロイ結果の取得
if az deployment group show --resource-group "$RESOURCE_GROUP" --name "$DEPLOYMENT_NAME" --query "properties.provisioningState" -o tsv | grep -q "Succeeded"; then
    print_status "✅ デプロイが正常に完了しました！"

    # 出力値の表示
    print_status "デプロイ結果:"

    WEB_APP_URL=$(az deployment group show --resource-group "$RESOURCE_GROUP" --name "$DEPLOYMENT_NAME" --query "properties.outputs.webAppUrl.value" -o tsv)
    POSTGRES_FQDN=$(az deployment group show --resource-group "$RESOURCE_GROUP" --name "$DEPLOYMENT_NAME" --query "properties.outputs.postgresqlServerFqdn.value" -o tsv)
    STORAGE_NAME=$(az deployment group show --resource-group "$RESOURCE_GROUP" --name "$DEPLOYMENT_NAME" --query "properties.outputs.storageAccountName.value" -o tsv)

    echo ""
    echo "🌐 Web App URL: $WEB_APP_URL"
    echo "🗄️  PostgreSQL Server: $POSTGRES_FQDN"
    echo "💾 Storage Account: $STORAGE_NAME"
    echo ""

    print_status "次のステップ:"
    echo "1. GitHub Actions または Azure DevOps でアプリケーションコードをデプロイ"
    echo "2. Azure Blob Storage にモデルファイル (fixed_rf_model.joblib) をアップロード"
    echo "3. Azure Blob Storage に CSV データ (ultimate_pickup_data.csv) をアップロード"
    echo ""

    # モデルアップロード用のコマンド例を表示
    print_status "モデルファイルアップロード用のコマンド例:"
    echo "az storage blob upload --account-name $STORAGE_NAME --container-name models --name fixed_rf_model.joblib --file ../fixed_rf_model.joblib"
    echo "az storage blob upload --account-name $STORAGE_NAME --container-name models --name ultimate_pickup_data.csv --file ../ultimate_pickup_data.csv"

else
    print_error "❌ デプロイに失敗しました"
    print_error "詳細なエラー情報は Azure ポータルで確認してください"
    exit 1
fi

print_status "デプロイスクリプトが完了しました 🎉"
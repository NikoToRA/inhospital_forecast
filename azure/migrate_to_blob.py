import os
import sys
import argparse
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
from azure.core.exceptions import ResourceExistsError

def migrate_to_blob(connection_string, container_name):
    """
    モデルとデータをAzure Blob Storageに移行する
    
    Args:
        connection_string (str): Azure Storageアカウントの接続文字列
        container_name (str): コンテナ名
    """
    try:
        # BlobServiceClientを作成
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        
        # コンテナが存在するか確認、なければ作成
        try:
            container_client = blob_service_client.create_container(container_name)
            print(f"コンテナ '{container_name}' を作成しました")
        except ResourceExistsError:
            container_client = blob_service_client.get_container_client(container_name)
            print(f"コンテナ '{container_name}' は既に存在します")
        
        # モデルファイルをアップロード
        model_path = "../backend/models/fixed_rf_model.joblib"
        model_blob_name = "models/fixed_rf_model.joblib"
        
        with open(model_path, "rb") as model_file:
            blob_client = container_client.upload_blob(
                name=model_blob_name,
                data=model_file,
                overwrite=True
            )
            print(f"モデルファイルを '{model_blob_name}' としてアップロードしました")
        
        # データファイルをアップロード
        data_path = "../data/ultimate_pickup_data.csv"
        data_blob_name = "data/ultimate_pickup_data.csv"
        
        with open(data_path, "rb") as data_file:
            blob_client = container_client.upload_blob(
                name=data_blob_name,
                data=data_file,
                overwrite=True
            )
            print(f"データファイルを '{data_blob_name}' としてアップロードしました")
        
        print("Blob Storageへの移行が完了しました")
        
        # Webアプリでの利用方法を表示
        print("\n==================================================")
        print("Web Appでの利用方法:")
        print("1. アプリケーション設定に以下の環境変数を追加してください:")
        print(f"   AZURE_STORAGE_CONNECTION_STRING={connection_string}")
        print(f"   AZURE_STORAGE_CONTAINER_NAME={container_name}")
        print("   MODEL_PATH=models/fixed_rf_model.joblib")
        print("2. app.pyを修正して、Blobからモデルを読み込むようにしてください")
        print("==================================================\n")
        
        return True
    
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="モデルとデータをAzure Blob Storageに移行するスクリプト")
    parser.add_argument("--connection-string", required=True, help="Azure Storageアカウントの接続文字列")
    parser.add_argument("--container", default="inhospital-forecast", help="コンテナ名")
    
    args = parser.parse_args()
    
    success = migrate_to_blob(args.connection_string, args.container)
    
    if success:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main() 